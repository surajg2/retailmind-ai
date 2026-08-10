from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

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
