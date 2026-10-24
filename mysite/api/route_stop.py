from mysite.database.models import RouteStop, Route, Delivery, RouteStatus, StopStatus, StopType, DeliveryStatus
from mysite.database.schema import RouteStopInputSchema, RouteStopOutSchema
from mysite.database.db import SessionLocal
from mysite.dependencies import get_current_user
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends
from typing import List

route_stop_router = APIRouter(prefix='/route_stop', tags=['RouteStop'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@route_stop_router.post('/', response_model=RouteStopOutSchema)
async def create_route_stop(stop: RouteStopInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Токтоочу жер кошууга уруксат жок')
    route_db = db.query(Route).filter(Route.id == stop.route_id).first()
    if not route_db:
        raise HTTPException(status_code=404, detail='Мындай маршрут жок')
    delivery_db = db.query(Delivery).filter(Delivery.id == stop.delivery_id).first()
    if not delivery_db:
        raise HTTPException(status_code=404, detail='Мындай доставка жок')
    if route_db.status != RouteStatus.planned:
        raise HTTPException(status_code=400, detail='Пландалган маршрутка гана токтоочу жер кошууга болот')
    if delivery_db.delivery_status in [DeliveryStatus.delivered, DeliveryStatus.cancelled]:
        raise HTTPException(status_code=400, detail='Бул доставка аяктаган же жокко чыгарылган')
    if route_db.courier_id != delivery_db.courier_id:
        raise HTTPException(status_code=400, detail='Маршрут менен доставканын курьери дал келбейт')
    sequence_db = db.query(RouteStop).filter(RouteStop.route_id == stop.route_id, RouteStop.sequence == stop.sequence).first()
    if sequence_db:
        raise HTTPException(status_code=400, detail='Бул маршрутта мындай кезек номери бар')
    stop_db = db.query(RouteStop).filter(RouteStop.route_id == stop.route_id, RouteStop.delivery_id == stop.delivery_id, RouteStop.stop_type == stop.stop_type).first()
    if stop_db:
        raise HTTPException(status_code=400, detail='Бул доставка үчүн мындай токтоочу жер бар')
    if stop.status != StopStatus.pending:
        raise HTTPException(status_code=400, detail='Жаңы токтоочу жер pending статусунда болушу керек')
    route_stop_db = RouteStop(**stop.model_dump())
    db.add(route_stop_db)
    db.commit()
    db.refresh(route_stop_db)
    return route_stop_db

@route_stop_router.get('/', response_model=List[RouteStopOutSchema])
async def list_route_stop(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] == 'manager':
        return db.query(RouteStop).order_by(RouteStop.route_id, RouteStop.sequence).all()
    if current_user['status'] == 'courier':
        return db.query(RouteStop).join(Route).join(Route.courier).filter(Courier.user_id == current_user['id']).order_by(RouteStop.route_id, RouteStop.sequence).all()
    raise HTTPException(status_code=403, detail='Токтоочу жерлерди көрүүгө уруксат жок')

@route_stop_router.get('/{stop_id}/', response_model=RouteStopOutSchema)
async def detail_route_stop(stop_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] not in ['manager', 'courier']:
        raise HTTPException(status_code=403, detail='Токтоочу жерди көрүүгө уруксат жок')
    stop_db = db.query(RouteStop).filter(RouteStop.id == stop_id).first()
    if not stop_db:
        raise HTTPException(status_code=404, detail='Мындай токтоочу жер жок')
    if current_user['status'] == 'courier' and stop_db.route.courier.user_id != current_user['id']:
        raise HTTPException(status_code=403, detail='Башка курьердин токтоочу жерин көрүүгө уруксат жок')
    return stop_db

@route_stop_router.put('/{stop_id}/', response_model=dict)
async def update_route_stop(stop_id: int, stop: RouteStopInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] not in ['manager', 'courier']:
        raise HTTPException(status_code=403, detail='Токтоочу жерди өзгөртүүгө уруксат жок')
    stop_db = db.query(RouteStop).filter(RouteStop.id == stop_id).first()
    if not stop_db:
        raise HTTPException(status_code=404, detail='Мындай токтоочу жер жок')
    if current_user['status'] == 'courier':
        if stop_db.route.courier.user_id != current_user['id']:
            raise HTTPException(status_code=403, detail='Башка курьердин токтоочу жерин өзгөртүүгө уруксат жок')
        if stop.route_id != stop_db.route_id or stop.delivery_id != stop_db.delivery_id or stop.stop_type != stop_db.stop_type or stop.sequence != stop_db.sequence or stop.latitude != stop_db.latitude or stop.longitude != stop_db.longitude:
            raise HTTPException(status_code=403, detail='Токтоочу жердин бул маалыматтарын өзгөртүүгө уруксат жок')
    route_db = db.query(Route).filter(Route.id == stop.route_id).first()
    if not route_db:
        raise HTTPException(status_code=404, detail='Мындай маршрут жок')
    delivery_db = db.query(Delivery).filter(Delivery.id == stop.delivery_id).first()
    if not delivery_db:
        raise HTTPException(status_code=404, detail='Мындай доставка жок')
    if stop.route_id != stop_db.route_id or stop.delivery_id != stop_db.delivery_id:
        raise HTTPException(status_code=400, detail='Маршрутту же доставканы өзгөртүүгө болбойт')
    if route_db.status in [RouteStatus.completed, RouteStatus.cancelled]:
        raise HTTPException(status_code=400, detail='Аяктаган маршруттун токтоочу жерин өзгөртүүгө болбойт')
    if route_db.courier_id != delivery_db.courier_id:
        raise HTTPException(status_code=400, detail='Маршрут менен доставканын курьери дал келбейт')
    if stop.stop_type != stop_db.stop_type:
        raise HTTPException(status_code=400, detail='Токтоочу жердин түрүн өзгөртүүгө болбойт')
    if stop_db.status in [StopStatus.completed, StopStatus.skipped]:
        raise HTTPException(status_code=400, detail='Аяктаган токтоочу жерди өзгөртүүгө болбойт')
    sequence_db = db.query(RouteStop).filter(RouteStop.route_id == stop.route_id, RouteStop.sequence == stop.sequence, RouteStop.id != stop_id).first()
    if sequence_db:
        raise HTTPException(status_code=400, detail='Бул маршрутта мындай кезек номери бар')
    if route_db.status == RouteStatus.planned and stop.status != StopStatus.pending:
        raise HTTPException(status_code=400, detail='Маршрут баштала элек')
    if stop_db.status == StopStatus.pending and stop.status == StopStatus.completed:
        raise HTTPException(status_code=400, detail='Алгач arrived статусуна өтүшү керек')
    if stop_db.status == StopStatus.arrived and stop.status == StopStatus.pending:
        raise HTTPException(status_code=400, detail='Статусту артка өзгөртүүгө болбойт')
    if route_db.status == RouteStatus.active and stop.sequence != stop_db.sequence:
        raise HTTPException(status_code=400, detail='Активдүү маршруттун кезегин өзгөртүүгө болбойт')
    if stop.stop_type == StopType.dropoff and stop.status == StopStatus.completed:
        pickup_db = db.query(RouteStop).filter(RouteStop.route_id == stop.route_id, RouteStop.delivery_id == stop.delivery_id, RouteStop.stop_type == StopType.pickup, RouteStop.status == StopStatus.completed).first()
        if not pickup_db:
            raise HTTPException(status_code=400, detail='Алгач товар складдан алынышы керек')
    for stop_key, stop_value in stop.model_dump().items():
        setattr(stop_db, stop_key, stop_value)
    db.commit()
    db.refresh(stop_db)
    return {'message': 'Токтоочу жер өзгөрүлдү'}

@route_stop_router.delete('/{stop_id}/', response_model=dict)
async def delete_route_stop(stop_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Токтоочу жерди өчүрүүгө уруксат жок')
    stop_db = db.query(RouteStop).filter(RouteStop.id == stop_id).first()
    if not stop_db:
        raise HTTPException(status_code=404, detail='Мындай токтоочу жер жок')
    if stop_db.route.status != RouteStatus.planned:
        raise HTTPException(status_code=400, detail='Пландалган маршруттун гана токтоочу жерин өчүрүүгө болот')
    if stop_db.status != StopStatus.pending:
        raise HTTPException(status_code=400, detail='Бул токтоочу жерди өчүрүүгө болбойт')
    db.delete(stop_db)
    db.commit()
    return {'message': 'Токтоочу жер өчүрүлдү'}