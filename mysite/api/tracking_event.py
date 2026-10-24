from mysite.database.models import TrackingEvent, Delivery, Courier, DeliveryStatus
from mysite.database.schema import TrackingEventInputSchema, TrackingEventOutSchema
from mysite.database.db import SessionLocal
from mysite.dependencies import get_current_user
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends
from typing import List

tracking_event_router = APIRouter(prefix='/tracking_event', tags=['TrackingEvent'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@tracking_event_router.post('/', response_model=TrackingEventOutSchema)
async def create_tracking_event(event: TrackingEventInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] not in ['manager', 'courier']:
        raise HTTPException(status_code=403, detail='Окуя кошууга уруксат жок')
    delivery_db = db.query(Delivery).filter(Delivery.id == event.delivery_id).first()
    if not delivery_db:
        raise HTTPException(status_code=404, detail='Мындай доставка жок')
    if current_user['status'] == 'courier' and delivery_db.courier_delivery.user_id != current_user['id']:
        raise HTTPException(status_code=403, detail='Башка курьердин доставкасына окуя кошууга уруксат жок')
    if delivery_db.delivery_status in [DeliveryStatus.delivered, DeliveryStatus.cancelled]:
        raise HTTPException(status_code=400, detail='Аяктаган доставкага окуя кошууга болбойт')
    if event.status not in [status.value for status in DeliveryStatus]:
        raise HTTPException(status_code=400, detail='Мындай статус жок')
    event_db = TrackingEvent(**event.model_dump())
    db.add(event_db)
    db.commit()
    db.refresh(event_db)
    return event_db

@tracking_event_router.get('/', response_model=List[TrackingEventOutSchema])
async def list_tracking_event(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] == 'manager':
        return db.query(TrackingEvent).order_by(TrackingEvent.created_at.desc()).all()
    if current_user['status'] == 'courier':
        return db.query(TrackingEvent).join(Delivery).join(Courier).filter(Courier.user_id == current_user['id']).order_by(TrackingEvent.created_at.desc()).all()
    raise HTTPException(status_code=403, detail='Окуяларды көрүүгө уруксат жок')

@tracking_event_router.get('/{event_id}/', response_model=TrackingEventOutSchema)
async def detail_tracking_event(event_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] not in ['manager', 'courier']:
        raise HTTPException(status_code=403, detail='Окуяны көрүүгө уруксат жок')
    event_db = db.query(TrackingEvent).filter(TrackingEvent.id == event_id).first()
    if not event_db:
        raise HTTPException(status_code=404, detail='Мындай окуя жок')
    if current_user['status'] == 'courier' and event_db.delivery.courier_delivery.user_id != current_user['id']:
        raise HTTPException(status_code=403, detail='Башка курьердин окуясын көрүүгө уруксат жок')
    return event_db

@tracking_event_router.put('/{event_id}/', response_model=dict)
async def update_tracking_event(event_id: int, event: TrackingEventInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Окуя өзгөртүүгө уруксат жок')
    event_db = db.query(TrackingEvent).filter(TrackingEvent.id == event_id).first()
    if not event_db:
        raise HTTPException(status_code=404, detail='Мындай окуя жок')
    delivery_db = db.query(Delivery).filter(Delivery.id == event.delivery_id).first()
    if not delivery_db:
        raise HTTPException(status_code=404, detail='Мындай доставка жок')
    if event.delivery_id != event_db.delivery_id:
        raise HTTPException(status_code=400, detail='Окуянын доставкасын өзгөртүүгө болбойт')
    if delivery_db.delivery_status in [DeliveryStatus.delivered, DeliveryStatus.cancelled]:
        raise HTTPException(status_code=400, detail='Аяктаган доставканын окуясын өзгөртүүгө болбойт')
    if event.status not in [status.value for status in DeliveryStatus]:
        raise HTTPException(status_code=400, detail='Мындай статус жок')
    for event_key, event_value in event.model_dump().items():
        setattr(event_db, event_key, event_value)
    db.commit()
    db.refresh(event_db)
    return {'message': 'Окуя өзгөрүлдү'}

@tracking_event_router.delete('/{event_id}/', response_model=dict)
async def delete_tracking_event(event_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Окуя өчүрүүгө уруксат жок')
    event_db = db.query(TrackingEvent).filter(TrackingEvent.id == event_id).first()
    if not event_db:
        raise HTTPException(status_code=404, detail='Мындай окуя жок')
    if event_db.delivery.delivery_status in [DeliveryStatus.delivered, DeliveryStatus.cancelled]:
        raise HTTPException(status_code=400, detail='Аяктаган доставканын окуясын өчүрүүгө болбойт')
    db.delete(event_db)
    db.commit()
    return {'message': 'Окуя өчүрүлдү'}