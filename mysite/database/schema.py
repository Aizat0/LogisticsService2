from pydantic import BaseModel, Field
from datetime import datetime
from .models import WarehouseStatus, InventoryReservationStatus, TransportType, CourierStatus, DeliveryStatus, RouteStatus, StopType, StopStatus


class WarehouseInputSchema(BaseModel):
    city_id: int = Field(ge=1)
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=150)
    street: str = Field(min_length=2, max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    capacity: int = Field(ge=0)
    status: WarehouseStatus = WarehouseStatus.active


class WarehouseOutSchema(BaseModel):
    id: int
    city_id: int
    code: str
    name: str
    street: str
    latitude: float
    longitude: float
    capacity: int
    status: WarehouseStatus
    created_at: datetime


class InventoryInputSchema(BaseModel):
    product_id: int = Field(ge=1)
    quantity: int = Field(ge=0)
    reserved_quantity: int = Field(ge=0)
    warehouse_id: int = Field(ge=1)


class InventoryOutSchema(BaseModel):
    id: int
    product_id: int
    quantity: int
    reserved_quantity: int
    updated_at: datetime
    warehouse_id: int


class InventoryReservationInputSchema(BaseModel):
    order_id: int = Field(ge=1)
    quantity: int = Field(gt=0)
    status_inventory: InventoryReservationStatus = InventoryReservationStatus.active
    expires_at: datetime
    inventory_id: int = Field(ge=1)


class InventoryReservationOutSchema(BaseModel):
    id: int
    order_id: int
    quantity: int
    status_inventory: InventoryReservationStatus
    expires_at: datetime
    created_at: datetime
    inventory_id: int


class CourierInputSchema(BaseModel):
    user_id: int = Field(ge=1)
    transport_type: TransportType = TransportType.walking
    status_courier: CourierStatus = CourierStatus.offline
    max_active_orders: int = Field(ge=1)
    warehouse_id: int = Field(ge=1)


class CourierOutSchema(BaseModel):
    id: int
    user_id: int
    transport_type: TransportType
    status_courier: CourierStatus
    max_active_orders: int
    created_at: datetime
    warehouse_id: int


class CourierLocationInputSchema(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    courier_id: int = Field(ge=1)


class CourierLocationOutSchema(BaseModel):
    id: int
    latitude: float
    longitude: float
    recorded_at: datetime
    courier_id: int


class DeliveryInputSchema(BaseModel):
    order_id: int = Field(ge=1)
    tracking_code: str = Field(min_length=2, max_length=100)
    delivery_status: DeliveryStatus = DeliveryStatus.pending
    destination_address: str = Field(min_length=2, max_length=255)
    destination_latitude: float = Field(ge=-90, le=90)
    destination_longitude: float = Field(ge=-180, le=180)
    estimated_delivery_at: datetime
    delivered_at: datetime
    warehouse_id: int = Field(ge=1)
    courier_id: int = Field(ge=1)


class DeliveryOutSchema(BaseModel):
    id: int
    order_id: int
    tracking_code: str
    delivery_status: DeliveryStatus
    destination_address: str
    destination_latitude: float
    destination_longitude: float
    estimated_delivery_at: datetime
    delivered_at: datetime
    created_at: datetime
    warehouse_id: int
    courier_id: int


class RouteInputSchema(BaseModel):
    courier_id: int = Field(ge=1)
    status: RouteStatus = RouteStatus.planned
    total_distance_km: float = Field(ge=0)
    estimated_duration_min: int = Field(ge=0)
    started_at: datetime
    completed_at: datetime


class RouteOutSchema(BaseModel):
    id: int
    courier_id: int
    status: RouteStatus
    total_distance_km: float
    estimated_duration_min: int
    started_at: datetime
    completed_at: datetime
    created_at: datetime


class RouteStopInputSchema(BaseModel):
    route_id: int = Field(ge=1)
    delivery_id: int = Field(ge=1)
    stop_type: StopType
    sequence: int = Field(ge=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    status: StopStatus = StopStatus.pending
    arrived_at: datetime


class RouteStopOutSchema(BaseModel):
    id: int
    route_id: int
    delivery_id: int
    stop_type: StopType
    sequence: int
    latitude: float
    longitude: float
    status: StopStatus
    arrived_at: datetime


class TrackingEventInputSchema(BaseModel):
    delivery_id: int = Field(ge=1)
    status: str = Field(min_length=2, max_length=50)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    description: str = Field(min_length=1)


class TrackingEventOutSchema(BaseModel):
    id: int
    delivery_id: int
    status: str
    latitude: float
    longitude: float
    description: str
    created_at: datetime