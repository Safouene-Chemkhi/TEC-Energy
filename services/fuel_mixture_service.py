from typing import Any, Dict, List
from datetime import datetime
import logging
from models.schemas.fuel_mixture import FuelPayload, FuelItem
from repositories.fuel_mixture_repository import FuelMixtureRepository

logger = logging.getLogger(__name__)


def _parse_datetime(value) -> datetime:
	if value is None:
		return None
	if isinstance(value, datetime):
		return value
	try:
		# try ISO formats
		return datetime.fromisoformat(value)
	except Exception:
		try:
			# fallback: many APIs use space separated timezone
			return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
		except Exception:
			return None


def _process_fuel_record(item: Dict[str, Any], ref_id: str, interval_ts: datetime, repo: FuelMixtureRepository, idx: int) -> None:
	"""Process a single fuel record and write to DB."""
	if not isinstance(item, dict):
		logger.warning(f"Fuel record {idx} is not a dict: {type(item)}")
		return

	category = item.get("CATEGORY") or item.get("FUEL_CATEGORY") or item.get("category")
	mw_raw = item.get("ACT") or item.get("MW") or item.get("actual_mw")
	try:
		mw = float(mw_raw) if mw_raw is not None else 0.0
	except Exception:
		mw = 0.0

	interval = _parse_datetime(item.get("INTERVALEST") or item.get("interval_est")) or interval_ts

	logger.debug(f"Fuel record {idx}: category={category}, mw={mw}")
	fuel_obj = repo.get_or_create_fuel(category)
	repo.upsert_fuel_generation(ref_id or "unknown", interval, fuel_obj.id, mw, fuel_label=category)


def ingest_payload(payload: Dict[str, Any], session) -> None:
	"""Process one payload item and write idempotently to the DB.

	Caller should manage transactions; this function assumes an active SQLAlchemy session.
	"""
	repo = FuelMixtureRepository(session)

	# Allow payload to be a parsed Pydantic model or a raw dict
	if not isinstance(payload, dict):
		# try to coerce
		payload = payload.dict()

	logger.debug(f"Ingest payload keys: {payload.keys()}")

	ref_id = payload.get("RefId") or payload.get("RefID") or payload.get("refId")
	total_mw = payload.get("TotalMW")
	try:
		total_mw = float(total_mw) if total_mw is not None else None
	except Exception:
		total_mw = None

	fuels = payload.get("Fuel") or []

	# If top-level fuel list is provided as dict, try to convert to list
	if isinstance(fuels, dict):
		fuels = list(fuels.values())

	logger.info(f"Extracted ref_id={ref_id}, total_mw={total_mw}, fuel_count={len(fuels)}")

	# Insert or update grid generation fact (interval timestamp will be taken from fuel items if present)
	interval_ts = None
	if fuels:
		first = fuels[0]
		if isinstance(first, dict):
			interval_ts = _parse_datetime(first.get("INTERVALEST") or first.get("interval_est"))
		elif isinstance(first, FuelItem):
			interval_ts = first.interval_est

	# fallback to now if no timestamp
	if interval_ts is None:
		interval_ts = datetime.utcnow()

	repo.upsert_grid_generation(ref_id or "unknown", interval_ts, total_mw or 0.0)

	# Process each fuel row
	for idx, item in enumerate(fuels):
		logger.debug(f"Fuel item {idx} type: {type(item)}")
		if isinstance(item, list):
			logger.info(f"Fuel item {idx} is a list with {len(item)} elements, content: {item[:2] if len(item) > 0 else 'empty'}")
			# If it's a list of fuel records, process each record
			for sub_idx, sub_item in enumerate(item):
				_process_fuel_record(sub_item, ref_id, interval_ts, repo, sub_idx)
		elif not isinstance(item, dict):
			# pydantic model or similar
			try:
				item = item.dict(by_alias=True)
				_process_fuel_record(item, ref_id, interval_ts, repo, idx)
			except Exception as e:
				logger.warning(f"Fuel item {idx} failed to coerce to dict: {e}, type={type(item)}")
				continue
		else:
			_process_fuel_record(item, ref_id, interval_ts, repo, idx)

	logger.info(f"Ingest complete: {len(fuels)} fuel items processed")


__all__ = ["ingest_payload"]
