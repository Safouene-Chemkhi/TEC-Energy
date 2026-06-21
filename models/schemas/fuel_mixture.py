from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class FuelItem(BaseModel):
    interval_est: Optional[datetime] = Field(None, alias='INTERVALEST')
    category: Optional[str] = Field(None, alias='CATEGORY')
    actual_mw: Optional[float] = Field(None, alias='ACT')
    fuel_category: Optional[str] = Field(None, alias='FUEL_CATEGORY')


class FuelPayload(BaseModel):
    RefId: Optional[str]
    TotalMW: Optional[float]
    Fuel: Optional[List[FuelItem]]

    class Config:
        allow_population_by_field_name = True