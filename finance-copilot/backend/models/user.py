"""
User models for authentication and profile
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    """User creation model"""
    password: str


class User(UserBase):
    """User model with ID"""
    id: str
    created_at: datetime
    is_active: bool = True
    risk_profile: Optional[str] = None
    investment_horizon: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response model (without sensitive data)"""
    id: str
    email: str
    full_name: str
    created_at: datetime
    risk_profile: Optional[str] = None


class Token(BaseModel):
    """JWT Token model"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[str] = None
    email: Optional[str] = None


class RiskProfile(BaseModel):
    """User risk profile"""
    risk_tolerance: str  # conservative, moderate, aggressive
    investment_horizon: str  # short, medium, long
    investment_goals: list[str]
    annual_income: Optional[float] = None
    net_worth: Optional[float] = None
