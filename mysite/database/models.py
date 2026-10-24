from sqlalchemy import String, Integer, Text, DateTime, Enum, ForeignKey, Float
from typing import List
from .db import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from enum import Enum as PyEnum

class WarehouseStatus(str, PyEnum):
    active = 'active'
    inactive = 'inactive'
    maintenance = 'maintenance'

class Warehouse(Base):
    __tablename__ = 'warehouse'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_id: Mapped[int] = mapped_column(Integer)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(150))
    street: Mapped[str] = mapped_column(String(255), unique=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    capacity: Mapped[int] = mapped_column(Integer)
    status: Mapped[WarehouseStatus] = mapped_column(Enum(WarehouseStatus), default=WarehouseStatus.active)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ware_inventory: Mapped[List['Inventory']] = relationship(back_populates='inventory_ware', cascade='all, delete-orphan')
    courier_warehouse: Mapped[List['Courier']] = relationship(back_populates='warehouse_courier', cascade='all, delete-orphan')
    warehouse_delivery: Mapped[List['Delivery']] = relationship(back_populates='delivery_warehouse', cascade='all, delete-orphan')

class Inventory(Base):
    __tablename__ = 'inventory'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    reserved_quantity: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey('warehouse.id'))
    inventory_ware: Mapped[Warehouse] = relationship(Warehouse, back_populates='ware_inventory')
    inventory_reservation: Mapped[List['InventoryReservation']] = relationship(back_populates='reservation_inventory', cascade='all, delete-orphan')

class InventoryReservationStatus(str, PyEnum):
    active = 'active'
    committed = 'committed'
    released = 'released'
    expired = 'expired'

class InventoryReservation(Base):
    __tablename__ = 'inventory_reservation'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    status_inventory: Mapped[InventoryReservationStatus] = mapped_column(Enum(InventoryReservationStatus), default=InventoryReservationStatus.active)
    expires_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    inventory_id: Mapped[int] = mapped_column(ForeignKey('inventory.id'))
    reservation_inventory: Mapped[Inventory] = relationship(Inventory, back_populates='inventory_reservation')

class TransportType(str, PyEnum):
    walking = 'walking'
    bicycle = 'bicycle'
    motorcycle = 'motorcycle'
    car = 'car'

class CourierStatus(str, PyEnum):
    offline = 'offline'
    available = 'available'
    busy = 'busy'
    suspended = 'suspended'

class Courier(Base):
    __tablename__ = 'courier'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer)
    transport_type: Mapped[TransportType] = mapped_column(Enum(TransportType), default=TransportType.walking)
    status_courier: Mapped[CourierStatus] = mapped_column(Enum(CourierStatus), default=CourierStatus.offline)
    max_active_orders: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey('warehouse.id'))
    warehouse_courier: Mapped[Warehouse] = relationship(Warehouse, back_populates='courier_warehouse')
    courier_location: Mapped[List['CourierLocation']] = relationship(back_populates='location_courier', cascade='all, delete-orphan')
    delivery_courier: Mapped[List['Delivery']] = relationship(back_populates='courier_delivery', cascade='all, delete-orphan')
    routes: Mapped[List['Route']] = relationship(back_populates='courier', cascade='all, delete-orphan')

class CourierLocation(Base):
    __tablename__ = 'courier_location'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    courier_id: Mapped[int] = mapped_column(ForeignKey('courier.id'))
    location_courier: Mapped[Courier] = relationship(Courier, back_populates='courier_location')

class DeliveryStatus(str, PyEnum):
    pending = 'pending'
    assigned = 'assigned'
    delivered = 'delivered'
    cancelled = 'cancelled'

class Delivery(Base):
    __tablename__ = 'delivery'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer)
    tracking_code: Mapped[str] = mapped_column(String(100), unique=True)
    delivery_status: Mapped[DeliveryStatus] = mapped_column(Enum(DeliveryStatus), default=DeliveryStatus.pending)
    destination_address: Mapped[str] = mapped_column(String(255))
    destination_latitude: Mapped[float] = mapped_column(Float)
    destination_longitude: Mapped[float] = mapped_column(Float)
    estimated_delivery_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey('warehouse.id'))
    courier_id: Mapped[int] = mapped_column(ForeignKey('courier.id'))
    delivery_warehouse: Mapped[Warehouse] = relationship(Warehouse, back_populates='warehouse_delivery')
    courier_delivery: Mapped[Courier] = relationship(Courier, back_populates='delivery_courier')
    route_stops: Mapped[List['RouteStop']] = relationship(back_populates='delivery', cascade='all, delete-orphan')
    tracking_events: Mapped[List['TrackingEvent']] = relationship(back_populates='delivery', cascade='all, delete-orphan')

class RouteStatus(str, PyEnum):
    planned = 'planned'
    active = 'active'
    completed = 'completed'
    cancelled = 'cancelled'


class Route(Base):
    __tablename__ = 'route'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    courier_id: Mapped[int] = mapped_column(ForeignKey('courier.id'))
    status: Mapped[RouteStatus] = mapped_column(Enum(RouteStatus), default=RouteStatus.planned)
    total_distance_km: Mapped[float] = mapped_column(Float, default=0)
    estimated_duration_min: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    courier: Mapped['Courier'] = relationship(back_populates='routes')
    stops: Mapped[List['RouteStop']] = relationship(back_populates='route', cascade='all, delete-orphan')

class StopType(str, PyEnum):
    pickup = 'pickup'
    dropoff = 'dropoff'


class StopStatus(str, PyEnum):
    pending = 'pending'
    arrived = 'arrived'
    completed = 'completed'
    skipped = 'skipped'


class RouteStop(Base):
    __tablename__ = 'route_stop'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_id: Mapped[int] = mapped_column(ForeignKey('route.id'))
    delivery_id: Mapped[int] = mapped_column(ForeignKey('delivery.id'))
    stop_type: Mapped[StopType] = mapped_column(Enum(StopType))
    sequence: Mapped[int] = mapped_column(Integer)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    status: Mapped[StopStatus] = mapped_column(Enum(StopStatus), default=StopStatus.pending)
    arrived_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    route: Mapped['Route'] = relationship(back_populates='stops')
    delivery: Mapped['Delivery'] = relationship(back_populates='route_stops')

class TrackingEvent(Base):
    __tablename__ = 'tracking_event'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    delivery_id: Mapped[int] = mapped_column(ForeignKey('delivery.id'))
    status: Mapped[str] = mapped_column(String(50))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    delivery: Mapped['Delivery'] = relationship(back_populates='tracking_events')