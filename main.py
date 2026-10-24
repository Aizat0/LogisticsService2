from fastapi import FastAPI
import uvicorn
from mysite.api import courier, courier_location, delivery, inventory, inventory_reservation, route, route_stop, tracking_event, warehouse

logistic_app = FastAPI(title='Logistics Project')
logistic_app.include_router(courier.courier_router)
logistic_app.include_router(courier_location.courier_location_router)
logistic_app.include_router(delivery.delivery_router)
logistic_app.include_router(inventory.inventory_router)
logistic_app.include_router(inventory_reservation.inventory_reservation_router)
logistic_app.include_router(route.route_router)
logistic_app.include_router(route_stop.route_stop_router)
logistic_app.include_router(tracking_event.tracking_event_router)
logistic_app.include_router(warehouse.warehouse_router)

if __name__ == '__main__':
    uvicorn.run(logistic_app, host='127.0.0.1', port=8001)