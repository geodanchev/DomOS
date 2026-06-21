"""Apartment schemas."""

from pydantic import BaseModel, Field
from datetime import datetime


class ApartmentBase(BaseModel):
    """Base apartment fields."""
    number: str = Field(..., min_length=1, max_length=20, description="Номер на апартамента")
    floor: int | None = Field(None, description="Етаж")
    owner_name: str = Field(..., min_length=1, max_length=200, description="Име на собственика")
    residents_count: int = Field(1, ge=0, description="Брой живущи")
    monthly_fee: float = Field(..., gt=0, description="Месечна такса в лева")
    notes: str | None = Field(None, description="Бележки")


class ApartmentCreate(ApartmentBase):
    """Schema for creating an apartment."""
    pass


class ApartmentUpdate(BaseModel):
    """Schema for updating an apartment."""
    number: str | None = Field(None, min_length=1, max_length=20)
    floor: int | None = None
    owner_name: str | None = Field(None, min_length=1, max_length=200)
    residents_count: int | None = Field(None, ge=0)
    monthly_fee: float | None = Field(None, gt=0)
    notes: str | None = None


class ApartmentResponse(ApartmentBase):
    """Schema for apartment response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ApartmentList(BaseModel):
    """Schema for list of apartments."""
    items: list[ApartmentResponse]
    total: int
