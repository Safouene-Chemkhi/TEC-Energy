import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.db_models.fuel_mixture_db import Base

DATABASE_URL = os.getenv(
	"DATABASE_URL",
	# Use psycopg (psycopg3) driver for SQLAlchemy: postgresql+psycopg://
	"postgresql+psycopg://postgres:admin@localhost:5432/mydb",
)

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def init_db():
	Base.metadata.create_all(bind=engine)


__all__ = ["engine", "SessionLocal", "init_db"]
