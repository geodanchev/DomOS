"""Apartments API endpoints - домова книга."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.models.apartment import Apartment
from app.models.user import User
from app.schemas.apartment import ApartmentCreate, ApartmentUpdate, ApartmentResponse, ApartmentList
from app.api.auth import get_current_user

router = APIRouter()


@router.get("", response_model=ApartmentList)
async def list_apartments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all apartments."""
    query = db.query(Apartment).order_by(Apartment.number)
    total = query.count()
    apartments = query.offset(skip).limit(limit).all()
    
    return ApartmentList(
        items=[ApartmentResponse.model_validate(a) for a in apartments],
        total=total,
    )


@router.get("/{apartment_id}", response_model=ApartmentResponse)
async def get_apartment(
    apartment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get apartment by ID."""
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Апартаментът не е намерен",
        )
    return ApartmentResponse.model_validate(apartment)


@router.post("", response_model=ApartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_apartment(
    data: ApartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new apartment."""
    # Check if apartment number exists
    existing = db.query(Apartment).filter(Apartment.number == data.number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Апартамент с номер '{data.number}' вече съществува",
        )
    
    apartment = Apartment(**data.model_dump())
    db.add(apartment)
    db.commit()
    db.refresh(apartment)
    
    return ApartmentResponse.model_validate(apartment)


@router.put("/{apartment_id}", response_model=ApartmentResponse)
async def update_apartment(
    apartment_id: int,
    data: ApartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an apartment."""
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Апартаментът не е намерен",
        )
    
    # Check if new number conflicts
    if data.number and data.number != apartment.number:
        existing = db.query(Apartment).filter(Apartment.number == data.number).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Апартамент с номер '{data.number}' вече съществува",
            )
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(apartment, field, value)
    
    db.commit()
    db.refresh(apartment)
    
    return ApartmentResponse.model_validate(apartment)


@router.delete("/{apartment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_apartment(
    apartment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an apartment."""
    apartment = db.query(Apartment).filter(Apartment.id == apartment_id).first()
    if not apartment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Апартаментът не е намерен",
        )
    
    db.delete(apartment)
    db.commit()
