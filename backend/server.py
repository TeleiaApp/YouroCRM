from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import io
import base64
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import json
import base64
import bcrypt
import secrets
from stdnum.eu import vat
from stdnum import util
import xml.etree.ElementTree as ET

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    picture: Optional[str] = None
    password_hash: Optional[str] = None  # For traditional auth
    auth_type: str = "google"  # "google" or "traditional"
    is_active: bool = True
    current_plan: str = "starter"  # starter, professional, enterprise
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Contact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Account(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    contact_id: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    # Separated address fields for VIES integration
    street: Optional[str] = None
    street_nr: Optional[str] = None
    box: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    vat_number: Optional[str] = None  # Important for Peppol and VIES
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    name: str
    description: Optional[str] = None
    price: float
    currency: str = "EUR"
    tax_rate: float = 0.21  # Belgium VAT rate
    sku: Optional[str] = None
    category: Optional[str] = None
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InvoiceItem(BaseModel):
    product_id: str
    quantity: float
    unit_price: float
    description: Optional[str] = None

class Invoice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    invoice_number: str
    account_id: str
    contact_id: Optional[str] = None
    items: List[InvoiceItem]
    subtotal: float
    tax_amount: float
    total_amount: float
    currency: str = "EUR"
    issue_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[datetime] = None
    status: str = "draft"  # draft, sent, paid, overdue, cancelled
    peppol_status: Optional[str] = None  # pending, sent, delivered, failed
    peppol_message_id: Optional[str] = None
    pdf_url: Optional[str] = None
    xml_url: Optional[str] = None
    notes: Optional[str] = None
    invoice_type: str = "invoice"  # invoice, credit_note
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CalendarEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    event_type: str  # meeting, invoice_due, deadline, call
    related_id: Optional[str] = None  # ID of related contact, account, or invoice
    related_type: Optional[str] = None  # contact, account, invoice
    location: Optional[str] = None
    all_day: bool = False
    reminder_minutes: Optional[int] = 30
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Create models for API requests
class ContactCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class AccountCreate(BaseModel):
    name: str
    contact_id: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    # Separated address fields for VIES integration
    street: Optional[str] = None
    street_nr: Optional[str] = None
    box: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    vat_number: Optional[str] = None
    notes: Optional[str] = None

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    currency: str = "EUR"
    tax_rate: float = 0.21
    sku: Optional[str] = None
    category: Optional[str] = None

class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    event_type: str
    related_id: Optional[str] = None
    related_type: Optional[str] = None
    location: Optional[str] = None
    all_day: bool = False
    reminder_minutes: Optional[int] = 30

# Payment Models
class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    payment_id: Optional[str] = None
    amount: float
    currency: str = "EUR"
    package_id: str
    payment_status: str = "pending"  # pending, paid, failed, expired
    metadata: Optional[dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CheckoutRequest(BaseModel):
    package_id: str
    success_url: str
    cancel_url: str
    metadata: Optional[dict] = None

class PayPalOrderRequest(BaseModel):
    package_id: str
    return_url: str
    cancel_url: str
    metadata: Optional[dict] = None

# Traditional Authentication Models
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    roles: Optional[List[str]] = []
    
class PlanSelection(BaseModel):
    plan_id: str  # starter, professional, enterprise

# VIES Response Models
class VIESResponse(BaseModel):
    valid: bool
    name: Optional[str] = None
    address: Optional[str] = None
    street: Optional[str] = None
    street_nr: Optional[str] = None
    box: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    request_date: Optional[str] = None

# Subscription Plans Models
class SubscriptionPlan(BaseModel):
    id: str
    name: str
    price: float
    currency: str = "EUR"
    billing_cycle: str = "monthly"  # monthly, yearly
    features: List[str]
    limits: dict
    is_popular: bool = False

class UserSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    plan_id: str
    status: str = "active"  # active, cancelled, expired
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Internationalization Models
class Translation(BaseModel):
    key: str
    language: str
    value: str

class LanguageResponse(BaseModel):
    language: str
    translations: dict

# User Roles and Admin Models
class UserRole(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    role: str  # admin, user, premium_user
    granted_by: str
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CustomField(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str  # contacts, accounts, products, invoices
    field_name: str
    field_type: str  # text, number, date, select, boolean
    field_options: Optional[List[str]] = None  # for select fields
    required: bool = False
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Authentication helper
async def get_current_user(request: Request) -> User:
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find session
    session = await db.sessions.find_one({"session_token": session_token})
    if not session:
        raise HTTPException(status_code=401, detail="Session not found")
    
    # Handle timezone-aware comparison
    expires_at = session["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Get user
    user = await db.users.find_one({"id": session["user_id"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user)

# Authentication routes
@api_router.get("/auth/profile")
async def get_profile(request: Request):
    """Handle profile redirect after OAuth login"""
    session_id = request.query_params.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")
    
    # Call Emergent auth API
    async with httpx.AsyncClient() as client:
        headers = {"X-Session-ID": session_id}
        response = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        user_data = response.json()
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data["email"]})
    if not existing_user:
        # Create new user
        user = User(
            email=user_data["email"],
            name=user_data["name"],
            picture=user_data.get("picture")
        )
        await db.users.insert_one(user.dict())
        user_id = user.id
    else:
        user_id = existing_user["id"]
    
    # Create session
    session_token = user_data["session_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session = Session(
        user_id=user_id,
        session_token=session_token,
        expires_at=expires_at
    )
    await db.sessions.insert_one(session.dict())
    
    return {"user_id": user_id, "session_token": session_token}

@api_router.post("/auth/set-session")
async def set_session(response: Response, session_token: str):
    """Set session cookie"""
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=7 * 24 * 60 * 60,  # 7 days
        httponly=True,
        secure=True,
        samesite="none",
        path="/"
    )
    return {"message": "Session set"}

@api_router.post("/auth/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    """Logout user"""
    response.delete_cookie("session_token", path="/")
    return {"message": "Logged out"}

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user"""
    return current_user

# Traditional Authentication Routes
@api_router.post("/auth/register")
async def register_user(user_data: UserRegister):
    """Register a new user with email and password"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hash_password(user_data.password),
        auth_type="traditional"
    )
    
    await db.users.insert_one(user.dict())
    
    return {"message": "User registered successfully", "user_id": user.id}

@api_router.post("/auth/login")
async def login_user(response: Response, login_data: UserLogin):
    """Login user with email and password"""
    # Find user
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = User(**user_doc)
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is disabled")
    
    # Verify password for traditional auth users
    if user.auth_type == "traditional":
        if not user.password_hash or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
    else:
        raise HTTPException(status_code=401, detail="This account uses Google authentication")
    
    # Create session
    session_token = generate_session_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session = Session(
        user_id=user.id,
        session_token=session_token,
        expires_at=expires_at
    )
    await db.sessions.insert_one(session.dict())
    
    # Set session cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=7 * 24 * 60 * 60,  # 7 days
        httponly=True,
        secure=True,
        samesite="none",
        path="/"
    )
    
    # Return user data without sensitive fields
    user_data = user.dict()
    user_data.pop("password_hash", None)  # Remove password_hash for security
    
    return {"message": "Login successful", "user": user_data, "session_token": session_token}

# Subscription Plans routes
@api_router.get("/plans")
async def get_plans():
    """Get all available subscription plans"""
    return list(SUBSCRIPTION_PLANS.values())

@api_router.post("/users/select-plan")
async def select_plan(plan_selection: PlanSelection, current_user: User = Depends(get_current_user)):
    """Select a subscription plan for current user"""
    if plan_selection.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan selected")
    
    # Update user's current plan
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {"current_plan": plan_selection.plan_id}}
    )
    
    # Create subscription record
    subscription = UserSubscription(
        user_id=current_user.id,
        plan_id=plan_selection.plan_id
    )
    await db.user_subscriptions.insert_one(subscription.dict())
    
    return {"message": "Plan selected successfully", "plan": SUBSCRIPTION_PLANS[plan_selection.plan_id]}

@api_router.get("/users/plan")
async def get_user_plan(current_user: User = Depends(get_current_user)):
    """Get current user's subscription plan"""
    plan = get_user_plan(current_user)
    
    # Get usage statistics
    contacts_count = await db.contacts.count_documents({"user_id": current_user.id})
    accounts_count = await db.accounts.count_documents({"user_id": current_user.id})
    
    return {
        "plan": plan,
        "usage": {
            "contacts": contacts_count,
            "accounts": accounts_count
        },
        "limits": {
            "contacts_limit_reached": not check_plan_limits(current_user, "contacts", contacts_count),
            "accounts_limit_reached": not check_plan_limits(current_user, "accounts", accounts_count)
        }
    }

# Internationalization routes
@api_router.get("/translations/{language}")
async def get_translations_by_language(language: str):
    """Get translations for specified language"""
    if language not in TRANSLATIONS:
        raise HTTPException(status_code=404, detail="Language not supported")
    
    return LanguageResponse(
        language=language,
        translations=get_translations(language)
    )

@api_router.get("/languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "languages": [
            {"code": "en", "name": "English", "flag": "🇬🇧"},
            {"code": "fr", "name": "Français", "flag": "🇫🇷"},
            {"code": "nl", "name": "Nederlands", "flag": "🇳🇱"}
        ],
        "default": "en"
    }

# Contact routes
@api_router.post("/contacts", response_model=Contact)
async def create_contact(contact_data: ContactCreate, current_user: User = Depends(get_current_user)):
    # Check plan limits
    current_contacts = await db.contacts.count_documents({"user_id": current_user.id})
    if not check_plan_limits(current_user, "contacts", current_contacts):
        plan = get_user_plan(current_user)
        raise HTTPException(
            status_code=403, 
            detail=f"Plan limit reached. {plan.name} plan allows maximum {plan.limits['contacts_max']} contacts. Upgrade to Professional for unlimited contacts."
        )
    
    contact_dict = contact_data.dict()
    contact_dict["user_id"] = current_user.id
    contact = Contact(**contact_dict)
    await db.contacts.insert_one(contact.dict())
    return contact

@api_router.get("/contacts", response_model=List[Contact])
async def get_contacts(current_user: User = Depends(get_current_user)):
    contacts = await db.contacts.find({"user_id": current_user.id}).to_list(1000)
    return [Contact(**contact) for contact in contacts]

@api_router.get("/contacts/{contact_id}", response_model=Contact)
async def get_contact(contact_id: str, current_user: User = Depends(get_current_user)):
    contact = await db.contacts.find_one({"id": contact_id, "user_id": current_user.id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return Contact(**contact)

@api_router.put("/contacts/{contact_id}", response_model=Contact)
async def update_contact(contact_id: str, contact_data: ContactCreate, current_user: User = Depends(get_current_user)):
    contact = await db.contacts.find_one({"id": contact_id, "user_id": current_user.id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    update_data = contact_data.dict()
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.contacts.update_one({"id": contact_id}, {"$set": update_data})
    updated_contact = await db.contacts.find_one({"id": contact_id})
    return Contact(**updated_contact)

@api_router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, current_user: User = Depends(get_current_user)):
    result = await db.contacts.delete_one({"id": contact_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted"}

# Account routes
@api_router.post("/accounts", response_model=Account)
async def create_account(account_data: AccountCreate, current_user: User = Depends(get_current_user)):
    # Check plan limits
    current_accounts = await db.accounts.count_documents({"user_id": current_user.id})
    if not check_plan_limits(current_user, "accounts", current_accounts):
        plan = get_user_plan(current_user)
        raise HTTPException(
            status_code=403, 
            detail=f"Plan limit reached. {plan.name} plan allows maximum {plan.limits['accounts_max']} accounts. Upgrade to Professional for unlimited accounts."
        )
    
    account_dict = account_data.dict()
    account_dict["user_id"] = current_user.id
    account = Account(**account_dict)
    await db.accounts.insert_one(account.dict())
    return account

@api_router.get("/accounts", response_model=List[Account])
async def get_accounts(current_user: User = Depends(get_current_user)):
    accounts = await db.accounts.find({"user_id": current_user.id}).to_list(1000)
    return [Account(**account) for account in accounts]

@api_router.get("/accounts/{account_id}", response_model=Account)
async def get_account(account_id: str, current_user: User = Depends(get_current_user)):
    account = await db.accounts.find_one({"id": account_id, "user_id": current_user.id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return Account(**account)

@api_router.put("/accounts/{account_id}", response_model=Account)
async def update_account(account_id: str, account_data: AccountCreate, current_user: User = Depends(get_current_user)):
    account = await db.accounts.find_one({"id": account_id, "user_id": current_user.id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    update_data = account_data.dict()
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.accounts.update_one({"id": account_id}, {"$set": update_data})
    updated_account = await db.accounts.find_one({"id": account_id})
    return Account(**updated_account)

@api_router.delete("/accounts/{account_id}")
async def delete_account(account_id: str, current_user: User = Depends(get_current_user)):
    result = await db.accounts.delete_one({"id": account_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account deleted"}

# VIES VAT validation route
@api_router.get("/accounts/vies-lookup/{vat_number}", response_model=VIESResponse)
async def vies_lookup(vat_number: str, current_user: User = Depends(get_current_user)):
    """Validate VAT number and retrieve company information from VIES"""
    # Check if user has access to VIES integration
    if not has_feature_access(current_user, "vies_integration"):
        plan = get_user_plan(current_user)
        raise HTTPException(
            status_code=403, 
            detail=f"VIES integration not available in {plan.name} plan. Upgrade to Professional to access EU company data auto-completion."
        )
    
    try:
        vies_data = await validate_vat_with_vies(vat_number)
        return vies_data
    except Exception as e:
        logger.error(f"VIES lookup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate VAT number with VIES")

# Product routes
@api_router.post("/products", response_model=Product)
async def create_product(product_data: ProductCreate, current_user: User = Depends(get_current_user)):
    product_dict = product_data.dict()
    product_dict["user_id"] = current_user.id
    product = Product(**product_dict)
    await db.products.insert_one(product.dict())
    return product

@api_router.get("/products", response_model=List[Product])
async def get_products(current_user: User = Depends(get_current_user)):
    products = await db.products.find({"user_id": current_user.id}).to_list(1000)
    return [Product(**product) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str, current_user: User = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id, "user_id": current_user.id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_data: ProductCreate, current_user: User = Depends(get_current_user)):
    product = await db.products.find_one({"id": product_id, "user_id": current_user.id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_data.dict()
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.products.update_one({"id": product_id}, {"$set": update_data})
    updated_product = await db.products.find_one({"id": product_id})
    return Product(**updated_product)

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, current_user: User = Depends(get_current_user)):
    result = await db.products.delete_one({"id": product_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}

# Calendar routes
@api_router.post("/calendar/events", response_model=CalendarEvent)
async def create_event(event_data: CalendarEventCreate, current_user: User = Depends(get_current_user)):
    event_dict = event_data.dict()
    event_dict["user_id"] = current_user.id
    event = CalendarEvent(**event_dict)
    await db.calendar_events.insert_one(event.dict())
    return event

@api_router.get("/calendar/events", response_model=List[CalendarEvent])
async def get_events(current_user: User = Depends(get_current_user)):
    events = await db.calendar_events.find({"user_id": current_user.id}).to_list(1000)
    return [CalendarEvent(**event) for event in events]

@api_router.get("/calendar/events/{event_id}", response_model=CalendarEvent)
async def get_event(event_id: str, current_user: User = Depends(get_current_user)):
    event = await db.calendar_events.find_one({"id": event_id, "user_id": current_user.id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return CalendarEvent(**event)

@api_router.put("/calendar/events/{event_id}", response_model=CalendarEvent)
async def update_event(event_id: str, event_data: CalendarEventCreate, current_user: User = Depends(get_current_user)):
    event = await db.calendar_events.find_one({"id": event_id, "user_id": current_user.id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    update_data = event_data.dict()
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.calendar_events.update_one({"id": event_id}, {"$set": update_data})
    updated_event = await db.calendar_events.find_one({"id": event_id})
    return CalendarEvent(**updated_event)

@api_router.delete("/calendar/events/{event_id}")
async def delete_event(event_id: str, current_user: User = Depends(get_current_user)):
    result = await db.calendar_events.delete_one({"id": event_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted"}

# Invoice creation models
class InvoiceItemCreate(BaseModel):
    product_id: str
    quantity: float
    unit_price: float
    description: Optional[str] = None

class InvoiceCreate(BaseModel):
    account_id: str
    contact_id: Optional[str] = None
    items: List[InvoiceItemCreate]
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    invoice_type: str = "invoice"

# Invoice routes
@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice_data: InvoiceCreate, current_user: User = Depends(get_current_user)):
    # Generate invoice number
    invoice_count = await db.invoices.count_documents({"user_id": current_user.id})
    invoice_number = f"INV-{datetime.now().year}-{invoice_count + 1:04d}"
    
    # Calculate totals
    subtotal = sum(item.quantity * item.unit_price for item in invoice_data.items)
    tax_rate = 0.21  # Belgium VAT rate
    tax_amount = subtotal * tax_rate
    total_amount = subtotal + tax_amount
    
    invoice_dict = invoice_data.dict()
    invoice_dict.update({
        "user_id": current_user.id,
        "invoice_number": invoice_number,
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "total_amount": total_amount
    })
    
    invoice = Invoice(**invoice_dict)
    await db.invoices.insert_one(invoice.dict())
    return invoice

@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices(current_user: User = Depends(get_current_user)):
    invoices = await db.invoices.find({"user_id": current_user.id}).to_list(1000)
    return [Invoice(**invoice) for invoice in invoices]

@api_router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str, current_user: User = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id, "user_id": current_user.id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return Invoice(**invoice)

@api_router.put("/invoices/{invoice_id}", response_model=Invoice)
async def update_invoice(invoice_id: str, invoice_data: InvoiceCreate, current_user: User = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id, "user_id": current_user.id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Recalculate totals
    subtotal = sum(item.quantity * item.unit_price for item in invoice_data.items)
    tax_rate = 0.21
    tax_amount = subtotal * tax_rate
    total_amount = subtotal + tax_amount
    
    update_data = invoice_data.dict()
    update_data.update({
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "updated_at": datetime.now(timezone.utc)
    })
    
    await db.invoices.update_one({"id": invoice_id}, {"$set": update_data})
    updated_invoice = await db.invoices.find_one({"id": invoice_id})
    return Invoice(**updated_invoice)

@api_router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: str, current_user: User = Depends(get_current_user)):
    result = await db.invoices.delete_one({"id": invoice_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {"message": "Invoice deleted"}

# PDF Generation
def generate_invoice_pdf(invoice_data, account_data, contact_data, products_data, user_data):
    """Generate PDF for invoice"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
    styles = getSampleStyleSheet()
    story = []
    
    # Header
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=30
    )
    story.append(Paragraph("INVOICE", header_style))
    
    # Invoice details table
    issue_date = invoice_data['issue_date']
    if isinstance(issue_date, datetime):
        issue_date_str = issue_date.strftime('%Y-%m-%d')
    else:
        issue_date_str = str(issue_date)[:10]
    
    due_date = invoice_data.get('due_date')
    if due_date:
        if isinstance(due_date, datetime):
            due_date_str = due_date.strftime('%Y-%m-%d')
        else:
            due_date_str = str(due_date)[:10]
    else:
        due_date_str = 'On Receipt'
    
    invoice_details = [
        ['Invoice Number:', invoice_data['invoice_number']],
        ['Issue Date:', issue_date_str],
        ['Due Date:', due_date_str],
        ['Status:', invoice_data['status'].title()]
    ]
    
    details_table = Table(invoice_details, colWidths=[2*inch, 3*inch])
    details_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 20))
    
    # Billing information
    billing_data = [
        ['Bill To:', 'From:'],
        [account_data['name'], user_data['name']],
        [account_data.get('address', ''), 'yourocrm.com'],
        [f"VAT: {account_data.get('vat_number', 'N/A')}", '']
    ]
    
    billing_table = Table(billing_data, colWidths=[3*inch, 3*inch])
    billing_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(billing_table)
    story.append(Spacer(1, 30))
    
    # Items table
    items_data = [['Description', 'Quantity', 'Unit Price', 'Total']]
    
    for item in invoice_data['items']:
        # Find product details
        product = next((p for p in products_data if p['id'] == item['product_id']), None)
        description = item.get('description') or (product['name'] if product else 'Product')
        total = item['quantity'] * item['unit_price']
        
        items_data.append([
            description,
            str(item['quantity']),
            f"€{item['unit_price']:.2f}",
            f"€{total:.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 20))
    
    # Totals table
    totals_data = [
        ['Subtotal:', f"€{invoice_data['subtotal']:.2f}"],
        ['VAT (21%):', f"€{invoice_data['tax_amount']:.2f}"],
        ['Total:', f"€{invoice_data['total_amount']:.2f}"]
    ]
    
    totals_table = Table(totals_data, colWidths=[4.5*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
    ]))
    story.append(totals_table)
    
    # Notes
    if invoice_data.get('notes'):
        story.append(Spacer(1, 30))
        story.append(Paragraph("Notes:", styles['Heading3']))
        story.append(Paragraph(invoice_data['notes'], styles['Normal']))
    
    # Footer
    story.append(Spacer(1, 50))
    footer_text = "Thank you for your business! Payment terms: Net 30 days."
    story.append(Paragraph(footer_text, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

@api_router.get("/invoices/{invoice_id}/pdf")
async def generate_invoice_pdf_endpoint(invoice_id: str, current_user: User = Depends(get_current_user)):
    # Get invoice
    invoice = await db.invoices.find_one({"id": invoice_id, "user_id": current_user.id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get related data
    account = await db.accounts.find_one({"id": invoice["account_id"]})
    contact = None
    if invoice.get("contact_id"):
        contact = await db.contacts.find_one({"id": invoice["contact_id"]})
    
    # Get products for invoice items
    product_ids = [item["product_id"] for item in invoice["items"]]
    products = await db.products.find({"id": {"$in": product_ids}}).to_list(100)
    
    # Generate PDF
    pdf_bytes = generate_invoice_pdf(invoice, account, contact, products, current_user.dict())
    
    # Encode as base64 for JSON response
    pdf_base64 = base64.b64encode(pdf_bytes).decode()
    
    return {
        "pdf_data": pdf_base64,
        "filename": f"{invoice['invoice_number']}.pdf"
    }

# Payment packages definition
PAYMENT_PACKAGES = {
    "premium": {
        "amount": 14.99,
        "currency": "EUR",
        "name": "YouroCRM Premium",
        "description": "Full access to all CRM and invoicing features"
    }
}

# Initialize Stripe
stripe_api_key = os.environ.get('STRIPE_API_KEY')
if not stripe_api_key:
    logger.warning("STRIPE_API_KEY not found in environment variables")

# PayPal configuration
paypal_client_id = os.environ.get('PAYPAL_CLIENT_ID')
paypal_client_secret = os.environ.get('PAYPAL_CLIENT_SECRET')
paypal_environment = os.environ.get('PAYPAL_ENVIRONMENT', 'sandbox')

if not paypal_client_id or not paypal_client_secret:
    logger.warning("PayPal credentials not found in environment variables")

# PayPal API URLs
PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com" if paypal_environment == "sandbox" else "https://api-m.paypal.com"

async def get_paypal_access_token():
    """Get PayPal access token"""
    if not paypal_client_id or not paypal_client_secret:
        return None
    
    auth = base64.b64encode(f"{paypal_client_id}:{paypal_client_secret}".encode()).decode()
    
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = "grant_type=client_credentials"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{PAYPAL_API_BASE}/v1/oauth2/token", headers=headers, data=data)
        if response.status_code == 200:
            return response.json()["access_token"]
    return None

# Password hashing utilities
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_session_token() -> str:
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

async def validate_vat_with_vies(vat_number: str) -> VIESResponse:
    """Validate VAT number using VIES and retrieve company information"""
    try:
        # Clean and validate VAT number format
        clean_vat = vat_number.replace(" ", "").replace("-", "").upper()
        
        # Check if it's a valid EU VAT number
        if not vat.is_valid(clean_vat):
            return VIESResponse(valid=False)
        
        # Extract country code and number
        country_code = clean_vat[:2]
        vat_num = clean_vat[2:]
        
        # VIES SOAP request
        soap_request = f"""<?xml version="1.0" encoding="UTF-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
                       xmlns:tns1="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
            <soap:Header>
            </soap:Header>
            <soap:Body>
                <tns1:checkVat>
                    <tns1:countryCode>{country_code}</tns1:countryCode>
                    <tns1:vatNumber>{vat_num}</tns1:vatNumber>
                </tns1:checkVat>
            </soap:Body>
        </soap:Envelope>"""
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'checkVat'
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                'https://ec.europa.eu/taxation_customs/vies/services/checkVatService',
                data=soap_request,
                headers=headers
            )
        
        if response.status_code == 200:
            # Parse SOAP response
            root = ET.fromstring(response.text)
            
            # Find the checkVatResponse element
            ns = {'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                  'tns': 'urn:ec.europa.eu:taxud:vies:services:checkVat:types'}
            
            check_vat_response = root.find('.//tns:checkVatResponse', ns)
            
            if check_vat_response is not None:
                valid_elem = check_vat_response.find('tns:valid', ns)
                name_elem = check_vat_response.find('tns:name', ns)
                address_elem = check_vat_response.find('tns:address', ns)
                date_elem = check_vat_response.find('tns:requestDate', ns)
                
                is_valid = valid_elem.text.lower() == 'true' if valid_elem is not None else False
                company_name = name_elem.text if name_elem is not None and name_elem.text else None
                full_address = address_elem.text if address_elem is not None and address_elem.text else None
                request_date = date_elem.text if date_elem is not None else None
                
                # Parse address into components (basic parsing)
                street, street_nr, box, postal_code, city = parse_vies_address(full_address)
                
                return VIESResponse(
                    valid=is_valid,
                    name=company_name,
                    address=full_address,
                    street=street,
                    street_nr=street_nr,
                    box=box,
                    postal_code=postal_code,
                    city=city,
                    country=get_country_name(country_code),
                    country_code=country_code,
                    request_date=request_date
                )
        
        return VIESResponse(valid=False)
        
    except Exception as e:
        logger.error(f"VIES validation error: {e}")
        return VIESResponse(valid=False)

def parse_vies_address(address: str) -> tuple:
    """Parse VIES address into components"""
    if not address:
        return None, None, None, None, None
    
    # This is a basic parser - you might want to enhance it based on your needs
    lines = address.strip().split('\n')
    
    street = None
    street_nr = None
    box = None
    postal_code = None
    city = None
    
    if len(lines) >= 1:
        # First line usually contains street and number
        first_line = lines[0].strip()
        # Try to extract street number (basic regex)
        import re
        
        # Look for patterns like "123" or "123A" at the end of the line
        match = re.search(r'(.+?)\s+(\d+[A-Za-z]?)$', first_line)
        if match:
            street = match.group(1).strip()
            street_nr = match.group(2).strip()
        else:
            street = first_line
    
    if len(lines) >= 2:
        # Last line usually contains postal code and city
        last_line = lines[-1].strip()
        # Look for postal code pattern (varies by country)
        match = re.search(r'^(\d{4,5})\s+(.+)$', last_line)
        if match:
            postal_code = match.group(1).strip()
            city = match.group(2).strip()
        else:
            city = last_line
    
    # Check for box number in middle lines
    if len(lines) > 2:
        for line in lines[1:-1]:
            if 'box' in line.lower() or 'boîte' in line.lower() or 'bus' in line.lower():
                box_match = re.search(r'(\d+)', line)
                if box_match:
                    box = box_match.group(1)
    
    return street, street_nr, box, postal_code, city

def get_country_name(country_code: str) -> str:
    """Get country name from country code"""
    country_map = {
        'AT': 'Austria', 'BE': 'Belgium', 'BG': 'Bulgaria', 'CY': 'Cyprus',
        'CZ': 'Czech Republic', 'DE': 'Germany', 'DK': 'Denmark', 'EE': 'Estonia',
        'ES': 'Spain', 'FI': 'Finland', 'FR': 'France', 'GR': 'Greece',
        'HR': 'Croatia', 'HU': 'Hungary', 'IE': 'Ireland', 'IT': 'Italy',
        'LT': 'Lithuania', 'LU': 'Luxembourg', 'LV': 'Latvia', 'MT': 'Malta',
        'NL': 'Netherlands', 'PL': 'Poland', 'PT': 'Portugal', 'RO': 'Romania',
        'SE': 'Sweden', 'SI': 'Slovenia', 'SK': 'Slovakia'
    }
    return country_map.get(country_code, country_code)

# Subscription Plans Configuration
SUBSCRIPTION_PLANS = {
    "starter": SubscriptionPlan(
        id="starter",
        name="Starter",
        price=0.0,
        features=[
            "5 contacts maximum",
            "2 comptes maximum", 
            "Facturation basique",
            "Support email"
        ],
        limits={
            "contacts_max": 5,
            "accounts_max": 2,
            "invoices_per_month": 10,
            "custom_fields": False,
            "api_access": False,
            "multi_user": False,
            "vies_integration": False,
            "peppol_invoicing": False,
            "advanced_calendar": False,
            "pdf_export": False,
            "priority_support": False
        }
    ),
    "professional": SubscriptionPlan(
        id="professional",
        name="Professional",
        price=14.99,
        features=[
            "Contacts/comptes illimités",
            "Intégration VIES complète",
            "Facturation Peppol",
            "Calendrier avancé",
            "Export PDF",
            "Support prioritaire",
            "Multi-utilisateur (+5€/utilisateur)"
        ],
        limits={
            "contacts_max": -1,  # -1 = unlimited
            "accounts_max": -1,
            "invoices_per_month": -1,
            "custom_fields": False,
            "api_access": False,
            "multi_user": True,
            "vies_integration": True,
            "peppol_invoicing": True,
            "advanced_calendar": True,
            "pdf_export": True,
            "priority_support": True
        },
        is_popular=True
    ),
    "enterprise": SubscriptionPlan(
        id="enterprise",
        name="Enterprise",
        price=39.99,
        features=[
            "Tout Professional",
            "Champs personnalisés",
            "API Access",
            "White-label",
            "Support dédié",
            "Formation incluse"
        ],
        limits={
            "contacts_max": -1,
            "accounts_max": -1,
            "invoices_per_month": -1,
            "custom_fields": True,
            "api_access": True,
            "multi_user": True,
            "vies_integration": True,
            "peppol_invoicing": True,
            "advanced_calendar": True,
            "pdf_export": True,
            "priority_support": True,
            "white_label": True,
            "dedicated_support": True,
            "training": True
        }
    )
}

def get_user_plan(user: User) -> SubscriptionPlan:
    """Get user's current subscription plan"""
    return SUBSCRIPTION_PLANS.get(user.current_plan, SUBSCRIPTION_PLANS["starter"])

def check_plan_limits(user: User, resource_type: str, current_count: int = 0) -> bool:
    """Check if user can create more resources based on their plan"""
    plan = get_user_plan(user)
    
    if resource_type == "contacts":
        max_allowed = plan.limits.get("contacts_max", 0)
    elif resource_type == "accounts":
        max_allowed = plan.limits.get("accounts_max", 0)
    elif resource_type == "invoices":
        max_allowed = plan.limits.get("invoices_per_month", 0)
    else:
        return True  # Unknown resource type, allow by default
    
    # -1 means unlimited
    if max_allowed == -1:
        return True
    
    return current_count < max_allowed

def has_feature_access(user: User, feature: str) -> bool:
    """Check if user has access to a specific feature"""
    plan = get_user_plan(user)
    return plan.limits.get(feature, False)

# Internationalization Configuration
TRANSLATIONS = {
    "en": {
        # Navigation & Common
        "app_name": "YouroCRM",
        "dashboard": "Dashboard",
        "contacts": "Contacts",
        "accounts": "Accounts",
        "products": "Products",
        "invoices": "Invoices",
        "calendar": "Calendar",
        "admin": "Admin",
        "pricing": "Pricing",
        "logout": "Logout",
        "login": "Login",
        "register": "Register",
        "back_to_home": "Back to home",
        
        # Homepage
        "hero_title": "The European CRM with VIES Integration",
        "hero_subtitle": "Manage your European clients with VIES company data auto-completion, Peppol compliant invoicing, and much more. Designed for European SMBs.",
        "start_free": "🚀 Start for free",
        "view_pricing": "📋 View pricing",
        "why_choose_title": "Why choose YouroCRM?",
        "why_choose_subtitle": "The only CRM with native VIES integration for Europe",
        
        # Features
        "feature_vies_title": "VIES Integration",
        "feature_vies_desc": "Real-time auto-completion of European company data via VAT number",
        "feature_peppol_title": "Peppol Invoicing",
        "feature_peppol_desc": "Electronic invoicing compliant with European and Belgian standards",
        "feature_management_title": "Complete Management",
        "feature_management_desc": "Contacts, accounts, products, invoices and calendar in one platform",
        "feature_security_title": "European Security",
        "feature_security_desc": "GDPR compliance, secure authentication and European hosting",
        "feature_payments_title": "Flexible Payments",
        "feature_payments_desc": "Integrated Stripe and PayPal to facilitate your client transactions",
        "feature_multiplatform_title": "Multi-platform",
        "feature_multiplatform_desc": "Responsive interface accessible on desktop, tablet and mobile",
        
        # Plans
        "pricing_title": "Simple and Transparent Pricing",
        "pricing_subtitle": "Start free, scale as you grow",
        "starter_plan": "🆓 Starter",
        "professional_plan": "💎 Professional",
        "enterprise_plan": "🏆 Enterprise",
        "most_popular": "⭐ Most popular",
        "per_month": "/month",
        "free": "Free",
        "choose_plan": "Choose",
        "start_free_btn": "Start free",
        
        # Plan Features
        "contacts_max": "contacts maximum",
        "accounts_max": "accounts maximum",
        "basic_invoicing": "Basic invoicing",
        "email_support": "Email support",
        "unlimited_contacts_accounts": "Unlimited contacts/accounts",
        "vies_integration_complete": "Complete VIES integration",
        "peppol_invoicing": "Peppol invoicing",
        "advanced_calendar": "Advanced calendar",
        "pdf_export": "PDF export",
        "priority_support": "Priority support",
        "multi_user": "Multi-user (+5€/user)",
        "everything_professional": "Everything Professional",
        "custom_fields": "Custom fields",
        "api_access": "API Access",
        "white_label": "White-label",
        "dedicated_support": "Dedicated support",
        "training_included": "Training included",
        
        # Authentication
        "continue_with_google": "Continue with Google",
        "sign_in_with_email": "Sign in with Email",
        "create_account_here": "Don't have an account? Create one here",
        "email_address": "Email Address",
        "password": "Password",
        "sign_in": "Sign In",
        "signing_in": "Signing in...",
        "back_to_login_options": "Back to login options",
        "create_your_account": "Create Your Account",
        "join_yourocrm": "Join YouroCRM - Professional CRM Platform",
        "full_name": "Full Name",
        "create_account": "Create Account",
        "creating_account": "Creating Account...",
        "already_have_account": "Already have an account? Sign in here",
        "minimum_6_characters": "Minimum 6 characters",
        "view_pricing_features": "💰 View Pricing & Features",
        
        # Plan Selection
        "choose_your_plan": "Choose your YouroCRM plan",
        "start_free_scale": "Start free and scale as you grow",
        "start_free_now": "Start free now",
        "secure_payment": "🔒 Secure payment via Stripe and PayPal",
        "no_commitment": "✅ No commitment",
        "support_included": "📞 Customer support included",
        "gdpr_compliant": "All plans include GDPR compliance and secure European hosting",
        
        # Messages
        "account_created_success": "Account created successfully! Now choose your plan.",
        "ready_to_transform": "Ready to transform your client management?",
        "join_european_companies": "Join European companies that trust YouroCRM",
        "start_now_free": "🚀 Start now - It's free!",
        
        # Limits & Upgrades
        "plan_limit_reached": "plan limit reached",
        "upgrade_to_professional": "Upgrade to Professional",
        "unlimited_contacts": "for unlimited contacts",
        "unlimited_accounts": "for unlimited accounts",
        "vies_not_available": "VIES integration not available in",
        "upgrade_for_vies": "Upgrade to Professional to access EU company data auto-completion",
        
        # Footer
        "european_crm_tagline": "The European CRM with VIES integration for modern SMBs.",
        "product": "Product",
        "features": "Features",
        "integrations": "Integrations",
        "support": "Support",
        "documentation": "Documentation",
        "help_center": "Help Center",
        "contact": "Contact",
        "legal": "Legal",
        "privacy": "Privacy",
        "terms": "Terms",
        "gdpr": "GDPR",
        "all_rights_reserved": "All rights reserved. Designed for Europe 🇪🇺"
    },
    
    "fr": {
        # Navigation & Common
        "app_name": "YouroCRM",
        "dashboard": "Tableau de bord",
        "contacts": "Contacts",
        "accounts": "Comptes",
        "products": "Produits",
        "invoices": "Factures",
        "calendar": "Calendrier",
        "admin": "Admin",
        "pricing": "Tarifs",
        "logout": "Déconnexion",
        "login": "Connexion",
        "register": "S'inscrire",
        "back_to_home": "Retour à l'accueil",
        
        # Homepage
        "hero_title": "Le CRM Européen avec Intégration VIES",
        "hero_subtitle": "Gérez vos clients européens avec l'auto-complétion des données d'entreprise VIES, la facturation Peppol conforme, et bien plus encore. Conçu pour les PME européennes.",
        "start_free": "🚀 Commencer gratuitement",
        "view_pricing": "📋 Voir les tarifs",
        "why_choose_title": "Pourquoi choisir YouroCRM ?",
        "why_choose_subtitle": "Le seul CRM avec intégration VIES native pour l'Europe",
        
        # Features
        "feature_vies_title": "Intégration VIES",
        "feature_vies_desc": "Auto-complétion des données d'entreprise européennes en temps réel via le numéro de TVA",
        "feature_peppol_title": "Facturation Peppol",
        "feature_peppol_desc": "Facturation électronique conforme aux normes européennes et belges",
        "feature_management_title": "Gestion Complète",
        "feature_management_desc": "Contacts, comptes, produits, factures et calendrier en une seule plateforme",
        "feature_security_title": "Sécurité Européenne",
        "feature_security_desc": "Conformité RGPD, authentification sécurisée et hébergement européen",
        "feature_payments_title": "Paiements Flexibles",
        "feature_payments_desc": "Stripe et PayPal intégrés pour faciliter vos transactions clients",
        "feature_multiplatform_title": "Multi-plateforme",
        "feature_multiplatform_desc": "Interface responsive accessible sur desktop, tablette et mobile",
        
        # Plans
        "pricing_title": "Tarifs Simples et Transparents",
        "pricing_subtitle": "Commencez gratuitement, évoluez selon vos besoins",
        "starter_plan": "🆓 Starter",
        "professional_plan": "💎 Professional",
        "enterprise_plan": "🏆 Enterprise",
        "most_popular": "⭐ Plus populaire",
        "per_month": "/mois",
        "free": "Gratuit",
        "choose_plan": "Choisir",
        "start_free_btn": "Commencer",
        
        # Plan Features
        "contacts_max": "contacts maximum",
        "accounts_max": "comptes maximum",
        "basic_invoicing": "Facturation basique",
        "email_support": "Support email",
        "unlimited_contacts_accounts": "Contacts/comptes illimités",
        "vies_integration_complete": "Intégration VIES complète",
        "peppol_invoicing": "Facturation Peppol",
        "advanced_calendar": "Calendrier avancé",
        "pdf_export": "Export PDF",
        "priority_support": "Support prioritaire",
        "multi_user": "Multi-utilisateur (+5€/utilisateur)",
        "everything_professional": "Tout Professional",
        "custom_fields": "Champs personnalisés",
        "api_access": "Accès API",
        "white_label": "White-label",
        "dedicated_support": "Support dédié",
        "training_included": "Formation incluse",
        
        # Authentication
        "continue_with_google": "Continuer avec Google",
        "sign_in_with_email": "Se connecter par Email",
        "create_account_here": "Pas de compte ? Créez-en un ici",
        "email_address": "Adresse Email",
        "password": "Mot de passe",
        "sign_in": "Se connecter",
        "signing_in": "Connexion...",
        "back_to_login_options": "Retour aux options de connexion",
        "create_your_account": "Créer votre compte",
        "join_yourocrm": "Rejoignez YouroCRM - Plateforme CRM Professionnelle",
        "full_name": "Nom complet",
        "create_account": "Créer le compte",
        "creating_account": "Création du compte...",
        "already_have_account": "Déjà un compte ? Connectez-vous ici",
        "minimum_6_characters": "Minimum 6 caractères",
        "view_pricing_features": "💰 Voir Tarifs & Fonctionnalités",
        
        # Plan Selection
        "choose_your_plan": "Choisissez votre plan YouroCRM",
        "start_free_scale": "Commencez gratuitement et évoluez selon vos besoins",
        "start_free_now": "Commencer gratuitement",
        "secure_payment": "🔒 Paiement sécurisé via Stripe et PayPal",
        "no_commitment": "✅ Aucun engagement",
        "support_included": "📞 Support client inclus",
        "gdpr_compliant": "Tous les plans incluent la conformité RGPD et l'hébergement européen sécurisé",
        
        # Messages
        "account_created_success": "Compte créé avec succès ! Choisissez maintenant votre plan.",
        "ready_to_transform": "Prêt à transformer votre gestion client ?",
        "join_european_companies": "Rejoignez les entreprises européennes qui font confiance à YouroCRM",
        "start_now_free": "🚀 Démarrer maintenant - C'est gratuit !",
        
        # Limits & Upgrades
        "plan_limit_reached": "limite du plan atteinte",
        "upgrade_to_professional": "Passez au plan Professional",
        "unlimited_contacts": "pour des contacts illimités",
        "unlimited_accounts": "pour des comptes illimités",
        "vies_not_available": "Intégration VIES non disponible dans le plan",
        "upgrade_for_vies": "Passez au plan Professional pour accéder à l'auto-complétion des données d'entreprise EU",
        
        # Footer
        "european_crm_tagline": "Le CRM européen avec intégration VIES pour les PME modernes.",
        "product": "Produit",
        "features": "Fonctionnalités", 
        "integrations": "Intégrations",
        "support": "Support",
        "documentation": "Documentation",
        "help_center": "Centre d'aide",
        "contact": "Contact",
        "legal": "Légal",
        "privacy": "Confidentialité",
        "terms": "Conditions",
        "gdpr": "RGPD",
        "all_rights_reserved": "Tous droits réservés. Conçu pour l'Europe 🇪🇺"
    },
    
    "nl": {
        # Navigation & Common
        "app_name": "YouroCRM",
        "dashboard": "Dashboard",
        "contacts": "Contacten",
        "accounts": "Accounts",
        "products": "Producten",
        "invoices": "Facturen",
        "calendar": "Kalender",
        "admin": "Admin",
        "pricing": "Prijzen",
        "logout": "Uitloggen",
        "login": "Inloggen",
        "register": "Registreren",
        "back_to_home": "Terug naar home",
        
        # Homepage
        "hero_title": "De Europese CRM met VIES Integratie",
        "hero_subtitle": "Beheer uw Europese klanten met VIES bedrijfsgegevens auto-aanvulling, Peppol conforme facturering, en veel meer. Ontworpen voor Europese KMO's.",
        "start_free": "🚀 Gratis beginnen",
        "view_pricing": "📋 Prijzen bekijken",
        "why_choose_title": "Waarom kiezen voor YouroCRM?",
        "why_choose_subtitle": "De enige CRM met native VIES integratie voor Europa",
        
        # Features
        "feature_vies_title": "VIES Integratie",
        "feature_vies_desc": "Real-time auto-aanvulling van Europese bedrijfsgegevens via BTW-nummer",
        "feature_peppol_title": "Peppol Facturering",
        "feature_peppol_desc": "Elektronische facturering conform Europese en Belgische normen",
        "feature_management_title": "Volledig Beheer",
        "feature_management_desc": "Contacten, accounts, producten, facturen en kalender in één platform",
        "feature_security_title": "Europese Beveiliging",
        "feature_security_desc": "AVG naleving, veilige authenticatie en Europese hosting",
        "feature_payments_title": "Flexibele Betalingen",
        "feature_payments_desc": "Geïntegreerde Stripe en PayPal om uw klanttransacties te vergemakkelijken",
        "feature_multiplatform_title": "Multi-platform",
        "feature_multiplatform_desc": "Responsieve interface toegankelijk op desktop, tablet en mobiel",
        
        # Plans
        "pricing_title": "Eenvoudige en Transparante Prijzen",
        "pricing_subtitle": "Begin gratis, schaal naar behoefte",
        "starter_plan": "🆓 Starter",
        "professional_plan": "💎 Professional",
        "enterprise_plan": "🏆 Enterprise",
        "most_popular": "⭐ Meest populair",
        "per_month": "/maand",
        "free": "Gratis",
        "choose_plan": "Kiezen",
        "start_free_btn": "Gratis starten",
        
        # Plan Features
        "contacts_max": "contacten maximum",
        "accounts_max": "accounts maximum",
        "basic_invoicing": "Basis facturering",
        "email_support": "Email ondersteuning",
        "unlimited_contacts_accounts": "Onbeperkte contacten/accounts",
        "vies_integration_complete": "Volledige VIES integratie",
        "peppol_invoicing": "Peppol facturering",
        "advanced_calendar": "Geavanceerde kalender",
        "pdf_export": "PDF export",
        "priority_support": "Prioriteit ondersteuning",
        "multi_user": "Multi-gebruiker (+5€/gebruiker)",
        "everything_professional": "Alles Professional",
        "custom_fields": "Aangepaste velden",
        "api_access": "API Toegang",
        "white_label": "White-label",
        "dedicated_support": "Toegewijde ondersteuning",
        "training_included": "Training inbegrepen",
        
        # Authentication
        "continue_with_google": "Doorgaan met Google",
        "sign_in_with_email": "Inloggen met Email",
        "create_account_here": "Geen account? Maak er hier een aan",
        "email_address": "Email Adres",
        "password": "Wachtwoord",
        "sign_in": "Inloggen",
        "signing_in": "Inloggen...",
        "back_to_login_options": "Terug naar login opties",
        "create_your_account": "Maak uw account aan",
        "full_name": "Volledige naam",
        "create_account": "Account aanmaken",
        "creating_account": "Account aanmaken...",
        "already_have_account": "Al een account? Log hier in",
        "minimum_6_characters": "Minimum 6 karakters",
        
        # Plan Selection
        "choose_your_plan": "Kies uw YouroCRM plan",
        "start_free_scale": "Begin gratis en schaal naar uw behoeften",
        "start_free_now": "Nu gratis starten",
        "secure_payment": "🔒 Veilige betaling via Stripe en PayPal",
        "no_commitment": "✅ Geen verplichtingen",
        "support_included": "📞 Klantondersteuning inbegrepen",
        "gdpr_compliant": "Alle plannen omvatten AVG naleving en veilige Europese hosting",
        
        # Messages
        "account_created_success": "Account succesvol aangemaakt! Kies nu uw plan.",
        "ready_to_transform": "Klaar om uw klantenbeheer te transformeren?",
        "join_european_companies": "Sluit je aan bij Europese bedrijven die vertrouwen op YouroCRM",
        "start_now_free": "🚀 Nu starten - Het is gratis!",
        
        # Limits & Upgrades
        "plan_limit_reached": "plan limiet bereikt",
        "upgrade_to_professional": "Upgrade naar Professional",
        "unlimited_contacts": "voor onbeperkte contacten",
        "unlimited_accounts": "voor onbeperkte accounts",
        "vies_not_available": "VIES integratie niet beschikbaar in",
        "upgrade_for_vies": "Upgrade naar Professional voor toegang tot EU bedrijfsgegevens auto-aanvulling",
        
        # Footer
        "european_crm_tagline": "De Europese CRM met VIES integratie voor moderne KMO's.",
        "product": "Product",
        "features": "Functies",
        "integrations": "Integraties",
        "support": "Ondersteuning",
        "documentation": "Documentatie",
        "help_center": "Helpcentrum",
        "contact": "Contact",
        "legal": "Juridisch",
        "privacy": "Privacy",
        "terms": "Voorwaarden",
        "gdpr": "AVG",
        "all_rights_reserved": "Alle rechten voorbehouden. Ontworpen voor Europa 🇪🇺"
    }
}

def get_translations(language: str = "en") -> dict:
    """Get translations for specified language"""
    return TRANSLATIONS.get(language, TRANSLATIONS["en"])

# Payment routes
@api_router.post("/payments/checkout/session")
async def create_checkout_session(request: Request, checkout_req: CheckoutRequest, current_user: User = Depends(get_current_user)):
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    # Validate package
    if checkout_req.package_id not in PAYMENT_PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    package = PAYMENT_PACKAGES[checkout_req.package_id]
    
    try:
        # Initialize Stripe checkout
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
        
        # Create checkout session request
        checkout_session_req = CheckoutSessionRequest(
            amount=package["amount"],
            currency=package["currency"],
            success_url=checkout_req.success_url,
            cancel_url=checkout_req.cancel_url,
            metadata={
                "user_id": current_user.id,
                "package_id": checkout_req.package_id,
                **(checkout_req.metadata or {})
            }
        )
        
        # Create checkout session
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_session_req)
        
        # Create payment transaction record
        payment_transaction = PaymentTransaction(
            user_id=current_user.id,
            session_id=session.session_id,
            amount=package["amount"],
            currency=package["currency"],
            package_id=checkout_req.package_id,
            payment_status="pending",
            metadata=checkout_req.metadata
        )
        
        await db.payment_transactions.insert_one(payment_transaction.dict())
        
        return {"url": session.url, "session_id": session.session_id}
    
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@api_router.get("/payments/checkout/status/{session_id}")
async def get_checkout_status(session_id: str, current_user: User = Depends(get_current_user)):
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    try:
        # Find payment transaction
        payment_transaction = await db.payment_transactions.find_one({
            "session_id": session_id,
            "user_id": current_user.id
        })
        
        if not payment_transaction:
            raise HTTPException(status_code=404, detail="Payment transaction not found")
        
        # Get status from Stripe
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        checkout_status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Update payment transaction if status changed
        if checkout_status.payment_status != payment_transaction["payment_status"]:
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "payment_status": checkout_status.payment_status,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # If payment successful, upgrade user to premium
            if checkout_status.payment_status == "paid":
                # Check if user role already exists to prevent duplicate upgrades
                existing_role = await db.user_roles.find_one({
                    "user_id": current_user.id,
                    "role": "premium_user"
                })
                
                if not existing_role:
                    user_role = UserRole(
                        user_id=current_user.id,
                        role="premium_user",
                        granted_by="system"
                    )
                    await db.user_roles.insert_one(user_role.dict())
        
        return {
            "status": checkout_status.status,
            "payment_status": checkout_status.payment_status,
            "amount_total": checkout_status.amount_total,
            "currency": checkout_status.currency
        }
    
    except Exception as e:
        logger.error(f"Error getting checkout status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get checkout status")

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    try:
        body = await request.body()
        stripe_signature = request.headers.get("stripe-signature")
        
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        webhook_response = await stripe_checkout.handle_webhook(body, stripe_signature)
        
        # Process webhook event
        if webhook_response.event_type in ["checkout.session.completed", "payment_intent.succeeded"]:
            # Update payment transaction
            await db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {
                    "$set": {
                        "payment_status": webhook_response.payment_status,
                        "payment_id": webhook_response.event_id,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # If payment successful, ensure user has premium role
            if webhook_response.payment_status == "paid":
                payment_transaction = await db.payment_transactions.find_one({
                    "session_id": webhook_response.session_id
                })
                
                if payment_transaction:
                    existing_role = await db.user_roles.find_one({
                        "user_id": payment_transaction["user_id"],
                        "role": "premium_user"
                    })
                    
                    if not existing_role:
                        user_role = UserRole(
                            user_id=payment_transaction["user_id"],
                            role="premium_user",
                            granted_by="system"
                        )
                        await db.user_roles.insert_one(user_role.dict())
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

# PayPal Payment routes
@api_router.post("/payments/paypal/create-order")
async def create_paypal_order(request: Request, order_req: PayPalOrderRequest, current_user: User = Depends(get_current_user)):
    if not paypal_client_id or not paypal_client_secret:
        raise HTTPException(status_code=500, detail="PayPal payment system not configured")
    
    # Validate package
    if order_req.package_id not in PAYMENT_PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    package = PAYMENT_PACKAGES[order_req.package_id]
    
    try:
        # Get PayPal access token
        access_token = await get_paypal_access_token()
        if not access_token:
            raise HTTPException(status_code=500, detail="Failed to authenticate with PayPal")
        
        # Create PayPal order
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": f"yourocrm_{current_user.id}_{order_req.package_id}",
                "amount": {
                    "currency_code": "EUR",
                    "value": str(package["amount"])
                },
                "description": package["description"]
            }],
            "application_context": {
                "return_url": order_req.return_url,
                "cancel_url": order_req.cancel_url,
                "brand_name": "YouroCRM",
                "landing_page": "BILLING",
                "user_action": "PAY_NOW"
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Prefer": "return=representation"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PAYPAL_API_BASE}/v2/checkout/orders",
                headers=headers,
                json=order_data
            )
        
        if response.status_code == 201:
            order_response = response.json()
            
            # Create payment transaction record
            payment_transaction = PaymentTransaction(
                user_id=current_user.id,
                session_id=order_response["id"],
                amount=package["amount"],
                currency=package["currency"],
                package_id=order_req.package_id,
                payment_status="pending",
                metadata={
                    "payment_method": "paypal",
                    "paypal_order_id": order_response["id"],
                    **(order_req.metadata or {})
                }
            )
            
            await db.payment_transactions.insert_one(payment_transaction.dict())
            
            # Find approval URL
            approval_url = None
            for link in order_response.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
            
            return {
                "order_id": order_response["id"],
                "approval_url": approval_url,
                "status": order_response["status"]
            }
        else:
            logger.error(f"PayPal order creation failed: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Failed to create PayPal order")
    
    except Exception as e:
        logger.error(f"Error creating PayPal order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create PayPal order")

@api_router.post("/payments/paypal/capture-order/{order_id}")
async def capture_paypal_order(order_id: str, current_user: User = Depends(get_current_user)):
    if not paypal_client_id or not paypal_client_secret:
        raise HTTPException(status_code=500, detail="PayPal payment system not configured")
    
    try:
        # Get PayPal access token
        access_token = await get_paypal_access_token()
        if not access_token:
            raise HTTPException(status_code=500, detail="Failed to authenticate with PayPal")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Prefer": "return=representation"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
                headers=headers,
                json={}
            )
        
        if response.status_code == 201:
            order_data = response.json()
            
            # Update payment transaction
            await db.payment_transactions.update_one(
                {"session_id": order_id, "user_id": current_user.id},
                {
                    "$set": {
                        "payment_status": "paid" if order_data["status"] == "COMPLETED" else "pending",
                        "payment_id": order_data["id"],
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            # If payment successful, upgrade user to premium
            if order_data["status"] == "COMPLETED":
                existing_role = await db.user_roles.find_one({
                    "user_id": current_user.id,
                    "role": "premium_user"
                })
                
                if not existing_role:
                    user_role = UserRole(
                        user_id=current_user.id,
                        role="premium_user",
                        granted_by="system"
                    )
                    await db.user_roles.insert_one(user_role.dict())
            
            return {
                "order_id": order_data["id"],
                "status": order_data["status"],
                "payment_status": "paid" if order_data["status"] == "COMPLETED" else "pending"
            }
        else:
            logger.error(f"PayPal capture failed: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Failed to capture PayPal payment")
    
    except Exception as e:
        logger.error(f"Error capturing PayPal order: {e}")
        raise HTTPException(status_code=500, detail="Failed to capture PayPal payment")

@api_router.get("/payments/paypal/order-status/{order_id}")
async def get_paypal_order_status(order_id: str, current_user: User = Depends(get_current_user)):
    if not paypal_client_id or not paypal_client_secret:
        raise HTTPException(status_code=500, detail="PayPal payment system not configured")
    
    try:
        # Check our database first
        payment_transaction = await db.payment_transactions.find_one({
            "session_id": order_id,
            "user_id": current_user.id
        })
        
        if not payment_transaction:
            raise HTTPException(status_code=404, detail="Payment transaction not found")
        
        # Get status from PayPal
        access_token = await get_paypal_access_token()
        if not access_token:
            raise HTTPException(status_code=500, detail="Failed to authenticate with PayPal")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}",
                headers=headers
            )
        
        if response.status_code == 200:
            order_data = response.json()
            
            payment_status = "paid" if order_data["status"] == "COMPLETED" else "pending"
            
            # Update our database if status changed
            if payment_status != payment_transaction["payment_status"]:
                await db.payment_transactions.update_one(
                    {"session_id": order_id},
                    {
                        "$set": {
                            "payment_status": payment_status,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
            
            return {
                "order_id": order_data["id"],
                "status": order_data["status"],
                "payment_status": payment_status,
                "amount": payment_transaction["amount"],
                "currency": payment_transaction["currency"]
            }
        else:
            logger.error(f"PayPal status check failed: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Failed to get PayPal order status")
    
    except Exception as e:
        logger.error(f"Error getting PayPal order status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get PayPal order status")

# Admin routes
@api_router.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_current_user)):
    # Check if user is admin
    user_role = await db.user_roles.find_one({"user_id": current_user.id, "role": "admin"})
    if not user_role:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find({}).to_list(1000)
    
    # Get roles for each user
    for user in users:
        roles = await db.user_roles.find({"user_id": user["id"]}).to_list(10)
        user["roles"] = [role["role"] for role in roles]
        
        # Get payment info
        payments = await db.payment_transactions.find({
            "user_id": user["id"],
            "payment_status": "paid"
        }).to_list(10)
        user["payments_count"] = len(payments)
        user["total_paid"] = sum(p["amount"] for p in payments)
    
    return users

@api_router.post("/admin/users/{user_id}/role")
async def assign_user_role(user_id: str, role_data: dict, current_user: User = Depends(get_current_user)):
    # Check if user is admin
    user_role = await db.user_roles.find_one({"user_id": current_user.id, "role": "admin"})
    if not user_role:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if role already exists
    existing_role = await db.user_roles.find_one({
        "user_id": user_id,
        "role": role_data["role"]
    })
    
    if existing_role:
        raise HTTPException(status_code=400, detail="User already has this role")
    
    # Create new role
    new_role = UserRole(
        user_id=user_id,
        role=role_data["role"],
        granted_by=current_user.id
    )
    
    await db.user_roles.insert_one(new_role.dict())
    
    return {"message": "Role assigned successfully"}

@api_router.delete("/admin/users/{user_id}/role/{role}")
async def remove_user_role(user_id: str, role: str, current_user: User = Depends(get_current_user)):
    # Check if user is admin
    user_role = await db.user_roles.find_one({"user_id": current_user.id, "role": "admin"})
    if not user_role:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.user_roles.delete_one({
        "user_id": user_id,
        "role": role
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return {"message": "Role removed successfully"}

@api_router.get("/admin/custom-fields")
async def get_custom_fields(current_user: User = Depends(get_current_user)):
    # Check if user is admin
    user_role = await db.user_roles.find_one({"user_id": current_user.id, "role": "admin"})
    if not user_role:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    custom_fields = await db.custom_fields.find({}).to_list(1000)
    return [CustomField(**field) for field in custom_fields]

@api_router.post("/admin/custom-fields")
async def create_custom_field(field_data: dict, current_user: User = Depends(get_current_user)):
    # Check if user is admin
    user_role = await db.user_roles.find_one({"user_id": current_user.id, "role": "admin"})
    if not user_role:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    custom_field = CustomField(
        entity_type=field_data["entity_type"],
        field_name=field_data["field_name"],
        field_type=field_data["field_type"],
        field_options=field_data.get("field_options"),
        required=field_data.get("required", False),
        created_by=current_user.id
    )
    
    await db.custom_fields.insert_one(custom_field.dict())
    return custom_field

@api_router.delete("/admin/custom-fields/{field_id}")
async def delete_custom_field(field_id: str, current_user: User = Depends(get_current_user)):
    # Check if user is admin
    user_role = await db.user_roles.find_one({"user_id": current_user.id, "role": "admin"})
    if not user_role:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.custom_fields.delete_one({"id": field_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Custom field not found")
    
    return {"message": "Custom field deleted successfully"}

@api_router.post("/admin/users")
async def create_user(user_data: UserCreate, current_user: User = Depends(get_current_user)):
    # Check if user is admin
    user_role = await db.user_roles.find_one({"user_id": current_user.id, "role": "admin"})
    if not user_role:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hash_password(user_data.password),
        auth_type="traditional"
    )
    
    await db.users.insert_one(user.dict())
    
    # Assign roles if provided
    for role in user_data.roles:
        user_role = UserRole(
            user_id=user.id,
            role=role,
            granted_by=current_user.id
        )
        await db.user_roles.insert_one(user_role.dict())
    
    return {"message": "User created successfully", "user_id": user.id}

@api_router.put("/admin/users/{user_id}/status")
async def toggle_user_status(user_id: str, status_data: dict, current_user: User = Depends(get_current_user)):
    # Check if user is admin
    user_role = await db.user_roles.find_one({"user_id": current_user.id, "role": "admin"})
    if not user_role:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Update user status
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": status_data.get("is_active", True)}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User status updated successfully"}

# Basic dashboard stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    contacts_count = await db.contacts.count_documents({"user_id": current_user.id})
    accounts_count = await db.accounts.count_documents({"user_id": current_user.id})
    products_count = await db.products.count_documents({"user_id": current_user.id})
    events_count = await db.calendar_events.count_documents({"user_id": current_user.id})
    invoices_count = await db.invoices.count_documents({"user_id": current_user.id})
    
    return {
        "contacts": contacts_count,
        "accounts": accounts_count,
        "products": products_count,
        "events": events_count,
        "invoices": invoices_count
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()