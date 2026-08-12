from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict, Field

class BusinessCreate(BaseModel):
    name: str
    type: Optional[str] = "General Retail"
    location: Optional[str] = None

class BusinessOut(BaseModel):
    id: int
    name: str
    type: Optional[str]
    location: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = "General Retail"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    role: str
    is_active: bool
    business_id: Optional[int]
    business: Optional[BusinessOut] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HealthCheck(BaseModel):
    status: str
    database: str
    timestamp: datetime

# Product & Sales Schemas
class ProductOut(BaseModel):
    id: int
    business_id: int
    sku: str
    name: str
    category: Optional[str]
    unit: str
    cost_price: Decimal
    selling_price: Decimal
    min_stock_level: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SalesCreate(BaseModel):
    sku: str
    product_name: str
    category: str
    units_sold: int = Field(..., ge=0)
    selling_price: Decimal = Field(..., gt=0)
    promotion: bool = False
    holiday: bool = False
    festival: Optional[str] = None
    stock_available: int = Field(..., ge=0)
    is_stockout: Optional[bool] = None
    sale_date: date

class SalesOut(BaseModel):
    id: int
    business_id: int
    product_id: int
    quantity: int
    selling_price: Decimal
    total_amount: Decimal
    promotion: bool
    holiday: bool
    festival: Optional[str] = None
    stock_available: int
    is_stockout: Optional[bool] = None
    sale_date: date
    created_at: datetime
    product: Optional[ProductOut] = None

    model_config = ConfigDict(from_attributes=True)

class CSVRowError(BaseModel):
    row_number: int
    column: Optional[str] = None
    error: str

class CSVImportResult(BaseModel):
    success: bool
    total_rows_processed: int
    successful_imports: int
    errors: List[CSVRowError] = []
    message: str

class SyntheticGenResult(BaseModel):
    success: bool
    records_generated: int
    imported_count: int
    message: str
