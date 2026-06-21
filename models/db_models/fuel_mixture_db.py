from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class GridGenerationDB(Base):
    __tablename__ = "fact_grid_generation"

    id = Column(Integer, primary_key=True, index=True)

    ref_id = Column(String, index=True, nullable=False)
    interval_ts = Column(DateTime, nullable=False)

    total_mw = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("ref_id", "interval_ts", name="uq_grid_snapshot"),
    )

class FuelDB(Base):
    __tablename__ = "dim_fuel"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), unique=True, nullable=False)

class FuelGenerationDB(Base):
    __tablename__ = "fact_fuel_generation"

    id = Column(Integer, primary_key=True, index=True)

    ref_id = Column(String, index=True, nullable=False)
    interval_ts = Column(DateTime, nullable=False)

    fuel_id = Column(Integer, ForeignKey("dim_fuel.id"))

    mw = Column(Integer, nullable=False)

    fuel_label = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)

    fuel = relationship("FuelDB")

    __table_args__ = (
        UniqueConstraint(
            "ref_id", "interval_ts", "fuel_id",
            name="uq_fuel_snapshot"
        ),
    )