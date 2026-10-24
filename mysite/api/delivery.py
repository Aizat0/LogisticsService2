from mysite.database.models import Delivery, Warehouse, Courier, DeliveryStatus, CourierStatus
from mysite.database.schema import DeliveryInputSchema, DeliveryOutSchema
from mysite.database.db import SessionLocal
from mysite.dependencies import get_current_user
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends
from typing import List

delivery_router = APIRouter(prefix='/delivery', tags=['Delivery'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@delivery_router.post('/', response_model=DeliveryOutSchema)
async def create_delivery(delivery: DeliveryInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Доставка кошууга уруксат жок')
    warehouse_db = db.query(Warehouse).filter(Warehouse.id == delivery.warehouse_id).first()
    if not warehouse_db:
        raise HTTPException(status_code=404, detail='Мындай склад жок')
    if warehouse_db.status.value != 'active':
        raise HTTPException(status_code=400, detail='Склад активдүү эмес')
    courier_db = db.query(Courier).filter(Courier.id == delivery.courier_id).first()
    if not courier_db:
        raise HTTPException(status_code=404, detail='Мындай курьер жок')
    if courier_db.warehouse_id != delivery.warehouse_id:
        raise HTTPException(status_code=400, detail='Курьер бул складга тиешелүү эмес')
    if courier_db.status_courier in [CourierStatus.offline, CourierStatus.suspended]:
        raise HTTPException(status_code=400, detail='Курьер жеткиликтүү эмес')
    tracking_db = db.query(Delivery).filter(Delivery.tracking_code == delivery.tracking_code).first()
    if tracking_db:
        raise HTTPException(status_code=400, detail='Мындай tracking code бар')
    order_db = db.query(Delivery).filter(Delivery.order_id == delivery.order_id, Delivery.delivery_status.notin_([DeliveryStatus.cancelled])).first()
    if order_db:
        raise HTTPException(status_code=400, detail='Бул заказ үчүн доставка мурунтан бар')
    active_orders = db.query(Delivery).filter(Delivery.courier_id == delivery.courier_id, Delivery.delivery_status.in_([DeliveryStatus.pending, DeliveryStatus.assigned])).count()
    if active_orders >= courier_db.max_active_orders:
        raise HTTPException(status_code=400, detail='Курьердин заказ лимити толду')
    if delivery.delivery_status not in [DeliveryStatus.pending, DeliveryStatus.assigned]:
        raise HTTPException(status_code=400, detail='Жаңы доставка pending же assigned болушу керек')
    delivery_db = Delivery(**delivery.model_dump())
    db.add(delivery_db)
    db.commit()
    db.refresh(delivery_db)
    return delivery_db

@delivery_router.get('/', response_model=List[DeliveryOutSchema])
async def list_delivery(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] == 'manager':
        return db.query(Delivery).all()
    if current_user['status'] == 'courier':
        return db.query(Delivery).join(Courier).filter(Courier.user_id == current_user['id']).all()
    raise HTTPException(status_code=403, detail='Доставкаларды көрүүгө уруксат жок')

@delivery_router.get('/{delivery_id}/', response_model=DeliveryOutSchema)
async def detail_delivery(delivery_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] not in ['manager', 'courier']:
        raise HTTPException(status_code=403, detail='Доставканы көрүүгө уруксат жок')
    delivery_db = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery_db:
        raise HTTPException(status_code=404, detail='Мындай доставка жок')
    if current_user['status'] == 'courier' and delivery_db.courier_delivery.user_id != current_user['id']:
        raise HTTPException(status_code=403, detail='Башка курьердин доставкаларын көрүүгө уруксат жок')
    return delivery_db

@delivery_router.put('/{delivery_id}/', response_model=dict)
async def update_delivery(delivery_id: int, delivery: DeliveryInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] not in ['manager', 'courier']:
        raise HTTPException(status_code=403, detail='Доставка өзгөртүүгө уруксат жок')
    delivery_db = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery_db:
        raise HTTPException(status_code=404, detail='Мындай доставка жок')
    if current_user['status'] == 'courier':
        if delivery_db.courier_delivery.user_id != current_user['id']:
            raise HTTPException(status_code=403, detail='Башка курьердин доставкаларын өзгөртүүгө уруксат жок')
        if delivery.order_id != delivery_db.order_id or delivery.tracking_code != delivery_db.tracking_code or delivery.warehouse_id != delivery_db.warehouse_id or delivery.courier_id != delivery_db.courier_id or delivery.destination_address != delivery_db.destination_address or delivery.destination_latitude != delivery_db.destination_latitude or delivery.destination_longitude != delivery_db.destination_longitude or delivery.estimated_delivery_at != delivery_db.estimated_delivery_at:
            raise HTTPException(status_code=403, detail='Доставканын бул маалыматтарын өзгөртүүгө уруксат жок')
    warehouse_db = db.query(Warehouse).filter(Warehouse.id == delivery.warehouse_id).first()
    if not warehouse_db:
        raise HTTPException(status_code=404, detail='Мындай склад жок')
    courier_db = db.query(Courier).filter(Courier.id == delivery.courier_id).first()
    if not courier_db:
        raise HTTPException(status_code=404, detail='Мындай курьер жок')
    if delivery.order_id != delivery_db.order_id:
        raise HTTPException(status_code=400, detail='Доставканын заказын өзгөртүүгө болбойт')
    if delivery.tracking_code != delivery_db.tracking_code:
        raise HTTPException(status_code=400, detail='Tracking code өзгөртүүгө болбойт')
    if delivery_db.delivery_status in [DeliveryStatus.delivered, DeliveryStatus.cancelled]:
        raise HTTPException(status_code=400, detail='Аяктаган доставканы өзгөртүүгө болбойт')
    if delivery.delivery_status == DeliveryStatus.pending and delivery_db.delivery_status == DeliveryStatus.assigned:
        raise HTTPException(status_code=400, detail='Статусту артка өзгөртүүгө болбойт')
    if courier_db.warehouse_id != delivery.warehouse_id:
        raise HTTPException(status_code=400, detail='Курьер бул складга тиешелүү эмес')
    if courier_db.status_courier in [CourierStatus.offline, CourierStatus.suspended] and delivery.delivery_status == DeliveryStatus.assigned:
        raise HTTPException(status_code=400, detail='Курьер жеткиликтүү эмес')
    if current_user['status'] == 'courier' and delivery.delivery_status not in [delivery_db.delivery_status, DeliveryStatus.delivered]:
        raise HTTPException(status_code=403, detail='Бул статуска өзгөртүүгө уруксат жок')
    if delivery.courier_id != delivery_db.courier_id and delivery.delivery_status in [DeliveryStatus.pending, DeliveryStatus.assigned]:
        active_orders = db.query(Delivery).filter(Delivery.courier_id == delivery.courier_id, Delivery.delivery_status.in_([DeliveryStatus.pending, DeliveryStatus.assigned])).count()
        if active_orders >= courier_db.max_active_orders:
            raise HTTPException(status_code=400, detail='Курьердин заказ лимити толду')
    for delivery_key, delivery_value in delivery.model_dump().items():
        setattr(delivery_db, delivery_key, delivery_value)
    db.commit()
    db.refresh(delivery_db)
    return {'message': 'Доставка өзгөрүлдү'}

@delivery_router.delete('/{delivery_id}/', response_model=dict)
async def delete_delivery(delivery_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Доставка өчүрүүгө уруксат жок')
    delivery_db = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery_db:
        raise HTTPException(status_code=404, detail='Мындай доставка жок')
    if delivery_db.delivery_status == DeliveryStatus.delivered:
        raise HTTPException(status_code=400, detail='Жеткирилген доставканы өчүрүүгө болбойт')
    if delivery_db.route_stops or delivery_db.tracking_events:
        raise HTTPException(status_code=400, detail='Доставка маршрутка же тарыхка байланышкан')
    db.delete(delivery_db)
    db.commit()
    return {'message': 'Доставка өчүрүлдү'}