# models.py
import os
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, TIMESTAMP, create_engine
from sqlalchemy.dialects.postgresql import UUID #VECTOR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@hostname:port/dbname")

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default='uuid_generate_v4()')
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    cart_id = Column(UUID(as_uuid=True), ForeignKey('carts.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default='now()')
    updated_at = Column(TIMESTAMP(timezone=True), default='now()')

class Cart(Base):
    __tablename__ = "carts"

    id = Column(UUID(as_uuid=True), primary_key=True, default='uuid_generate_v4()')
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    is_complete = Column(Boolean, default=False, nullable=False)
    is_reminder_sent = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default='now()')
    updated_at = Column(TIMESTAMP(timezone=True), default='now()')

class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default='uuid_generate_v4()')
    name = Column(Text, nullable=False)
    products = relationship("Product", back_populates="category")

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(UUID(as_uuid=True), primary_key=True, default='gen_random_uuid()')
    created_at = Column(TIMESTAMP(timezone=True), default='now()', nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default='now()', nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    code = Column(Text, nullable=False)
    expiration_date = Column(TIMESTAMP(timezone=True), nullable=False)
    amount = Column(Integer)
    percent_or_value = Column(Text)

class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(UUID(as_uuid=True), primary_key=True, default='uuid_generate_v4()')
    name = Column(Text, nullable=False)
    products = relationship("Product", back_populates="manufacturer")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default='gen_random_uuid()')
    created_at = Column(TIMESTAMP(timezone=True), default='now()', nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default='now()', nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    message = Column(Text, nullable=False)

class Order(Base):
    __tablename__ = "orders"

    created_at = Column(TIMESTAMP(timezone=True), default='now()', nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default='now()', nullable=False)
    id = Column(UUID(as_uuid=True), primary_key=True, default='gen_random_uuid()')
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    status = Column(Text, nullable=False)
    delivery_date = Column(TIMESTAMP(timezone=True))
    is_reviewed = Column(Boolean, default=False, nullable=False)

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default='uuid_generate_v4()')
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    manufacturer_id = Column(UUID(as_uuid=True), ForeignKey('manufacturers.id'), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey('categories.id'), nullable=False)
    image = Column(Text, nullable=False)
    country_of_origin = Column(Text, nullable=False)
    #vector = Column(VECTOR(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default='now()', nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default='now()', nullable=False)
    manufacturer = relationship("Manufacturer", back_populates="products")
    category = relationship("Category", back_populates="products")
    reviews = relationship("Review", back_populates="product")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default='uuid_generate_v4()')
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    rating = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    is_visible = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default='now()', nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default='now()', nullable=False)
    product = relationship("Product", back_populates="reviews")

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default='uuid_generate_v4()')
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    last_seen = Column(TIMESTAMP(timezone=True))
    password = Column(Text)
    is_email_verified = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), default='now()', nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default='now()', nullable=False)
