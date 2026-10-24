from mysite.database.models import CourierLocation, Courier
from mysite.database.schema import CourierLocationInputSchema, CourierLocationOutSchema
from mysite.database.db import SessionLocal
from mysite.dependencies import get_current_user
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends
from typing import List

courier_location_router = APIRouter(prefix='/courier_location', tags=['CourierLocation'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@courier_location_router.post('/', response_model=CourierLocationOutSchema)
async def create_courier_location(location: CourierLocationInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] not in ['manager', 'courier']:
        raise HTTPException(status_code=403, detail='Жайгашкан жерди кошууга уруксат жок')
    courier_db = db.query(Courier).filter(Courier.id == location.courier_id).first()
    if not courier_db:
        raise HTTPException(status_code=404, detail='Мындай курьер жок')
    if current_user['status'] == 'courier' and courier_db.user_id != current_user['id']:
        raise HTTPException(status_code=403, detail='Башка курьердин жайгашкан жерин кошууга уруксат жок')
    if courier_db.status_courier.value == 'suspended':
        raise HTTPException(status_code=400, detail='Блоктолгон курьердин жайгашкан жерин кошууга болбойт')
    location_db = CourierLocation(**location.model_dump())
    db.add(location_db)
    db.commit()
    db.refresh(location_db)
    return location_db

@courier_location_router.get('/', response_model=List[CourierLocationOutSchema])
async def list_courier_location(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] == 'manager':
        return db.query(CourierLocation).all()
    if current_user['status'] == 'courier':
        return db.query(CourierLocation).join(Courier).filter(Courier.user_id == current_user['id']).all()
    raise HTTPException(status_code=403, detail='Жайгашкан жерлерди көрүүгө уруксат жок')

@courier_location_router.get('/{location_id}/', response_model=CourierLocationOutSchema)
async def detail_courier_location(location_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] not in ['manager', 'courier']:
        raise HTTPException(status_code=403, detail='Жайгашкан жерди көрүүгө уруксат жок')
    location_db = db.query(CourierLocation).filter(CourierLocation.id == location_id).first()
    if not location_db:
        raise HTTPException(status_code=404, detail='Мындай жайгашкан жер жок')
    if current_user['status'] == 'courier' and location_db.location_courier.user_id != current_user['id']:
        raise HTTPException(status_code=403, detail='Башка курьердин жайгашкан жерин көрүүгө уруксат жок')
    return location_db

@courier_location_router.put('/{location_id}/', response_model=dict)
async def update_courier_location(location_id: int, location: CourierLocationInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Жайгашкан жерди өзгөртүүгө уруксат жок')
    location_db = db.query(CourierLocation).filter(CourierLocation.id == location_id).first()
    if not location_db:
        raise HTTPException(status_code=404, detail='Мындай жайгашкан жер жок')
    courier_db = db.query(Courier).filter(Courier.id == location.courier_id).first()
    if not courier_db:
        raise HTTPException(status_code=404, detail='Мындай курьер жок')
    if location.courier_id != location_db.courier_id:
        raise HTTPException(status_code=400, detail='Жайгашкан жердин курьерин өзгөртүүгө болбойт')
    if courier_db.status_courier.value == 'suspended':
        raise HTTPException(status_code=400, detail='Блоктолгон курьердин жайгашкан жерин өзгөртүүгө болбойт')
    for location_key, location_value in location.model_dump().items():
        setattr(location_db, location_key, location_value)
    db.commit()
    db.refresh(location_db)
    return {'message': 'Курьердин жайгашкан жери өзгөрүлдү'}

@courier_location_router.delete('/{location_id}/', response_model=dict)
async def delete_courier_location(location_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Жайгашкан жерди өчүрүүгө уруксат жок')
    location_db = db.query(CourierLocation).filter(CourierLocation.id == location_id).first()
    if not location_db:
        raise HTTPException(status_code=404, detail='Мындай жайгашкан жер жок')
    db.delete(location_db)
    db.commit()
    return {'message': 'Курьердин жайгашкан жери өчүрүлдү'}