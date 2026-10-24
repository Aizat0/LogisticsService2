from mysite.database.models import Route, Courier, RouteStatus, CourierStatus
from mysite.database.schema import RouteInputSchema, RouteOutSchema
from mysite.database.db import SessionLocal
from mysite.dependencies import get_current_user
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends
from typing import List

route_router = APIRouter(prefix='/route', tags=['Route'])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@route_router.post('/', response_model=RouteOutSchema)
async def create_route(route: RouteInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Маршрут кошууга уруксат жок')
    courier_db = db.query(Courier).filter(Courier.id == route.courier_id).first()
    if not courier_db:
        raise HTTPException(status_code=404, detail='Мындай курьер жок')
    if courier_db.status_courier in [CourierStatus.offline, CourierStatus.suspended]:
        raise HTTPException(status_code=400, detail='Курьер жеткиликтүү эмес')
    if route.status != RouteStatus.planned:
        raise HTTPException(status_code=400, detail='Жаңы маршрут planned статусунда болушу керек')
    active_route = db.query(Route).filter(Route.courier_id == route.courier_id, Route.status.in_([RouteStatus.planned, RouteStatus.active])).first()
    if active_route:
        raise HTTPException(status_code=400, detail='Курьердин активдүү же пландалган маршруту бар')
    route_db = Route(**route.model_dump())
    db.add(route_db)
    db.commit()
    db.refresh(route_db)
    return route_db

@route_router.get('/', response_model=List[RouteOutSchema])
async def list_route(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] == 'manager':
        return db.query(Route).all()
    if current_user['status'] == 'courier':
        return db.query(Route).join(Courier).filter(Courier.user_id == current_user['id']).all()
    raise HTTPException(status_code=403, detail='Маршруттарды көрүүгө уруксат жок')

@route_router.get('/{route_id}/', response_model=RouteOutSchema)
async def detail_route(route_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] not in ['manager', 'courier']:
        raise HTTPException(status_code=403, detail='Маршрутту көрүүгө уруксат жок')
    route_db = db.query(Route).filter(Route.id == route_id).first()
    if not route_db:
        raise HTTPException(status_code=404, detail='Мындай маршрут жок')
    if current_user['status'] == 'courier' and route_db.courier.user_id != current_user['id']:
        raise HTTPException(status_code=403, detail='Башка курьердин маршрутун көрүүгө уруксат жок')
    return route_db

@route_router.put('/{route_id}/', response_model=dict)
async def update_route(route_id: int, route: RouteInputSchema, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] not in ['manager', 'courier']:
        raise HTTPException(status_code=403, detail='Маршрут өзгөртүүгө уруксат жок')
    route_db = db.query(Route).filter(Route.id == route_id).first()
    if not route_db:
        raise HTTPException(status_code=404, detail='Мындай маршрут жок')
    if current_user['status'] == 'courier':
        if route_db.courier.user_id != current_user['id']:
            raise HTTPException(status_code=403, detail='Башка курьердин маршрутун өзгөртүүгө уруксат жок')
        if route.courier_id != route_db.courier_id or route.total_distance_km != route_db.total_distance_km or route.estimated_duration_min != route_db.estimated_duration_min:
            raise HTTPException(status_code=403, detail='Маршруттун бул маалыматтарын өзгөртүүгө уруксат жок')
        if route.status not in [route_db.status, RouteStatus.active, RouteStatus.completed]:
            raise HTTPException(status_code=403, detail='Бул статуска өзгөртүүгө уруксат жок')
        if route.status == RouteStatus.active and route_db.status != RouteStatus.planned:
            raise HTTPException(status_code=400, detail='Маршрут planned статусунда болушу керек')
        if route.status == RouteStatus.completed and route_db.status != RouteStatus.active:
            raise HTTPException(status_code=400, detail='Маршрут active статусунда болушу керек')
        if route.status == route_db.status and (route.started_at != route_db.started_at or route.completed_at != route_db.completed_at):
            raise HTTPException(status_code=403, detail='Маршруттун убактысын өзгөртүүгө уруксат жок')
    courier_db = db.query(Courier).filter(Courier.id == route.courier_id).first()
    if not courier_db:
        raise HTTPException(status_code=404, detail='Мындай курьер жок')
    if route_db.status in [RouteStatus.completed, RouteStatus.cancelled]:
        raise HTTPException(status_code=400, detail='Аяктаган маршрутту өзгөртүүгө болбойт')
    if route.courier_id != route_db.courier_id:
        raise HTTPException(status_code=400, detail='Маршруттун курьерин өзгөртүүгө болбойт')
    if route_db.status == RouteStatus.active and route.status == RouteStatus.planned:
        raise HTTPException(status_code=400, detail='Статусту артка өзгөртүүгө болбойт')
    if route_db.status == RouteStatus.planned and route.status == RouteStatus.completed:
        raise HTTPException(status_code=400, detail='Маршрутту баштабай туруп аяктоого болбойт')
    if route.status == RouteStatus.active and courier_db.status_courier in [CourierStatus.offline, CourierStatus.suspended]:
        raise HTTPException(status_code=400, detail='Курьер жеткиликтүү эмес')
    if route.status == RouteStatus.completed:
        if not route_db.stops:
            raise HTTPException(status_code=400, detail='Маршрутта токтоочу жерлер жок')
        if any(stop.status.value not in ['completed', 'skipped'] for stop in route_db.stops):
            raise HTTPException(status_code=400, detail='Маршруттун бардык токтоочу жерлери аякташы керек')
    for route_key, route_value in route.model_dump().items():
        setattr(route_db, route_key, route_value)
    db.commit()
    db.refresh(route_db)
    return {'message': 'Маршрут өзгөрүлдү'}

@route_router.delete('/{route_id}/', response_model=dict)
async def delete_route(route_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user['status'] != 'manager':
        raise HTTPException(status_code=403, detail='Маршрут өчүрүүгө уруксат жок')
    route_db = db.query(Route).filter(Route.id == route_id).first()
    if not route_db:
        raise HTTPException(status_code=404, detail='Мындай маршрут жок')
    if route_db.status == RouteStatus.active:
        raise HTTPException(status_code=400, detail='Активдүү маршрутту өчүрүүгө болбойт')
    if route_db.status == RouteStatus.completed:
        raise HTTPException(status_code=400, detail='Аяктаган маршрутту өчүрүүгө болбойт')
    if route_db.stops:
        raise HTTPException(status_code=400, detail='Маршрутка байланышкан токтоочу жерлер бар')
    db.delete(route_db)
    db.commit()
    return {'message': 'Маршрут өчүрүлдү'}