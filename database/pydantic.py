from pydantic import BaseModel, Field
from typing import Literal, Optional


class LeadRequest(BaseModel):
    name: str = Field(..., example="Иван")
    phone: str = Field(..., example="+77001234567")
    message: Optional[str] = Field(None, example="Хочу заказать консультацию")
    city: Optional[str] = Field(None, example="Алматы")
    source: str = Field(..., example="website")


from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LeadSchema(BaseModel):
    id: int
    message: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    operator: Optional[str] = None
    created_at: Optional[datetime] = None
    office: Optional[str] = None
    city: Optional[str] = None