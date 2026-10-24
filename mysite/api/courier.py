from mysite.database.models import Courier, Warehouse
from mysite.database.schema import CourierInputSchema, CourierOutSchema
from mysite.database.db import SessionLocal
from mysite.dependencies import get_current_user
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends
from typing import List

courier_router = APIRouter(prefix='/courier', tags=['Courier'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@courier_router.post('/', response_model=CourierOutSchema)
async def create_courier(courier: CourierInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Курьер кошууга уруксат жок')
    warehouse_db = db.query(Warehouse).filter(Warehouse.id == courier.warehouse_id).first()
    if not warehouse_db:
        raise HTTPException(status_code=404, detail='Мындай склад жок')
    user_db = db.query(Courier).filter(Courier.user_id == courier.user_id).first()
    if user_db:
        raise HTTPException(status_code=400, detail='Бул колдонуучу курьер катары катталган')
    courier_db = Courier(**courier.model_dump())
    db.add(courier_db)
    db.commit()
    db.refresh(courier_db)
    return courier_db

@courier_router.get('/', response_model=List[CourierOutSchema])
async def list_courier(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] == 'manager':
        return db.query(Courier).all()
    if current_user['status'] == 'courier':
        return db.query(Courier).filter(Courier.user_id == current_user['id']).all()
    raise HTTPException(status_code=403, detail='Курьерлерди көрүүгө уруксат жок')

@courier_router.get('/{courier_id}/', response_model=CourierOutSchema)
async def detail_courier(courier_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] not in ['manager', 'courier']:
        raise HTTPException(status_code=403, detail='Курьерди көрүүгө уруксат жок')
    courier_db = db.query(Courier).filter(Courier.id == courier_id).first()
    if not courier_db:
        raise HTTPException(status_code=404, detail='Мындай курьер жок')
    if current_user['status'] == 'courier' and courier_db.user_id != current_user['id']:
        raise HTTPException(status_code=403, detail='Башка курьердин маалыматын көрүүгө уруксат жок')
    return courier_db

@courier_router.put('/{courier_id}/', response_model=dict)
async def update_courier(courier_id: int, courier: CourierInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] not in ['manager', 'courier']:
        raise HTTPException(status_code=403, detail='Курьер өзгөртүүгө уруксат жок')
    courier_db = db.query(Courier).filter(Courier.id == courier_id).first()
    if not courier_db:
        raise HTTPException(status_code=404, detail='Мындай курьер жок')
    if current_user['status'] == 'courier':
        if courier_db.user_id != current_user['id']:
            raise HTTPException(status_code=403, detail='Башка курьерди өзгөртүүгө уруксат жок')
        if courier.user_id != courier_db.user_id or courier.warehouse_id != courier_db.warehouse_id or courier.max_active_orders != courier_db.max_active_orders:
            raise HTTPException(status_code=403, detail='Бул маалыматтарды өзгөртүүгө уруксат жок')
    warehouse_db = db.query(Warehouse).filter(Warehouse.id == courier.warehouse_id).first()
    if not warehouse_db:
        raise HTTPException(status_code=404, detail='Мындай склад жок')
    user_db = db.query(Courier).filter(Courier.user_id == courier.user_id, Courier.id != courier_id).first()
    if user_db:
        raise HTTPException(status_code=400, detail='Бул колдонуучу курьер катары катталган')
    if any(route.status.value == 'active' for route in courier_db.routes):
        if courier.warehouse_id != courier_db.warehouse_id:
            raise HTTPException(status_code=400, detail='Активдүү маршруту бар курьердин складын өзгөртүүгө болбойт')
    for courier_key, courier_value in courier.model_dump().items():
        setattr(courier_db, courier_key, courier_value)
    db.commit()
    db.refresh(courier_db)
    return {'message': 'Курьер өзгөрүлдү'}