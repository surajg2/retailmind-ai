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

# Product Schemas
class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = "General"
    unit: Optional[str] = "pcs"
    cost_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    selling_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    min_stock_level: int = Field(default=10, ge=0)

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    cost_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    min_stock_level: Optional[int] = None
    is_active: Optional[bool] = None

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
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Sales Schemas
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

# Analytics & Dashboard Response Schemas
class AnalyticsSummary(BaseModel):
    total_revenue: Decimal
    observed_units_sold: int
    avg_revenue_per_recorded_day: Decimal
    active_catalog_size: int
    confirmed_stockout_days: int
    zero_eod_stock_days: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class SalesTrendPoint(BaseModel):
    sale_date: date
    revenue: Decimal
    units_sold: int
    promo_active: bool = False

class CategoryBreakdown(BaseModel):
    category: str
    revenue: Decimal
    units_sold: int
    percentage_share: float

class TopProductItem(BaseModel):
    product_id: int
    sku: str
    name: str
    category: Optional[str]
    total_revenue: Decimal
    total_units_sold: int

class ProductPerformancePoint(BaseModel):
    sale_date: date
    units_sold: int
    selling_price: Decimal
    stock_available: int
    is_stockout: Optional[bool] = None

class DataQualityReport(BaseModel):
    quality_score: float # 0.0 to 100.0
    total_recorded_days: int
    expected_days: int
    date_coverage_ratio: float # 0.0 to 1.0
    date_gaps_count: int
    anomalies_count: int
    stockout_censored_ratio: float # Operational business indicator
    status: str # Excellent, Good, Warning, Poor


# Phase 4B Forecast Schemas
class ForecastGenerateRequest(BaseModel):
    product_id: Optional[int] = None

class ForecastPoint(BaseModel):
    forecast_date: date
    predicted_units: float
    actual_units: Optional[float] = None

class ForecastProductInfo(BaseModel):
    id: int
    sku: str
    name: str
    category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ForecastMetadata(BaseModel):
    model_name: str = "XGBoost"
    model_version: str = "xgb-v1"
    training_cutoff_date: date
    generated_at: datetime
    horizon_days: int = 7
    disclaimer: str = "Forecasts estimate future observed units sold based on historical observations."
    historical_stockout_ratio: Optional[float] = None

class SkippedProductInfo(BaseModel):
    product_id: int
    sku: Optional[str] = None
    name: Optional[str] = None
    reason: str = "INSUFFICIENT_HISTORY"

class ForecastItem(BaseModel):
    id: int
    business_id: int
    product_id: int
    forecast_date: date
    predicted_units: float
    model_name: str
    model_version: str
    training_cutoff_date: date
    horizon_days: int
    generated_at: datetime
    actual_units: Optional[float] = None
    product: Optional[ForecastProductInfo] = None

    model_config = ConfigDict(from_attributes=True)

class ForecastGenerationResponse(BaseModel):
    business_id: int
    generated_count: int
    skipped_count: int
    skipped_products: List[SkippedProductInfo] = []
    metadata: ForecastMetadata
    forecasts: List[ForecastItem] = []

class ForecastListResponse(BaseModel):
    total_records: int
    metadata: Optional[ForecastMetadata] = None
    forecasts: List[ForecastItem]

class ProductForecastResponse(BaseModel):
    product: ForecastProductInfo
    metadata: ForecastMetadata
    forecast: List[ForecastPoint]

class LatestForecastProductGroup(BaseModel):
    product: ForecastProductInfo
    forecast: List[ForecastPoint]

class LatestForecastResponse(BaseModel):
    business_id: int
    generated_at: datetime
    model_version: str
    training_cutoff_date: date
    horizon_days: int
    total_products: int
    products: List[LatestForecastProductGroup]
