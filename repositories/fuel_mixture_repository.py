from typing import Optional
from sqlalchemy.orm import Session
from models.db_models.fuel_mixture_db import (
	GridGenerationDB,
	FuelDB,
	FuelGenerationDB,
)


class FuelMixtureRepository:
	"""Repository for idempotent access to the star-schema tables.

	Usage: create with a SQLAlchemy `Session` and call methods inside a transaction.
	Commits/rollbacks are the caller's responsibility.
	"""

	def __init__(self, session: Session):
		self.session = session

	def get_or_create_fuel(self, category: str) -> FuelDB:
		if category is None:
			category = "UNKNOWN"
		obj = self.session.query(FuelDB).filter(FuelDB.category == category).first()
		if obj:
			return obj
		obj = FuelDB(category=category)
		self.session.add(obj)
		self.session.flush()
		return obj

	def upsert_grid_generation(self, ref_id: str, interval_ts, total_mw: float) -> GridGenerationDB:
		obj = (
			self.session.query(GridGenerationDB)
			.filter(GridGenerationDB.ref_id == ref_id, GridGenerationDB.interval_ts == interval_ts)
			.first()
		)
		if obj:
			obj.total_mw = total_mw
			return obj
		obj = GridGenerationDB(ref_id=ref_id, interval_ts=interval_ts, total_mw=total_mw)
		self.session.add(obj)
		self.session.flush()
		return obj

	def upsert_fuel_generation(
		self, ref_id: str, interval_ts, fuel_id: int, mw: float, fuel_label: Optional[str] = None
	) -> FuelGenerationDB:
		obj = (
			self.session.query(FuelGenerationDB)
			.filter(
				FuelGenerationDB.ref_id == ref_id,
				FuelGenerationDB.interval_ts == interval_ts,
				FuelGenerationDB.fuel_id == fuel_id,
			)
			.first()
		)
		if obj:
			obj.mw = mw
			obj.fuel_label = fuel_label
			return obj
		obj = FuelGenerationDB(
			ref_id=ref_id, interval_ts=interval_ts, fuel_id=fuel_id, mw=mw, fuel_label=fuel_label
		)
		self.session.add(obj)
		self.session.flush()
		return obj


__all__ = ["FuelMixtureRepository"]
