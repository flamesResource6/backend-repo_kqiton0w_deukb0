"""
Database Schemas for ZÈLE Ecommerce

Each Pydantic model represents a MongoDB collection.
Collection name is the lowercase of the class name.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    slug: str = Field(..., description="URL-friendly unique identifier")
    description: str = Field(..., description="Long form description")
    short_description: Optional[str] = Field(None, description="Short teaser copy")
    price: float = Field(..., ge=0, description="Price in USD")
    category: str = Field(..., description="formal | casual | bestseller | new")
    colors: List[str] = Field(default_factory=list, description="Available colors")
    sizes: List[int] = Field(default_factory=list, description="Available sizes (EU)")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    leather: Optional[str] = Field(None, description="Leather type")
    craftsmanship: Optional[str] = Field(None, description="Craftsmanship highlights")
    is_featured: bool = Field(default=False)

class Review(BaseModel):
    product_id: str = Field(..., description="ID of the reviewed product")
    name: str = Field(...)
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(...)
    created_at: Optional[datetime] = None

class OrderItem(BaseModel):
    product_id: str
    title: str
    price: float
    size: int
    color: str
    quantity: int = Field(..., ge=1)

class Address(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    country: str
    postal_code: str

class Order(BaseModel):
    items: List[OrderItem]
    shipping: Address
    subtotal: float = 0
    shipping_cost: float = 0
    total: float = 0
    status: str = Field("pending", description="pending | paid | shipped | delivered | cancelled")

class Newsletter(BaseModel):
    email: EmailStr

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str
