from fastapi import FastAPI
import asyncio
import aiohttp
import os
import logging
from dotenv import load_dotenv

from dependencies import init_db, SessionLocal
from services.fuel_mixture_service import ingest_payload

load_dotenv()  # Loads variables from .env file into environment
logging.basicConfig(level=logging.INFO)


app = FastAPI()

MISO_API_URL = os.getenv("MISO_API_URL", "https://public-api.misoenergy.org/api/FuelMixxxx")


@app.on_event("startup")
def on_startup():
    init_db()


def _ingest_sync(data):
    with SessionLocal() as session:
        try:
            if isinstance(data, list):
                for item in data:
                    ingest_payload(item, session)
            else:
                ingest_payload(data, session)
            session.commit()
        except Exception:
            logging.exception("_ingest_sync failed, rolling back")
            session.rollback()
            raise


async def fetch_and_ingest_async(raise_on_error: bool = False):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(MISO_API_URL, timeout=20) as resp:
                resp.raise_for_status()
                data = await resp.json()

        logging.info("fetched ingest data, scheduling DB work")
        # Run synchronous DB work in a thread to avoid blocking the event loop
        await asyncio.to_thread(_ingest_sync, data)
        logging.info("ingest completed successfully")
    except Exception as e:
        logging.exception("ingest failed")
        if raise_on_error:
            raise


@app.post("/ingest")
async def trigger_ingest():
    asyncio.create_task(fetch_and_ingest_async())
    return {"status": "ingestion_scheduled"}


@app.post("/ingest_now")
async def ingest_now():
    """Debug endpoint: fetch and ingest synchronously and return result or error."""
    try:
        await fetch_and_ingest_async(raise_on_error=True)
        return {"status": "ingested"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


@app.get("/")
async def read_root():
    return {"status": "ok"}

