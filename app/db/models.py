"""SQLAlchemy ORM models for the vehicle database."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Vehicle(Base):
    """Vehicle information table."""

    __tablename__ = "vehicles"

    vehicle_id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String(100), nullable=False, index=True)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True)
    vehicle_type = Column(String(50), nullable=True, comment="e.g. car, truck, motorcycle")

    images = relationship("VehicleImage", back_populates="vehicle", lazy="selectin")
    transactions = relationship("TransactionHistory", back_populates="vehicle", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Vehicle {self.brand} {self.model} ({self.year})>"


class Owner(Base):
    """Vehicle owners table."""

    __tablename__ = "owners"

    owner_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False, index=True)
    city = Column(String(100), nullable=True)
    email = Column(String(200), nullable=True)
    phone = Column(String(20), nullable=True)

    purchases = relationship(
        "TransactionHistory",
        foreign_keys="TransactionHistory.buyer_id",
        back_populates="buyer",
        lazy="selectin",
    )
    sales = relationship(
        "TransactionHistory",
        foreign_keys="TransactionHistory.seller_id",
        back_populates="seller",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Owner {self.first_name} {self.last_name}>"


class TransactionHistory(Base):
    """Transaction history table (purchases/sales)."""

    __tablename__ = "transaction_history"

    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("owners.owner_id"), nullable=True)
    transaction_date = Column(Date, nullable=False)
    price = Column(Float, nullable=False)

    vehicle = relationship("Vehicle", back_populates="transactions")
    buyer = relationship("Owner", foreign_keys=[buyer_id], back_populates="purchases")
    seller = relationship("Owner", foreign_keys=[seller_id], back_populates="sales")

    def __repr__(self) -> str:
        return f"<Transaction {self.transaction_id}: vehicle={self.vehicle_id}>"


class VehicleImage(Base):
    """Vehicle images table."""

    __tablename__ = "vehicle_images"

    image_id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id"), nullable=False)
    image_url = Column(Text, nullable=False, comment="Path or URL to the image file")

    vehicle = relationship("Vehicle", back_populates="images")

    def __repr__(self) -> str:
        return f"<VehicleImage {self.image_id} for vehicle={self.vehicle_id}>"
