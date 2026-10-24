from mysite.database.models import Warehouse
from mysite.database.schema import WarehouseInputSchema, WarehouseOutSchema
from mysite.database.db import SessionLocal
from mysite.dependencies import get_current_user
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends
from typing import List

warehouse_router = APIRouter(prefix='/warehouse', tags=['Warehouse'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@warehouse_router.post('/', response_model=WarehouseOutSchema)
async def create_warehouse(warehouse: WarehouseInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Склад кошууга уруксат жок')
    code_db = db.query(Warehouse).filter(Warehouse.code == warehouse.code).first()
    if code_db:
        raise HTTPException(status_code=400, detail='Мындай склад коду бар')
    street_db = db.query(Warehouse).filter(Warehouse.street == warehouse.street).first()
    if street_db:
        raise HTTPException(status_code=400, detail='Мындай склад дареги бар')
    warehouse_db = Warehouse(**warehouse.model_dump())
    db.add(warehouse_db)
    db.commit()
    db.refresh(warehouse_db)
    return warehouse_db

@warehouse_router.get('/', response_model=List[WarehouseOutSchema])
async def list_warehouse(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return db.query(Warehouse).all()

@warehouse_router.get('/{warehouse_id}/', response_model=WarehouseOutSchema)
async def detail_warehouse(warehouse_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    warehouse_db = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse_db:
        raise HTTPException(status_code=404, detail='Мындай склад жок')
    return warehouse_db

@warehouse_router.put('/{warehouse_id}/', response_model=dict)
async def update_warehouse(warehouse_id: int, warehouse: WarehouseInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Склад өзгөртүүгө уруксат жок')
    warehouse_db = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse_db:
        raise HTTPException(status_code=404, detail='Мындай склад жок')
    code_db = db.query(Warehouse).filter(Warehouse.code == warehouse.code, Warehouse.id != warehouse_id).first()
    if code_db:
        raise HTTPException(status_code=400, detail='Мындай склад коду бар')
    street_db = db.query(Warehouse).filter(Warehouse.street == warehouse.street, Warehouse.id != warehouse_id).first()
    if street_db:
        raise HTTPException(status_code=400, detail='Мындай склад дареги бар')
    for warehouse_key, warehouse_value in warehouse.model_dump().items():
        setattr(warehouse_db, warehouse_key, warehouse_value)
    db.commit()
    db.refresh(warehouse_db)
    return {'message': 'Склад өзгөрүлдү'}

@warehouse_router.delete('/{warehouse_id}/', response_model=dict)
async def delete_warehouse(warehouse_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Склад өчүрүүгө уруксат жок')
    warehouse_db = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse_db:
        raise HTTPException(status_code=404, detail='Мындай склад жок')
    if warehouse_db.ware_inventory or warehouse_db.courier_warehouse or warehouse_db.warehouse_delivery:
        raise HTTPException(status_code=400, detail='Складга товар, курьер же доставка байланышкан')
    db.delete(warehouse_db)
    db.commit()
    return {'message': 'Склад өчүрүлдү'}