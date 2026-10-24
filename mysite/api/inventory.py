from mysite.database.models import Inventory, Warehouse
from mysite.database.schema import InventoryInputSchema, InventoryOutSchema
from mysite.database.db import SessionLocal
from mysite.dependencies import get_current_user
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends
from typing import List

inventory_router = APIRouter(prefix='/inventory', tags=['Inventory'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@inventory_router.post('/', response_model=InventoryOutSchema)
async def create_inventory(inventory: InventoryInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Товар калдыгын кошууга уруксат жок')
    warehouse_db = db.query(Warehouse).filter(Warehouse.id == inventory.warehouse_id).first()
    if not warehouse_db:
        raise HTTPException(status_code=404, detail='Мындай склад жок')
    inventory_db = db.query(Inventory).filter(Inventory.warehouse_id == inventory.warehouse_id, Inventory.product_id == inventory.product_id).first()
    if inventory_db:
        raise HTTPException(status_code=400, detail='Бул товар складда мурунтан бар')
    if inventory.reserved_quantity > inventory.quantity:
        raise HTTPException(status_code=400, detail='Резервдеги товар жалпы сандан көп болбошу керек')
    inventory_db = Inventory(**inventory.model_dump())
    db.add(inventory_db)
    db.commit()
    db.refresh(inventory_db)
    return inventory_db

@inventory_router.get('/', response_model=List[InventoryOutSchema])
async def list_inventory(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return db.query(Inventory).all()

@inventory_router.get('/{inventory_id}/', response_model=InventoryOutSchema)
async def detail_inventory(inventory_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    inventory_db = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory_db:
        raise HTTPException(status_code=404, detail='Мындай товар калдыгы жок')
    return inventory_db

@inventory_router.put('/{inventory_id}/', response_model=dict)
async def update_inventory(inventory_id: int, inventory: InventoryInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Товар калдыгын өзгөртүүгө уруксат жок')
    inventory_db = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory_db:
        raise HTTPException(status_code=404, detail='Мындай товар калдыгы жок')
    warehouse_db = db.query(Warehouse).filter(Warehouse.id == inventory.warehouse_id).first()
    if not warehouse_db:
        raise HTTPException(status_code=404, detail='Мындай склад жок')
    existing_db = db.query(Inventory).filter(Inventory.warehouse_id == inventory.warehouse_id, Inventory.product_id == inventory.product_id, Inventory.id != inventory_id).first()
    if existing_db:
        raise HTTPException(status_code=400, detail='Бул товар складда мурунтан бар')
    if inventory.reserved_quantity > inventory.quantity:
        raise HTTPException(status_code=400, detail='Резервдеги товар жалпы сандан көп болбошу керек')
    active_reserved = sum(reservation.quantity for reservation in inventory_db.inventory_reservation if reservation.status_inventory.value == 'active')
    if inventory.reserved_quantity < active_reserved:
        raise HTTPException(status_code=400, detail='Активдүү резервдердин санынан аз болбошу керек')
    for inventory_key, inventory_value in inventory.model_dump().items():
        setattr(inventory_db, inventory_key, inventory_value)
    db.commit()
    db.refresh(inventory_db)
    return {'message': 'Товар калдыгы өзгөрүлдү'}

@inventory_router.delete('/{inventory_id}/', response_model=dict)
async def delete_inventory(inventory_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Товар калдыгын өчүрүүгө уруксат жок')
    inventory_db = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory_db:
        raise HTTPException(status_code=404, detail='Мындай товар калдыгы жок')
    if inventory_db.inventory_reservation:
        raise HTTPException(status_code=400, detail='Бул товарга байланышкан резервдер бар')
    db.delete(inventory_db)
    db.commit()
    return {'message': 'Товар калдыгы өчүрүлдү'}