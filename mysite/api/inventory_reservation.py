from mysite.database.models import InventoryReservation, Inventory, InventoryReservationStatus
from mysite.database.schema import InventoryReservationInputSchema, InventoryReservationOutSchema
from mysite.database.db import SessionLocal
from mysite.dependencies import get_current_user
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime

inventory_reservation_router = APIRouter(prefix='/inventory_reservation', tags=['InventoryReservation'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@inventory_reservation_router.post('/', response_model=InventoryReservationOutSchema)
async def create_inventory_reservation(reservation: InventoryReservationInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Резерв кошууга уруксат жок')
    inventory_db = db.query(Inventory).filter(Inventory.id == reservation.inventory_id).first()
    if not inventory_db:
        raise HTTPException(status_code=404, detail='Мындай товар калдыгы жок')
    if reservation.status_inventory != InventoryReservationStatus.active:
        raise HTTPException(status_code=400, detail='Жаңы резерв active статусунда болушу керек')
    if reservation.expires_at <= datetime.utcnow():
        raise HTTPException(status_code=400, detail='Резервдин мөөнөтү келечекте болушу керек')
    available_quantity = inventory_db.quantity - inventory_db.reserved_quantity
    if reservation.quantity > available_quantity:
        raise HTTPException(status_code=400, detail='Складда жетиштүү товар жок')
    reservation_db = InventoryReservation(**reservation.model_dump())
    inventory_db.reserved_quantity += reservation.quantity
    db.add(reservation_db)
    db.commit()
    db.refresh(reservation_db)
    return reservation_db

@inventory_reservation_router.get('/', response_model=List[InventoryReservationOutSchema])
async def list_inventory_reservation(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Резервдерди көрүүгө уруксат жок')
    return db.query(InventoryReservation).all()

@inventory_reservation_router.get('/{reservation_id}/', response_model=InventoryReservationOutSchema)
async def detail_inventory_reservation(reservation_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Резервди көрүүгө уруксат жок')
    reservation_db = db.query(InventoryReservation).filter(InventoryReservation.id == reservation_id).first()
    if not reservation_db:
        raise HTTPException(status_code=404, detail='Мындай резерв жок')
    return reservation_db

@inventory_reservation_router.put('/{reservation_id}/', response_model=dict)
async def update_inventory_reservation(reservation_id: int, reservation: InventoryReservationInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Резерв өзгөртүүгө уруксат жок')
    reservation_db = db.query(InventoryReservation).filter(InventoryReservation.id == reservation_id).first()
    if not reservation_db:
        raise HTTPException(status_code=404, detail='Мындай резерв жок')
    inventory_db = db.query(Inventory).filter(Inventory.id == reservation.inventory_id).first()
    if not inventory_db:
        raise HTTPException(status_code=404, detail='Мындай товар калдыгы жок')
    if reservation_db.status_inventory != InventoryReservationStatus.active:
        raise HTTPException(status_code=400, detail='Бул резервди өзгөртүүгө болбойт')
    if reservation.inventory_id != reservation_db.inventory_id or reservation.order_id != reservation_db.order_id:
        raise HTTPException(status_code=400, detail='Резервдин товарын же заказын өзгөртүүгө болбойт')
    if reservation.status_inventory == InventoryReservationStatus.active:
        if reservation.expires_at <= datetime.utcnow():
            raise HTTPException(status_code=400, detail='Резервдин мөөнөтү келечекте болушу керек')
        available_quantity = inventory_db.quantity - inventory_db.reserved_quantity + reservation_db.quantity
        if reservation.quantity > available_quantity:
            raise HTTPException(status_code=400, detail='Складда жетиштүү товар жок')
        inventory_db.reserved_quantity += reservation.quantity - reservation_db.quantity
    elif reservation.status_inventory == InventoryReservationStatus.committed:
        if inventory_db.quantity < reservation_db.quantity or inventory_db.reserved_quantity < reservation_db.quantity:
            raise HTTPException(status_code=400, detail='Товардын калдыгы жетишсиз')
        if reservation.quantity != reservation_db.quantity:
            raise HTTPException(status_code=400, detail='Резервдин санын өзгөртүүгө болбойт')
        inventory_db.quantity -= reservation_db.quantity
        inventory_db.reserved_quantity -= reservation_db.quantity
    else:
        if reservation.quantity != reservation_db.quantity:
            raise HTTPException(status_code=400, detail='Резервдин санын өзгөртүүгө болбойт')
        inventory_db.reserved_quantity -= reservation_db.quantity
    for reservation_key, reservation_value in reservation.model_dump().items():
        setattr(reservation_db, reservation_key, reservation_value)
    db.commit()
    db.refresh(reservation_db)
    return {'message': 'Резерв өзгөрүлдү'}

@inventory_reservation_router.delete('/{reservation_id}/', response_model=dict)
async def delete_inventory_reservation(reservation_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Резерв өчүрүүгө уруксат жок')
    reservation_db = db.query(InventoryReservation).filter(InventoryReservation.id == reservation_id).first()
    if not reservation_db:
        raise HTTPException(status_code=404, detail='Мындай резерв жок')
    if reservation_db.status_inventory == InventoryReservationStatus.active:
        raise HTTPException(status_code=400, detail='Алгач активдүү резервди бошотуңуз')
    db.delete(reservation_db)
    db.commit()
    return {'message': 'Резерв өчүрүлдү'}