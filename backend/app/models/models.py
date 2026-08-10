from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Index, Text
)
from sqlalchemy.orm import relationship
from backend.app.db.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=True) # e.g. Kirana, General Store, Supermarket
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    users = relationship("User", back_populates="business", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="business", cascade="all, delete-orphan")
    sales = relationship("Sales", back_populates="business", cascade="all, delete-orphan")
    inventory_items = relationship("Inventory", back_populates="business", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="business", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="business", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="owner", nullable=False) # e.g., owner, manager, staff
    is_active = Column(Boolean, default=True, nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    business = relationship("Business", back_populates="users")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)
    unit = Column(String(50), default="pcs") # e.g., kg, pcs, packet
    cost_price = Column(Float, nullable=False, default=0.0)
    selling_price = Column(Float, nullable=False, default=0.0)
    min_stock_level = Column(Integer, default=10, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    business = relationship("Business", back_populates="products")
    sales = relationship("Sales", back_populates="product", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="product", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_product_business_sku", "business_id", "sku", unique=True),
    )


class Sales(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)
    sale_date = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    business = relationship("Business", back_populates="sales")
    product = relationship("Product", back_populates="sales")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    current_stock = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False, default=15)
    last_restocked_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    business = relationship("Business", back_populates="inventory_items")
    product = relationship("Product", back_populates="inventory")


class Festival(Base):
    __tablename__ = "festivals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    start_date = Column(DateTime(timezone=True), nullable=False, index=True)
    end_date = Column(DateTime(timezone=True), nullable=False)
    region = Column(String(100), default="National", nullable=False)
    expected_uplift = Column(Float, default=1.2, nullable=False) # 1.2 = +20% demand
    created_at = Column(DateTime(timezone=True), default=utc_now)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version = Column(String(50), nullable=False, default="v1.0")
    predicted_demand = Column(Float, nullable=False)
    prediction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    business = relationship("Business", back_populates="predictions")
    product = relationship("Product", back_populates="predictions")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_type = Column(String(100), nullable=False, index=True) # e.g., RESTOCK, STOCKOUT_RISK, DEAD_STOCK
    details = Column(Text, nullable=True)
    status = Column(String(50), default="PENDING", nullable=False) # e.g., PENDING, APPLIED, DISMISSED
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    business = relationship("Business", back_populates="recommendations")
    product = relationship("Product", back_populates="recommendations")
