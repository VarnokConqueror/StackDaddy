from fastapi import FastAPI, APIRouter, HTTPException, Request, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
from pathlib import Path

# Version for deployment verification
API_VERSION = "2026.01.25.v3"
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
import requests
import stripe
import openai
import sys
import importlib

def _import_local_modules():
    if 'backend.stripe_client' in sys.modules or __name__.startswith('backend.'):
        stripe_mod = importlib.import_module('backend.stripe_client')
        db_mod = importlib.import_module('backend.db')
    else:
        stripe_mod = importlib.import_module('stripe_client')
        db_mod = importlib.import_module('db')
    return stripe_mod, db_mod

_stripe_mod, _db_mod = _import_local_modules()
init_stripe_client = _stripe_mod.init_stripe

init_pool = _db_mod.init_pool
close_pool = _db_mod.close_pool
find_user_by_id = _db_mod.find_user_by_id
find_user_by_email = _db_mod.find_user_by_email
find_user_by_oauth = _db_mod.find_user_by_oauth
insert_user = _db_mod.insert_user
update_user = _db_mod.update_user
count_supplements = _db_mod.count_supplements
insert_supplements = _db_mod.insert_supplements
find_all_supplements = _db_mod.find_all_supplements
find_supplement_by_id = _db_mod.find_supplement_by_id
insert_supplement = _db_mod.insert_supplement
find_promo_by_code = _db_mod.find_promo_by_code
update_promo_uses = _db_mod.update_promo_uses
insert_promo_code = _db_mod.insert_promo_code
find_all_promo_codes = _db_mod.find_all_promo_codes
deactivate_promo_code = _db_mod.deactivate_promo_code
insert_meal = _db_mod.insert_meal
find_meals = _db_mod.find_meals
find_meal_by_id = _db_mod.find_meal_by_id
insert_meal_plan = _db_mod.insert_meal_plan
find_meal_plans_by_user = _db_mod.find_meal_plans_by_user
find_meal_plan_by_id = _db_mod.find_meal_plan_by_id
update_meal_plan = _db_mod.update_meal_plan
delete_meal_plan = _db_mod.delete_meal_plan
delete_shopping_lists_by_meal_plan = _db_mod.delete_shopping_lists_by_meal_plan
insert_shopping_list = _db_mod.insert_shopping_list
find_shopping_lists_by_user = _db_mod.find_shopping_lists_by_user
delete_shopping_list = _db_mod.delete_shopping_list
find_pantry_by_user = _db_mod.find_pantry_by_user
insert_pantry_item = _db_mod.insert_pantry_item
find_pantry_item = _db_mod.find_pantry_item
update_pantry_item = _db_mod.update_pantry_item
delete_pantry_item = _db_mod.delete_pantry_item
insert_user_supplement = _db_mod.insert_user_supplement
find_user_supplements = _db_mod.find_user_supplements
update_user_supplement = _db_mod.update_user_supplement
delete_user_supplement = _db_mod.delete_user_supplement
insert_supplement_log = _db_mod.insert_supplement_log
find_supplement_logs = _db_mod.find_supplement_logs
find_subscription_by_user = _db_mod.find_subscription_by_user
insert_subscription = _db_mod.insert_subscription
update_subscription = _db_mod.update_subscription
insert_payment = _db_mod.insert_payment
find_payments_by_user = _db_mod.find_payments_by_user

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-this')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 720

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    await seed_supplements()
    await init_stripe_client()
    yield
    await close_pool()

app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")

@api_router.get("/version")
async def get_version():
    """Get API version for deployment verification"""
    return {"version": API_VERSION, "google_callback_route": "enabled"}

# Helper function for LLM calls using OpenAI API
async def call_openai(api_key: str, prompt: str, system_message: str = None, model: str = "gpt-4") -> str:
    """Call OpenAI API directly"""
    try:
        client = openai.OpenAI(api_key=api_key)
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        raise

# ============== Models ==============

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    subscription_status: str = "inactive"
    subscription_end_date: Optional[str] = None
    dietary_preferences: List[str] = []
    cooking_methods: List[str] = []
    health_goal: Optional[str] = None
    allergies: List[str] = []
    role: Optional[str] = None
    oauth_provider: Optional[str] = None
    picture_url: Optional[str] = None

class TokenResponse(BaseModel):
    token: str
    user: UserResponse

class MealCreate(BaseModel):
    name: str
    description: Optional[str] = None
    ingredients: List[Dict[str, Any]]
    instructions: List[str]
    cooking_method: str
    prep_time: int
    cook_time: int
    servings: int
    nutrition: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    tags: List[str] = []

class Meal(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: Optional[str] = None
    ingredients: List[Dict[str, Any]]
    instructions: List[str]
    cooking_method: str
    prep_time: int
    cook_time: int
    servings: int
    nutrition: Optional[Dict[str, Any]] = None
    image_url: Optional[str] = None
    tags: List[str] = []
    created_at: str

class MealPlanCreate(BaseModel):
    plan_type: str = "weekly"
    goal: Optional[str] = None
    dietary_preferences: List[str] = []
    cooking_methods: List[str] = []
    generate_with_ai: bool = False
    servings: int = 1
    use_leftovers: bool = True

class RecipeDetail(BaseModel):
    ingredients: List[str] = []
    instructions: str = ""
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    servings: Optional[int] = None

class MealPlanDay(BaseModel):
    day: str
    meals: Dict[str, Optional[str]]
    meal_times: Optional[Dict[str, str]] = {}
    is_leftover: Optional[Dict[str, bool]] = {}
    instructions: Optional[Dict[str, str]] = {}
    recipes: Optional[Dict[str, RecipeDetail]] = {}
    locked: bool = False

class MealPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    plan_type: str
    start_date: str
    end_date: str
    days: List[MealPlanDay]
    dietary_preferences: List[str]
    cooking_methods: List[str]
    servings: int = 1
    created_at: str
    goal: Optional[str] = None

class PantryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    name: str
    quantity: float
    unit: str
    category: str
    low_stock_threshold: Optional[float] = None
    created_at: str
    updated_at: str

class PantryItemCreate(BaseModel):
    name: str
    quantity: float
    unit: str
    category: str
    low_stock_threshold: Optional[float] = None

class ShoppingListItem(BaseModel):
    name: str
    quantity: float
    unit: str
    category: str
    checked: bool = False

class ShoppingList(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    meal_plan_id: str
    items: List[ShoppingListItem]
    created_at: str

class SupplementCreate(BaseModel):
    name: str
    purpose: Optional[str] = None
    typical_dose_min: Optional[float] = None
    typical_dose_max: Optional[float] = None
    dose_unit: Optional[str] = None
    warnings: Optional[str] = None
    interactions: Optional[str] = None

class Supplement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    purpose: Optional[str] = None
    typical_dose_min: Optional[float] = None
    typical_dose_max: Optional[float] = None
    dose_unit: Optional[str] = None
    warnings: Optional[str] = None
    interactions: Optional[str] = None

class UserSupplementCreate(BaseModel):
    supplement_id: str
    custom_dose: float
    dose_unit: str
    frequency: str
    timing: List[str]
    stock_quantity: int
    expiration_date: Optional[str] = None
    reminder_enabled: bool = True

class UserSupplement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    supplement_id: str
    supplement_name: str
    custom_dose: float
    dose_unit: str
    frequency: str
    timing: List[str]
    stock_quantity: int
    expiration_date: Optional[str] = None
    reminder_enabled: bool
    created_at: str

class SupplementLogCreate(BaseModel):
    user_supplement_id: str
    dose_taken: float
    notes: Optional[str] = None

class SupplementLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    user_supplement_id: str
    dose_taken: float
    taken_at: str
    notes: Optional[str] = None

class AIConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    provider: str = "openai"
    model: str = "gpt-5.2"
    api_key: Optional[str] = None

class AIConfigUpdate(BaseModel):
    provider: str
    model: str
    api_key: Optional[str] = None

class CheckoutRequest(BaseModel):
    package_id: str
    origin_url: str

# ============== Helper Functions ==============

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def _normalize_user(user: dict) -> dict:
    if user.get("dietary_preferences") is None:
        user["dietary_preferences"] = []
    if user.get("cooking_methods") is None:
        user["cooking_methods"] = []
    if user.get("allergies") is None:
        user["allergies"] = []
    return user

async def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await find_user_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return _normalize_user(user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============== Seed Data ==============

async def seed_supplements():
    count = await count_supplements()
    if count == 0:
        supplements = [
            {"id": str(uuid.uuid4()), "name": "Vitamin D3", "purpose": "Bone health, immune support", "typical_dose_min": 1000, "typical_dose_max": 5000, "dose_unit": "IU", "warnings": "High doses may cause hypercalcemia", "interactions": "May interact with certain heart medications"},
            {"id": str(uuid.uuid4()), "name": "Omega-3 Fish Oil", "purpose": "Heart health, brain function", "typical_dose_min": 1000, "typical_dose_max": 3000, "dose_unit": "mg", "warnings": "May increase bleeding risk", "interactions": "Blood thinners"},
            {"id": str(uuid.uuid4()), "name": "Magnesium", "purpose": "Muscle function, sleep quality", "typical_dose_min": 200, "typical_dose_max": 400, "dose_unit": "mg", "warnings": "High doses may cause digestive issues", "interactions": "Antibiotics, bisphosphonates"},
            {"id": str(uuid.uuid4()), "name": "Vitamin B12", "purpose": "Energy, nerve function", "typical_dose_min": 500, "typical_dose_max": 2000, "dose_unit": "mcg", "warnings": "Generally safe", "interactions": "Metformin may reduce absorption"},
            {"id": str(uuid.uuid4()), "name": "Probiotics", "purpose": "Digestive health, immune support", "typical_dose_min": 10, "typical_dose_max": 50, "dose_unit": "billion CFU", "warnings": "May cause mild gas initially", "interactions": "Antibiotics"},
            {"id": str(uuid.uuid4()), "name": "Creatine", "purpose": "Muscle strength, exercise performance", "typical_dose_min": 3, "typical_dose_max": 5, "dose_unit": "g", "warnings": "Stay hydrated", "interactions": "Caffeine may reduce effectiveness"},
            {"id": str(uuid.uuid4()), "name": "Zinc", "purpose": "Immune function, wound healing", "typical_dose_min": 8, "typical_dose_max": 40, "dose_unit": "mg", "warnings": "Too much can interfere with copper absorption", "interactions": "Antibiotics, diuretics"},
            {"id": str(uuid.uuid4()), "name": "Vitamin C", "purpose": "Immune support, antioxidant", "typical_dose_min": 500, "typical_dose_max": 2000, "dose_unit": "mg", "warnings": "High doses may cause digestive upset", "interactions": "Generally safe"},
        ]
        await insert_supplements(supplements)

# ============== Auth Routes ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    existing_user = await find_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "name": user_data.name,
        "subscription_status": "inactive",
        "subscription_end_date": None,
        "dietary_preferences": [],
        "cooking_methods": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await insert_user(user_doc)
    
    token = create_access_token({"sub": user_id})
    user_response = UserResponse(
        id=user_id,
        email=user_data.email,
        name=user_data.name,
        subscription_status="inactive"
    )
    
    return TokenResponse(token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await find_user_by_email(credentials.email)
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user["id"]})
    user_response = UserResponse(**_normalize_user(user))
    
    return TokenResponse(token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    return UserResponse(**user)

@api_router.put("/auth/preferences")
async def update_preferences(
    preferences: Dict[str, Any],
    authorization: str = Header(None)
):
    user = await get_current_user(authorization)
    
    update_data = {}
    if "dietary_preferences" in preferences:
        update_data["dietary_preferences"] = preferences["dietary_preferences"]
    if "cooking_methods" in preferences:
        update_data["cooking_methods"] = preferences["cooking_methods"]
    if "health_goal" in preferences:
        update_data["health_goal"] = preferences["health_goal"]
    if "allergies" in preferences:
        update_data["allergies"] = preferences["allergies"]
    
    await update_user(user["id"], update_data)
    
    return {"message": "Preferences updated"}

@api_router.put("/auth/profile-picture")
async def update_profile_picture(
    picture_data: Dict[str, str],
    authorization: str = Header(None)
):
    user = await get_current_user(authorization)
    
    picture_url = picture_data.get("picture_url")
    if not picture_url:
        raise HTTPException(status_code=400, detail="picture_url required")
    
    await update_user(user["id"], {"picture_url": picture_url})
    
    return {"message": "Profile picture updated", "picture_url": picture_url}

# ============== OAuth Routes ==============

class OAuthCodeRequest(BaseModel):
    code: str
    redirect_uri: str

class OAuthCallbackData(BaseModel):
    provider: str
    id_token: Optional[str] = None
    access_token: Optional[str] = None
    user_data: Optional[Dict[str, Any]] = None

async def exchange_google_code(code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
    try:
        client_id = os.environ.get('GOOGLE_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            logging.error("Google OAuth credentials not configured")
            return None
        
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            },
            timeout=10
        )
        
        if token_response.status_code != 200:
            logging.error(f"Google token exchange failed: {token_response.text}")
            return None
        
        tokens = token_response.json()
        access_token = tokens.get("access_token")
        
        userinfo_response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        if userinfo_response.status_code != 200:
            logging.error(f"Google userinfo request failed: {userinfo_response.text}")
            return None
        
        user_info = userinfo_response.json()
        return {
            "id": user_info.get("id"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "access_token": access_token,
            "refresh_token": tokens.get("refresh_token")
        }
    except Exception as e:
        logging.error(f"Google OAuth exchange failed: {e}")
        return None

async def verify_apple_token(id_token: str) -> Optional[Dict[str, Any]]:
    apple_team_id = os.environ.get('APPLE_TEAM_ID')
    if not apple_team_id:
        return None
    return None

async def verify_facebook_token(access_token: str) -> Optional[Dict[str, Any]]:
    facebook_app_id = os.environ.get('FACEBOOK_APP_ID')
    facebook_app_secret = os.environ.get('FACEBOOK_APP_SECRET')
    
    if not facebook_app_id or not facebook_app_secret:
        return None
    
    try:
        verify_response = requests.get(
            "https://graph.facebook.com/debug_token",
            params={
                "input_token": access_token,
                "access_token": f"{facebook_app_id}|{facebook_app_secret}"
            },
            timeout=10
        )
        verify_data = verify_response.json()
        
        if not verify_data.get("data", {}).get("is_valid"):
            return None
        
        user_response = requests.get(
            "https://graph.facebook.com/me",
            params={
                "fields": "id,name,email,picture",
                "access_token": access_token
            },
            timeout=10
        )
        user_data = user_response.json()
        
        if "error" in user_data:
            return None
        
        return {
            "provider_id": user_data["id"],
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "picture": user_data.get("picture", {}).get("data", {}).get("url")
        }
    except Exception as e:
        logging.error(f"Facebook token verification failed: {e}")
        return None

@api_router.get("/auth/google-callback")
async def google_oauth_callback_v2(code: str = None, error: str = None):
    """Redirect handler for Google OAuth"""
    from fastapi.responses import RedirectResponse
    
    if error:
        return RedirectResponse(url=f"/?error={error}")
    
    if not code:
        return RedirectResponse(url="/?error=no_code")
    
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI', 'https://temple.theconquerorscourt.com/api/auth/google-callback')
    user_data = await exchange_google_code(code, redirect_uri)
    
    if not user_data:
        return RedirectResponse(url="/?error=auth_failed")
    
    email = user_data.get("email")
    name = user_data.get("name")
    picture = user_data.get("picture")
    provider_id = user_data.get("id")
    
    existing_user = await find_user_by_oauth("google", provider_id)
    
    if existing_user:
        token = create_access_token({"sub": existing_user["id"]})
        return RedirectResponse(url=f"/?token={token}")
    
    existing_email = await find_user_by_email(email)
    
    if existing_email:
        await update_user(existing_email["id"], {"oauth_provider": "google", "oauth_id": provider_id, "picture_url": picture})
        token = create_access_token({"sub": existing_email["id"]})
        return RedirectResponse(url=f"/?token={token}")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": email,
        "name": name,
        "oauth_provider": "google",
        "oauth_id": provider_id,
        "picture_url": picture,
        "subscription_status": "inactive",
        "subscription_end_date": None,
        "dietary_preferences": [],
        "cooking_methods": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await insert_user(user_doc)
    
    token = create_access_token({"sub": user_id})
    return RedirectResponse(url=f"/?token={token}")

@api_router.get("/auth/google/callback")
async def google_oauth_callback(code: str = None, error: str = None):
    from fastapi.responses import RedirectResponse
    
    if error:
        return RedirectResponse(url=f"/?error={error}")
    
    if not code:
        return RedirectResponse(url="/?error=no_code")
    
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI', 'https://temple.theconquerorscourt.com/api/auth/google/callback')
    user_data = await exchange_google_code(code, redirect_uri)
    
    if not user_data:
        return RedirectResponse(url="/?error=auth_failed")
    
    email = user_data.get("email")
    name = user_data.get("name")
    picture = user_data.get("picture")
    provider_id = user_data.get("id")
    
    existing_user = await find_user_by_oauth("google", provider_id)
    
    if existing_user:
        token = create_access_token({"sub": existing_user["id"]})
        return RedirectResponse(url=f"/?token={token}")
    
    existing_email = await find_user_by_email(email)
    
    if existing_email:
        await update_user(existing_email["id"], {"oauth_provider": "google", "oauth_id": provider_id, "picture_url": picture})
        token = create_access_token({"sub": existing_email["id"]})
        return RedirectResponse(url=f"/?token={token}")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": email,
        "name": name,
        "oauth_provider": "google",
        "oauth_id": provider_id,
        "picture_url": picture,
        "subscription_status": "inactive",
        "subscription_end_date": None,
        "dietary_preferences": [],
        "cooking_methods": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await insert_user(user_doc)
    
    token = create_access_token({"sub": user_id})
    return RedirectResponse(url=f"/?token={token}")

@api_router.post("/auth/oauth/google")
async def google_oauth_exchange(request: OAuthCodeRequest):
    user_data = await exchange_google_code(request.code, request.redirect_uri)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Failed to authenticate with Google")
    
    email = user_data.get("email")
    name = user_data.get("name")
    picture = user_data.get("picture")
    provider_id = user_data.get("id")
    
    existing_user = await find_user_by_oauth("google", provider_id)
    
    if existing_user:
        user_response = UserResponse(**_normalize_user(existing_user))
        token = create_access_token({"sub": existing_user["id"]})
        return {"token": token, "user": user_response}
    
    existing_email = await find_user_by_email(email)
    
    if existing_email:
        await update_user(existing_email["id"], {
            "oauth_provider": "google",
            "oauth_id": provider_id,
            "picture_url": picture
        })
        user_response = UserResponse(**_normalize_user(existing_email))
        token = create_access_token({"sub": existing_email["id"]})
        return {"token": token, "user": user_response}
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": email,
        "name": name,
        "oauth_provider": "google",
        "oauth_id": provider_id,
        "picture_url": picture,
        "subscription_status": "inactive",
        "subscription_end_date": None,
        "dietary_preferences": [],
        "cooking_methods": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await insert_user(user_doc)
    
    user_response = UserResponse(**_normalize_user(user_doc))
    token = create_access_token({"sub": user_id})
    
    return {"token": token, "user": user_response}

@api_router.post("/auth/oauth/callback")
async def oauth_callback(callback_data: OAuthCallbackData):
    provider = callback_data.provider
    
    if provider == "apple":
        if not callback_data.id_token:
            raise HTTPException(status_code=400, detail="Apple ID token required")
        
        verified_data = await verify_apple_token(callback_data.id_token)
        if not verified_data:
            raise HTTPException(status_code=401, detail="Apple Sign-In not configured. Please add Apple credentials.")
    
    elif provider == "facebook":
        if not callback_data.access_token:
            raise HTTPException(status_code=400, detail="Facebook access token required")
        
        verified_data = await verify_facebook_token(callback_data.access_token)
        if not verified_data:
            raise HTTPException(status_code=401, detail="Facebook Login not configured. Please add Facebook credentials.")
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
    
    provider_id = verified_data["provider_id"]
    email = verified_data.get("email")
    name = verified_data.get("name", "User")
    picture = verified_data.get("picture")
    
    existing_user = await find_user_by_oauth(provider, provider_id)
    
    if existing_user:
        user_response = UserResponse(**_normalize_user(existing_user))
        token = create_access_token({"sub": existing_user["id"]})
        return {"token": token, "user": user_response}
    
    if email:
        existing_email = await find_user_by_email(email)
        if existing_email:
            await update_user(existing_email["id"], {
                "oauth_provider": provider,
                "oauth_id": provider_id,
                "picture_url": picture
            })
            user_response = UserResponse(**_normalize_user(existing_email))
            token = create_access_token({"sub": existing_email["id"]})
            return {"token": token, "user": user_response}
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": email or f"{provider}_{provider_id}@conquerorcourt.app",
        "name": name,
        "oauth_provider": provider,
        "oauth_id": provider_id,
        "picture_url": picture,
        "subscription_status": "inactive",
        "subscription_end_date": None,
        "dietary_preferences": [],
        "cooking_methods": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await insert_user(user_doc)
    
    user_response = UserResponse(**_normalize_user(user_doc))
    token = create_access_token({"sub": user_id})
    
    return {"token": token, "user": user_response}

@api_router.get("/auth/oauth/status")
async def get_oauth_status():
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID')
    return {
        "google": bool(google_client_id),
        "google_client_id": google_client_id,
        "apple": bool(os.environ.get('APPLE_TEAM_ID')),
        "facebook": bool(os.environ.get('FACEBOOK_APP_ID') and os.environ.get('FACEBOOK_APP_SECRET'))
    }

# ============== Promo Code Routes ==============

class PromoCodeRedeem(BaseModel):
    code: str

@api_router.post("/promo/redeem")
async def redeem_promo_code(promo_data: PromoCodeRedeem, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    promo = await find_promo_by_code(promo_data.code.upper())
    
    if not promo:
        raise HTTPException(status_code=404, detail="Invalid promo code")
    
    if not promo.get("active", True):
        raise HTTPException(status_code=400, detail="Promo code has been deactivated")
    
    max_uses = promo.get("max_uses", 0)
    current_uses = promo.get("uses", 0)
    if max_uses > 0 and current_uses >= max_uses:
        raise HTTPException(status_code=400, detail="Promo code has reached maximum uses")
    
    lifetime_end = datetime(2099, 12, 31, tzinfo=timezone.utc).isoformat()
    await update_user(user["id"], {
        "subscription_status": "active",
        "subscription_end_date": lifetime_end
    })
    
    await update_promo_uses(promo_data.code.upper(), user["id"])
    
    return {
        "message": "Promo code redeemed! You now have lifetime premium access.",
        "subscription_status": "active",
        "subscription_end_date": lifetime_end
    }

@api_router.post("/admin/promo/create")
async def create_promo_code(
    code: str,
    max_uses: int = 0,
    authorization: str = Header(None)
):
    user = await get_current_user(authorization)
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing = await find_promo_by_code(code.upper())
    if existing:
        raise HTTPException(status_code=400, detail="Promo code already exists")
    
    promo_doc = {
        "id": str(uuid.uuid4()),
        "code": code.upper(),
        "max_uses": max_uses,
        "uses": 0,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await insert_promo_code(promo_doc)
    
    return {
        "message": "Promo code created successfully",
        "code": code.upper(),
        "max_uses": max_uses
    }

@api_router.get("/admin/promo/list")
async def list_promo_codes(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    promos = await find_all_promo_codes()
    return promos

@api_router.delete("/admin/promo/{code}")
async def revoke_promo_code(code: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await deactivate_promo_code(code.upper())
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Promo code not found")
    
    return {"message": "Promo code revoked"}


# ============== Meal Routes ==============

@api_router.post("/meals", response_model=Meal)
async def create_meal(meal_data: MealCreate, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    meal_id = str(uuid.uuid4())
    meal_doc = {
        "id": meal_id,
        "user_id": user["id"],
        **meal_data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await insert_meal(meal_doc)
    return Meal(**meal_doc)

@api_router.get("/meals", response_model=List[Meal])
async def get_meals(
    cooking_method: Optional[str] = None,
    tags: Optional[str] = None,
    authorization: str = Header(None)
):
    await get_current_user(authorization)
    
    tag_list = tags.split(",") if tags else None
    meals = await find_meals(cooking_method, tag_list)
    return [Meal(**meal) for meal in meals]

@api_router.get("/meals/{meal_id}", response_model=Meal)
async def get_meal(meal_id: str, authorization: str = Header(None)):
    await get_current_user(authorization)
    
    meal = await find_meal_by_id(meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    return Meal(**meal)

# ============== Meal Plan Routes ==============

DEFAULT_MEAL_TIMES = {
    "breakfast": "8:00 AM",
    "lunch": "12:30 PM", 
    "dinner": "6:30 PM",
    "snack": "3:00 PM"
}

@api_router.post("/meal-plans", response_model=MealPlan)
async def create_meal_plan(plan_data: MealPlanCreate, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    plan_id = str(uuid.uuid4())
    start_date = datetime.now(timezone.utc)
    
    end_date = start_date + timedelta(days=7)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    plan_days = [
        {
            "day": day, 
            "meals": {"breakfast": None, "lunch": None, "dinner": None, "snack": None}, 
            "meal_times": DEFAULT_MEAL_TIMES.copy(),
            "is_leftover": {"breakfast": False, "lunch": False, "dinner": False, "snack": False},
            "instructions": {}, 
            "recipes": {},
            "locked": False
        }
        for day in days
    ]
    
    dietary_prefs = plan_data.dietary_preferences or user.get("dietary_preferences", [])
    cooking_methods = plan_data.cooking_methods or user.get("cooking_methods", [])
    goal = plan_data.goal or user.get("health_goal")
    servings = plan_data.servings
    use_leftovers = plan_data.use_leftovers
    
    ai_suggestions_raw = None
    
    if plan_data.generate_with_ai:
        ai_config = await find_ai_config(user["id"])
        if ai_config and ai_config.get("api_key"):
            try:
                system_message = "You are an expert nutritionist and meal planner. Create detailed, practical meal plans."
                model = ai_config.get("model", "gpt-5.2")
                
                goal_context = ""
                if goal:
                    goal_map = {
                        "lose_weight": "focused on calorie deficit, high protein, lower carbs for weight loss",
                        "gain_weight": "calorie surplus with nutrient-dense foods for healthy weight gain",
                        "gain_muscle": "high protein (1g per lb bodyweight), balanced carbs and fats for muscle building",
                        "eat_healthy": "balanced nutrition, whole foods, variety of nutrients",
                        "increase_energy": "complex carbs, B vitamins, sustained energy foods",
                        "improve_digestion": "fiber-rich, probiotic foods, gentle on stomach"
                    }
                    goal_context = f"Goal: {goal_map.get(goal, 'balanced nutrition')}\n"
                
                allergies = user.get("allergies", [])
                allergy_context = ""
                if allergies:
                    allergy_context = f"ALLERGIES/RESTRICTIONS: Avoid {', '.join(allergies)}\n"
                
                leftover_context = ""
                if use_leftovers:
                    leftover_context = """IMPORTANT - LEFTOVER STRATEGY:
To minimize ingredients and food waste, plan dinners that make extra portions for the NEXT day's lunch.
Mark these lunches as leftovers by setting "is_leftover": true for that lunch.
For leftover lunches, use the SAME recipe as the previous night's dinner (just reference it, don't duplicate ingredients).
This means: Monday dinner → Tuesday lunch (leftover), Tuesday dinner → Wednesday lunch (leftover), etc.

"""
                
                prompt = f"""Generate a complete 7-day weekly meal plan with DETAILED recipes for {servings} person(s).

{goal_context}{allergy_context}{leftover_context}Dietary preferences: {', '.join(dietary_prefs) if dietary_prefs else 'None'}
Cooking methods available: {', '.join(cooking_methods) if cooking_methods else 'Any'}
Servings per meal: {servings}

For each day (Monday through Sunday), provide:
- Breakfast with FULL recipe
- Lunch (can be leftover from previous dinner - mark with is_leftover: true)
- Dinner with FULL recipe (make extra for next day's lunch if using leftovers)
- Snack (simple)

Each recipe MUST include:
1. A list of ALL ingredients with exact quantities for {servings} serving(s) (e.g., "2 cups spinach", "1 tbsp olive oil")
2. Detailed step-by-step cooking instructions (at least 4-6 steps)
3. Prep time and cook time in minutes
4. Number of servings (should be {servings}, or {servings * 2} for dinners if making leftovers)

Keep meals practical, delicious, and aligned with the goal. Reuse common ingredients across meals to minimize shopping.

Respond ONLY with valid JSON in this exact format:
{{
  "days": [
    {{
      "day": "Monday",
      "breakfast": "Meal name",
      "breakfast_recipe": {{
        "ingredients": ["2 large eggs", "1 cup spinach", "1/4 cup feta cheese", "1 tbsp olive oil", "Salt and pepper to taste"],
        "instructions": "1. Heat olive oil in a non-stick pan over medium heat.\\n2. Add spinach and sauté for 2 minutes until wilted.\\n3. Crack eggs into the pan and scramble with the spinach.\\n4. Cook for 3-4 minutes until eggs are set but still moist.\\n5. Remove from heat, crumble feta cheese on top.\\n6. Season with salt and pepper, serve immediately.",
        "prep_time": 5,
        "cook_time": 10,
        "servings": {servings}
      }},
      "lunch": "Meal name",
      "lunch_is_leftover": false,
      "lunch_recipe": {{
        "ingredients": ["ingredient list"],
        "instructions": "Detailed multi-step instructions",
        "prep_time": 10,
        "cook_time": 15,
        "servings": {servings}
      }},
      "dinner": "Meal name",
      "dinner_recipe": {{
        "ingredients": ["ingredient list - make extra for tomorrow's lunch"],
        "instructions": "Detailed multi-step instructions",
        "prep_time": 15,
        "cook_time": 25,
        "servings": 2
      }},
      "snack": "Snack name"
    }}
  ]
}}"""
                
                response = await call_openai(ai_config["api_key"], prompt, system_message, model)
                ai_suggestions_raw = response
                
                try:
                    import json
                    response_text = response if isinstance(response, str) else str(response)
                    
                    start_idx = response_text.find('{')
                    end_idx = response_text.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = response_text[start_idx:end_idx]
                        ai_data = json.loads(json_str)
                        
                        if "days" in ai_data:
                            for i, ai_day in enumerate(ai_data["days"]):
                                if i < len(plan_days):
                                    plan_days[i]["meals"]["breakfast"] = ai_day.get("breakfast", "")
                                    plan_days[i]["meals"]["lunch"] = ai_day.get("lunch", "")
                                    plan_days[i]["meals"]["dinner"] = ai_day.get("dinner", "")
                                    plan_days[i]["meals"]["snack"] = ai_day.get("snack", "")
                                    
                                    is_leftover = ai_day.get("lunch_is_leftover", False)
                                    plan_days[i]["is_leftover"] = {
                                        "breakfast": False,
                                        "lunch": is_leftover,
                                        "dinner": False,
                                        "snack": False
                                    }
                                    
                                    plan_days[i]["recipes"] = {}
                                    plan_days[i]["instructions"] = {}
                                    
                                    for meal_type in ["breakfast", "lunch", "dinner"]:
                                        recipe_key = f"{meal_type}_recipe"
                                        if recipe_key in ai_day and ai_day[recipe_key]:
                                            recipe = ai_day[recipe_key]
                                            plan_days[i]["recipes"][meal_type] = {
                                                "ingredients": recipe.get("ingredients", []),
                                                "instructions": recipe.get("instructions", ""),
                                                "prep_time": recipe.get("prep_time"),
                                                "cook_time": recipe.get("cook_time"),
                                                "servings": recipe.get("servings")
                                            }
                                            plan_days[i]["instructions"][meal_type] = f"Prep: {recipe.get('prep_time', '?')} min | Cook: {recipe.get('cook_time', '?')} min"
                                    
                                    plan_days[i]["instructions"]["snack"] = ""
                except Exception as parse_error:
                    logging.error(f"Failed to parse AI response: {parse_error}")
                    
            except Exception as e:
                logging.error(f"AI generation error: {e}")
    
    plan_doc = {
        "id": plan_id,
        "user_id": user["id"],
        "plan_type": "weekly",
        "goal": goal,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days": plan_days,
        "dietary_preferences": dietary_prefs,
        "cooking_methods": cooking_methods,
        "servings": servings,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await insert_meal_plan(plan_doc)
    return MealPlan(**plan_doc)

@api_router.get("/meal-plans", response_model=List[MealPlan])
async def get_meal_plans(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    plans = await find_meal_plans_by_user(user["id"])
    return [MealPlan(**plan) for plan in plans]

@api_router.get("/meal-plans/{plan_id}", response_model=MealPlan)
async def get_meal_plan(plan_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    plan = await find_meal_plan_by_id(plan_id, user["id"])
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    return MealPlan(**plan)

@api_router.delete("/meal-plans/{plan_id}")
async def delete_meal_plan_route(plan_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    result = await delete_meal_plan(plan_id, user["id"])
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    await delete_shopping_lists_by_meal_plan(plan_id)
    
    return {"message": "Meal plan deleted"}

@api_router.put("/meal-plans/{plan_id}")
async def update_meal_plan_route(
    plan_id: str,
    updates: Dict[str, Any],
    authorization: str = Header(None)
):
    user = await get_current_user(authorization)
    
    await update_meal_plan(plan_id, user["id"], updates)
    
    return {"message": "Meal plan updated"}

class RegenerateRequest(BaseModel):
    extra_restriction: Optional[str] = None

@api_router.post("/meal-plans/{plan_id}/regenerate", response_model=MealPlan)
async def regenerate_meal_plan(
    plan_id: str,
    regen_data: RegenerateRequest,
    authorization: str = Header(None)
):
    user = await get_current_user(authorization)
    
    plan = await find_meal_plan_by_id(plan_id, user["id"])
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    ai_config = await find_ai_config(user["id"])
    if not ai_config or not ai_config.get("api_key"):
        raise HTTPException(status_code=400, detail="Please configure your AI API key in Profile first")
    
    user_allergies = user.get("allergies", [])
    all_restrictions = list(user_allergies)
    if regen_data.extra_restriction:
        all_restrictions.append(regen_data.extra_restriction)
    
    restrictions_text = ""
    if all_restrictions:
        restrictions_text = f"CRITICAL RESTRICTIONS - NEVER INCLUDE: {', '.join(all_restrictions)}\n"
    
    dietary_prefs = plan.get("dietary_preferences", [])
    cooking_methods = plan.get("cooking_methods", [])
    goal = plan.get("goal", "")
    
    goal_context = ""
    if goal:
        goal_map = {
            "lose_weight": "focused on calorie deficit, high protein, lower carbs for weight loss",
            "gain_weight": "calorie surplus with nutrient-dense foods for healthy weight gain",
            "gain_muscle": "high protein (1g per lb bodyweight), balanced carbs and fats for muscle building",
            "eat_healthy": "balanced nutrition, whole foods, variety of nutrients",
            "increase_energy": "complex carbs, B vitamins, sustained energy foods",
            "improve_digestion": "fiber-rich, probiotic foods, gentle on stomach"
        }
        goal_context = f"Goal: {goal_map.get(goal, 'balanced nutrition')}\n"
    
    try:
        import json
        model = ai_config.get("model", "gpt-5.2")
        
        prompt = f"""Generate a complete 7-day weekly meal plan with DETAILED recipes.

{restrictions_text}{goal_context}Dietary preferences: {', '.join(dietary_prefs) if dietary_prefs else 'None'}
Cooking methods available: {', '.join(cooking_methods) if cooking_methods else 'Any'}

For each day (Monday through Sunday), provide:
- Breakfast with FULL recipe
- Lunch with FULL recipe
- Dinner with FULL recipe
- Snack (simple)

Each recipe MUST include:
1. A list of ALL ingredients with exact quantities (e.g., "2 cups spinach", "1 tbsp olive oil")
2. Detailed step-by-step cooking instructions (at least 4-6 steps)
3. Prep time and cook time in minutes
4. Number of servings

IMPORTANT: DO NOT include any ingredients that contain or are derived from: {', '.join(all_restrictions) if all_restrictions else 'nothing restricted'}

Respond ONLY with valid JSON in this exact format:
{{
  "days": [
    {{
      "day": "Monday",
      "breakfast": "Meal name",
      "breakfast_recipe": {{
        "ingredients": ["2 large eggs", "1 cup spinach", "1/4 cup feta cheese", "1 tbsp olive oil", "Salt and pepper to taste"],
        "instructions": "1. Heat olive oil in a non-stick pan over medium heat.\\n2. Add spinach and sauté for 2 minutes until wilted.\\n3. Crack eggs into the pan and scramble with the spinach.\\n4. Cook for 3-4 minutes until eggs are set but still moist.\\n5. Remove from heat, crumble feta cheese on top.\\n6. Season with salt and pepper, serve immediately.",
        "prep_time": 5,
        "cook_time": 10,
        "servings": 1
      }},
      "lunch": "Meal name",
      "lunch_recipe": {{...}},
      "dinner": "Meal name",
      "dinner_recipe": {{...}},
      "snack": "Snack name"
    }}
  ]
}}"""
        
        response = await call_openai(ai_config["api_key"], prompt, None, model)
        
        response_text = response if isinstance(response, str) else str(response)
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        plan_days = [
            {"day": day, "meals": {"breakfast": None, "lunch": None, "dinner": None, "snack": None}, "instructions": {}, "recipes": {}, "locked": False}
            for day in days
        ]
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            ai_data = json.loads(json_str)
            
            if "days" in ai_data:
                for i, ai_day in enumerate(ai_data["days"]):
                    if i < len(plan_days):
                        plan_days[i]["meals"]["breakfast"] = ai_day.get("breakfast", "")
                        plan_days[i]["meals"]["lunch"] = ai_day.get("lunch", "")
                        plan_days[i]["meals"]["dinner"] = ai_day.get("dinner", "")
                        plan_days[i]["meals"]["snack"] = ai_day.get("snack", "")
                        
                        plan_days[i]["recipes"] = {}
                        plan_days[i]["instructions"] = {}
                        
                        for meal_type in ["breakfast", "lunch", "dinner"]:
                            recipe_key = f"{meal_type}_recipe"
                            if recipe_key in ai_day and ai_day[recipe_key]:
                                recipe = ai_day[recipe_key]
                                plan_days[i]["recipes"][meal_type] = {
                                    "ingredients": recipe.get("ingredients", []),
                                    "instructions": recipe.get("instructions", ""),
                                    "prep_time": recipe.get("prep_time"),
                                    "cook_time": recipe.get("cook_time"),
                                    "servings": recipe.get("servings")
                                }
                                plan_days[i]["instructions"][meal_type] = f"Prep: {recipe.get('prep_time', '?')} min | Cook: {recipe.get('cook_time', '?')} min"
                        
                        plan_days[i]["instructions"]["snack"] = ""
        
        await update_meal_plan(plan_id, user["id"], {"days": plan_days})
        
        updated_plan = await find_meal_plan_by_id(plan_id, user["id"])
        return MealPlan(**updated_plan)
        
    except Exception as e:
        logging.error(f"AI regeneration error: {e}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

# ============== Shopping List Routes ==============

INGREDIENT_CATEGORIES = {
    "chicken": "Proteins", "beef": "Proteins", "pork": "Proteins", "fish": "Proteins",
    "salmon": "Proteins", "tuna": "Proteins", "shrimp": "Proteins", "turkey": "Proteins",
    "egg": "Proteins", "eggs": "Proteins", "tofu": "Proteins", "tempeh": "Proteins",
    "milk": "Dairy", "cheese": "Dairy", "yogurt": "Dairy", "butter": "Dairy",
    "cream": "Dairy", "feta": "Dairy", "parmesan": "Dairy", "mozzarella": "Dairy",
    "spinach": "Produce", "lettuce": "Produce", "tomato": "Produce", "onion": "Produce",
    "garlic": "Produce", "pepper": "Produce", "carrot": "Produce", "broccoli": "Produce",
    "cucumber": "Produce", "avocado": "Produce", "lemon": "Produce", "lime": "Produce",
    "apple": "Produce", "banana": "Produce", "berry": "Produce", "berries": "Produce",
    "mushroom": "Produce", "zucchini": "Produce", "potato": "Produce", "sweet potato": "Produce",
    "rice": "Grains & Bread", "pasta": "Grains & Bread", "bread": "Grains & Bread",
    "oats": "Grains & Bread", "quinoa": "Grains & Bread", "tortilla": "Grains & Bread",
    "oil": "Pantry", "olive oil": "Pantry", "salt": "Pantry",
    "sugar": "Pantry", "flour": "Pantry", "honey": "Pantry", "vinegar": "Pantry",
    "soy sauce": "Pantry", "sauce": "Pantry", "broth": "Pantry", "stock": "Pantry",
    "almond": "Nuts & Seeds", "walnut": "Nuts & Seeds", "peanut": "Nuts & Seeds",
    "cashew": "Nuts & Seeds", "seed": "Nuts & Seeds", "nut": "Nuts & Seeds",
}

def categorize_ingredient(ingredient_name: str) -> str:
    name_lower = ingredient_name.lower()
    for keyword, category in INGREDIENT_CATEGORIES.items():
        if keyword in name_lower:
            return category
    return "Other"

def parse_ingredient_string(ingredient_str: str) -> dict:
    import re
    
    pattern = r'^([\d\/\.\s]+)?\s*(cups?|tbsp|tsp|oz|lb|g|kg|ml|l|bunch|cloves?|pieces?|slices?|cans?|bottles?|packages?|stalks?)?\s*(.+)$'
    match = re.match(pattern, ingredient_str.strip(), re.IGNORECASE)
    
    if match:
        quantity_str = match.group(1) or "1"
        unit = match.group(2) or "unit"
        name = match.group(3) or ingredient_str
        
        try:
            if '/' in quantity_str:
                parts = quantity_str.strip().split()
                total = 0
                for part in parts:
                    if '/' in part:
                        num, denom = part.split('/')
                        total += float(num) / float(denom)
                    else:
                        total += float(part) if part else 0
                quantity = total
            else:
                quantity = float(quantity_str.strip()) if quantity_str.strip() else 1
        except:
            quantity = 1
        
        return {
            "name": name.strip(),
            "quantity": quantity,
            "unit": unit.lower(),
            "category": categorize_ingredient(name)
        }
    
    return {
        "name": ingredient_str.strip(),
        "quantity": 1,
        "unit": "unit",
        "category": categorize_ingredient(ingredient_str)
    }

@api_router.post("/shopping-lists", response_model=ShoppingList)
async def generate_shopping_list(meal_plan_id: str, subtract_pantry: bool = True, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    plan = await find_meal_plan_by_id(meal_plan_id, user["id"])
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    servings = plan.get("servings", 1)
    
    all_ingredients = {}
    
    for day in plan.get("days", []):
        recipes = day.get("recipes", {})
        is_leftover = day.get("is_leftover", {})
        
        for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
            if is_leftover.get(meal_type, False):
                continue
                
            recipe = recipes.get(meal_type, {})
            ingredients_list = recipe.get("ingredients", [])
            
            for ingredient in ingredients_list:
                if isinstance(ingredient, str):
                    parsed = parse_ingredient_string(ingredient)
                elif isinstance(ingredient, dict):
                    parsed = {
                        "name": ingredient.get("name", "Unknown"),
                        "quantity": ingredient.get("quantity", 1),
                        "unit": ingredient.get("unit", "unit"),
                        "category": ingredient.get("category") or categorize_ingredient(ingredient.get("name", ""))
                    }
                else:
                    continue
                
                key = f"{parsed['name'].lower()}_{parsed['unit']}"
                if key in all_ingredients:
                    all_ingredients[key]["quantity"] += parsed["quantity"]
                else:
                    all_ingredients[key] = {
                        "name": parsed["name"],
                        "quantity": parsed["quantity"],
                        "unit": parsed["unit"],
                        "category": parsed["category"],
                        "checked": False,
                        "in_pantry": False,
                        "pantry_has": 0
                    }
    
    if subtract_pantry:
        pantry_items = await find_pantry_by_user(user["id"])
        
        for pantry_item in pantry_items:
            pantry_name = pantry_item["name"].lower()
            pantry_unit = pantry_item["unit"].lower()
            pantry_qty = pantry_item["quantity"]
            
            for key in list(all_ingredients.keys()):
                item = all_ingredients[key]
                item_name = item["name"].lower()
                
                if pantry_name in item_name or item_name in pantry_name:
                    if pantry_unit == item["unit"].lower() or pantry_unit in item["unit"].lower():
                        item["in_pantry"] = True
                        item["pantry_has"] = pantry_qty
                        
                        new_qty = item["quantity"] - pantry_qty
                        if new_qty <= 0:
                            item["quantity"] = 0
                            item["checked"] = True
                        else:
                            item["quantity"] = new_qty
    
    final_items = []
    for key in all_ingredients:
        item = all_ingredients[key]
        qty = item["quantity"]
        if qty > 0:
            if qty == int(qty):
                item["quantity"] = int(qty)
            else:
                item["quantity"] = round(qty, 2)
            final_items.append(item)
        elif item.get("in_pantry"):
            item["quantity"] = 0
            final_items.append(item)
    
    list_id = str(uuid.uuid4())
    list_doc = {
        "id": list_id,
        "user_id": user["id"],
        "meal_plan_id": meal_plan_id,
        "items": final_items,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await insert_shopping_list(list_doc)
    return ShoppingList(**list_doc)

@api_router.get("/shopping-lists", response_model=List[ShoppingList])
async def get_shopping_lists(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    lists = await find_shopping_lists_by_user(user["id"])
    return [ShoppingList(**lst) for lst in lists]

@api_router.delete("/shopping-lists/{list_id}")
async def delete_shopping_list_route(list_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    result = await delete_shopping_list(list_id, user["id"])
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Shopping list not found")
    
    return {"message": "Shopping list deleted"}

# ============== Pantry Routes ==============

PANTRY_CATEGORIES = ["Spices", "Oils & Vinegars", "Grains & Pasta", "Canned Goods", "Condiments", "Baking", "Other"]

@api_router.get("/pantry")
async def get_pantry(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    items = await find_pantry_by_user(user["id"])
    return items

@api_router.post("/pantry")
async def add_pantry_item(item_data: PantryItemCreate, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    item_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    item_doc = {
        "id": item_id,
        "user_id": user["id"],
        "name": item_data.name,
        "quantity": item_data.quantity,
        "unit": item_data.unit,
        "category": item_data.category,
        "low_stock_threshold": item_data.low_stock_threshold,
        "created_at": now,
        "updated_at": now
    }
    
    await insert_pantry_item(item_doc)
    return {"id": item_id, **item_data.model_dump()}

@api_router.put("/pantry/{item_id}")
async def update_pantry_item_route(item_id: str, updates: Dict[str, Any], authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await update_pantry_item(item_id, user["id"], updates)
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Pantry item not found")
    
    return {"message": "Pantry item updated"}

@api_router.delete("/pantry/{item_id}")
async def delete_pantry_item_route(item_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    result = await delete_pantry_item(item_id, user["id"])
    
    if result == 0:
        raise HTTPException(status_code=404, detail="Pantry item not found")
    
    return {"message": "Pantry item deleted"}

@api_router.post("/pantry/use")
async def use_pantry_item(data: Dict[str, Any], authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    item_id = data.get("item_id")
    amount = data.get("amount", 0)
    
    item = await find_pantry_item(item_id, user["id"])
    if not item:
        raise HTTPException(status_code=404, detail="Pantry item not found")
    
    new_quantity = max(0, item["quantity"] - amount)
    
    await update_pantry_item(item_id, user["id"], {"quantity": new_quantity, "updated_at": datetime.now(timezone.utc).isoformat()})
    
    return {"message": "Pantry updated", "new_quantity": new_quantity}

# ============== Supplement Routes ==============

def _normalize_supplement(supp: dict) -> dict:
    benefits = supp.get("benefits") or {}
    warnings = supp.get("warnings") or {}
    return {
        "id": supp.get("id"),
        "name": supp.get("name"),
        "purpose": supp.get("description"),
        "typical_dose_min": benefits.get("typical_dose_min") if isinstance(benefits, dict) else None,
        "typical_dose_max": benefits.get("typical_dose_max") if isinstance(benefits, dict) else None,
        "dose_unit": supp.get("dosage"),
        "warnings": warnings.get("warnings") if isinstance(warnings, dict) else None,
        "interactions": warnings.get("interactions") if isinstance(warnings, dict) else None
    }

@api_router.get("/supplements", response_model=List[Supplement])
async def get_supplements(authorization: str = Header(None)):
    await get_current_user(authorization)
    
    supplements = await find_all_supplements()
    return [Supplement(**_normalize_supplement(supp)) for supp in supplements]

@api_router.post("/supplements", response_model=Supplement)
async def create_supplement(supp_data: SupplementCreate, authorization: str = Header(None)):
    await get_current_user(authorization)
    
    supp_id = str(uuid.uuid4())
    supp_doc = {
        "id": supp_id,
        **supp_data.model_dump()
    }
    
    await insert_supplement(supp_doc)
    return Supplement(**supp_doc)

def _normalize_user_supplement(supp: dict) -> dict:
    return {
        "id": supp.get("id"),
        "user_id": supp.get("user_id"),
        "supplement_id": supp.get("supplement_id"),
        "supplement_name": supp.get("supplement_name", ""),
        "custom_dose": supp.get("dosage") or 0,
        "dose_unit": "unit",
        "frequency": supp.get("frequency") or "",
        "timing": [supp.get("time_of_day")] if supp.get("time_of_day") else [],
        "stock_quantity": 0,
        "expiration_date": supp.get("notes"),
        "reminder_enabled": supp.get("active", True),
        "created_at": supp.get("created_at") or ""
    }

@api_router.post("/user-supplements", response_model=UserSupplement)
async def add_user_supplement(supp_data: UserSupplementCreate, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    supplement = await find_supplement_by_id(supp_data.supplement_id)
    if not supplement:
        raise HTTPException(status_code=404, detail="Supplement not found")
    
    user_supp_id = str(uuid.uuid4())
    user_supp_doc = {
        "id": user_supp_id,
        "user_id": user["id"],
        "supplement_name": supplement["name"],
        **supp_data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await insert_user_supplement(user_supp_doc)
    return UserSupplement(**user_supp_doc)

@api_router.get("/user-supplements", response_model=List[UserSupplement])
async def get_user_supplements(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    supps = await find_user_supplements(user["id"])
    return [UserSupplement(**_normalize_user_supplement(supp)) for supp in supps]

@api_router.put("/user-supplements/{supp_id}")
async def update_user_supplement_route(
    supp_id: str,
    updates: Dict[str, Any],
    authorization: str = Header(None)
):
    user = await get_current_user(authorization)
    
    await update_user_supplement(supp_id, user["id"], updates)
    
    return {"message": "Supplement updated"}

@api_router.delete("/user-supplements/{supp_id}")
async def delete_user_supplement_route(supp_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    await delete_user_supplement(supp_id, user["id"])
    return {"message": "Supplement deleted"}

# ============== Supplement Log Routes ==============

def _normalize_supplement_log(log: dict) -> dict:
    return {
        "id": log.get("id"),
        "user_id": log.get("user_id"),
        "user_supplement_id": log.get("user_supplement_id"),
        "dose_taken": 0,
        "taken_at": log.get("taken_at") or "",
        "notes": log.get("notes")
    }

@api_router.post("/supplement-logs", response_model=SupplementLog)
async def log_supplement(log_data: SupplementLogCreate, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    log_id = str(uuid.uuid4())
    log_doc = {
        "id": log_id,
        "user_id": user["id"],
        **log_data.model_dump(),
        "taken_at": datetime.now(timezone.utc).isoformat()
    }
    
    await insert_supplement_log(log_doc)
    return SupplementLog(**log_doc)

@api_router.get("/supplement-logs", response_model=List[SupplementLog])
async def get_supplement_logs(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    logs = await find_supplement_logs(user["id"])
    return [SupplementLog(**_normalize_supplement_log(log)) for log in logs]

# ============== AI Supplement Recommendations ==============

@api_router.post("/supplements/ai-recommend")
async def ai_recommend_supplements(
    goal: str,
    authorization: str = Header(None)
):
    user = await get_current_user(authorization)
    
    ai_config = await find_ai_config(user["id"])
    if not ai_config or not ai_config.get("api_key"):
        raise HTTPException(status_code=400, detail="AI configuration required. Please add API key in Profile settings.")
    
    all_supplements = await find_all_supplements()
    supp_names = [s["name"] for s in all_supplements]
    
    goal_map = {
        "lose_weight": "weight loss, fat burning, metabolism boost",
        "gain_weight": "healthy weight gain, muscle building, calorie increase",
        "gain_muscle": "muscle growth, strength, recovery, protein synthesis",
        "eat_healthy": "overall health, wellness, nutritional balance",
        "increase_energy": "energy boost, reduce fatigue, vitality",
        "improve_digestion": "digestive health, gut health, nutrient absorption",
        "better_sleep": "sleep quality, relaxation, recovery",
        "reduce_stress": "stress management, mood support, mental clarity",
        "boost_immunity": "immune system support, illness prevention",
        "joint_health": "joint support, flexibility, inflammation reduction"
    }
    
    goal_description = goal_map.get(goal, "general wellness")
    
    try:
        system_message = "You are an expert nutritionist and supplement advisor. Recommend evidence-based supplements."
        model = ai_config.get("model", "gpt-5.2")
        
        prompt = f"""Based on the health goal of "{goal_description}", recommend 5-8 supplements from this list:
{', '.join(supp_names)}

For each recommendation, provide:
1. Supplement name (must match exactly from the list)
2. Why it helps with {goal_description}
3. Suggested daily dose
4. Best time to take it

Format as JSON:
{{
  "recommendations": [
    {{
      "name": "Supplement Name",
      "reason": "Why it helps",
      "suggested_dose": "Amount",
      "timing": "When to take"
    }}
  ]
}}"""
        
        response = await call_openai(ai_config["api_key"], prompt, system_message, model)
        
        return {
            "goal": goal,
            "recommendations": response,
            "available_supplements": supp_names
        }
    except Exception as e:
        logging.error(f"AI supplement recommendation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")

# ============== AI Config Routes ==============

@api_router.get("/ai-config")
async def get_ai_config_route(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    config = await find_ai_config(user["id"])
    if not config:
        config_id = str(uuid.uuid4())
        config_doc = {
            "id": config_id,
            "user_id": user["id"],
            "provider": "openai",
            "model": "gpt-5.2",
            "api_key": None
        }
        await insert_ai_config(config_doc)
        config = config_doc
    
    return config

@api_router.put("/ai-config")
async def update_ai_config_route(config_data: AIConfigUpdate, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    update_data = {
        "provider": config_data.provider,
        "model": config_data.model
    }
    
    if config_data.api_key and config_data.api_key != "********":
        update_data["api_key"] = config_data.api_key
    
    existing = await find_ai_config(user["id"])
    
    if existing:
        await update_ai_config(user["id"], update_data)
    else:
        config_id = str(uuid.uuid4())
        update_data["id"] = config_id
        update_data["user_id"] = user["id"]
        await insert_ai_config(update_data)
    
    return {"message": "AI configuration updated"}

# ============== Subscription Routes ==============

STRIPE_PRICES = {
    "monthly": {
        "amount": 999,
        "interval": "month",
        "name": "Monthly Premium"
    },
    "yearly": {
        "amount": 9999,
        "interval": "year",
        "name": "Yearly Premium"
    }
}

async def get_or_create_stripe_price(package_id: str) -> str:
    package = STRIPE_PRICES.get(package_id)
    if not package:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    cached_price = await find_stripe_price(package_id)
    if cached_price:
        return cached_price["stripe_price_id"]
    
    try:
        product = stripe.Product.create(
            name=f"Conqueror's Court {package['name']}",
            description=f"Premium subscription - {package['name']}"
        )
        
        price = stripe.Price.create(
            product=product.id,
            unit_amount=package["amount"],
            currency="usd",
            recurring={"interval": package["interval"]}
        )
        
        await insert_stripe_price({
            "id": str(uuid.uuid4()),
            "package_id": package_id,
            "price_id": price.id,
            "product_id": product.id,
            "amount": package["amount"],
            "interval": package["interval"]
        })
        
        return price.id
    except stripe.error.StripeError as e:
        logging.error(f"Stripe error creating price: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription price")

@api_router.post("/subscriptions/checkout")
async def create_checkout(checkout_req: CheckoutRequest, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    if checkout_req.package_id not in STRIPE_PRICES:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    try:
        price_id = await get_or_create_stripe_price(checkout_req.package_id)
        
        stripe_customer_id = user.get("stripe_customer_id")
        
        if not stripe_customer_id:
            customer = stripe.Customer.create(
                email=user["email"],
                name=user.get("name", ""),
                metadata={"user_id": user["id"]}
            )
            stripe_customer_id = customer.id
            
            await update_user(user["id"], {"stripe_customer_id": stripe_customer_id})
        
        success_url = f"{checkout_req.origin_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{checkout_req.origin_url}/subscription"
        
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": user["id"],
                "package_id": checkout_req.package_id
            }
        )
        
        transaction_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "session_id": session.id,
            "amount": STRIPE_PRICES[checkout_req.package_id]["amount"] / 100,
            "currency": "usd",
            "package_id": checkout_req.package_id,
            "payment_status": "pending",
            "subscription_mode": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await insert_payment_transaction(transaction_doc)
        
        return {"url": session.url, "session_id": session.id}
        
    except stripe.error.StripeError as e:
        logging.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/subscriptions/status/{session_id}")
async def check_subscription_status(session_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        transaction = await find_payment_transaction(session_id)
        
        if session.status == "complete" and session.payment_status == "paid":
            if transaction and transaction["payment_status"] != "completed":
                subscription = stripe.Subscription.retrieve(session.subscription)
                
                await update_user(user["id"], {
                    "subscription_status": "active",
                    "subscription_end_date": datetime.fromtimestamp(
                        subscription.current_period_end, tz=timezone.utc
                    ).isoformat()
                })
                
                await update_payment_transaction(session_id, {
                    "payment_status": "completed"
                })
        
        return {
            "status": session.status,
            "payment_status": session.payment_status,
            "amount": session.amount_total,
            "currency": session.currency
        }
        
    except stripe.error.StripeError as e:
        logging.error(f"Stripe status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/subscriptions/cancel")
async def cancel_subscription(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    subscription_id = user.get("subscription_id")
    if not subscription_id:
        raise HTTPException(status_code=400, detail="No active subscription found")
    
    try:
        subscription = stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True
        )
        
        await update_user(user["id"], {"subscription_cancel_at_period_end": True})
        
        return {
            "message": "Subscription will be cancelled at the end of the billing period",
            "cancel_at": datetime.fromtimestamp(subscription.current_period_end, tz=timezone.utc).isoformat()
        }
        
    except stripe.error.StripeError as e:
        logging.error(f"Stripe cancel error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/subscriptions/details")
async def get_subscription_details(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    subscription_id = user.get("subscription_id")
    if not subscription_id:
        return {
            "status": "inactive",
            "message": "No active subscription"
        }
    
    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        return {
            "status": subscription.status,
            "current_period_end": datetime.fromtimestamp(
                subscription.current_period_end, tz=timezone.utc
            ).isoformat(),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "plan": subscription.items.data[0].price.recurring.interval if subscription.items.data else None
        }
        
    except stripe.error.StripeError as e:
        logging.error(f"Stripe details error: {e}")
        return {
            "status": "error",
            "message": "Could not fetch subscription details"
        }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    import json
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(body, signature, webhook_secret)
        else:
            event = stripe.Event.construct_from(json.loads(body), stripe.api_key)
        
        event_type = event.type
        data = event.data.object
        
        logging.info(f"Stripe webhook received: {event_type}")
        
        if event_type == "checkout.session.completed":
            user_id = data.metadata.get("user_id")
            if user_id and data.subscription:
                subscription = stripe.Subscription.retrieve(data.subscription)
                await update_user(user_id, {
                    "subscription_status": "active",
                    "subscription_end_date": datetime.fromtimestamp(
                        subscription.current_period_end, tz=timezone.utc
                    ).isoformat()
                })
        
        elif event_type == "invoice.paid":
            subscription_id = data.subscription
            if subscription_id:
                subscription = stripe.Subscription.retrieve(subscription_id)
                customer = stripe.Customer.retrieve(data.customer)
                user_id = customer.metadata.get("user_id")
                
                if user_id:
                    await update_user(user_id, {
                        "subscription_status": "active",
                        "subscription_end_date": datetime.fromtimestamp(
                            subscription.current_period_end, tz=timezone.utc
                        ).isoformat()
                    })
        
        elif event_type == "invoice.payment_failed":
            subscription_id = data.subscription
            if subscription_id:
                customer = stripe.Customer.retrieve(data.customer)
                user_id = customer.metadata.get("user_id")
                
                if user_id:
                    await update_user(user_id, {"subscription_status": "past_due"})
        
        elif event_type == "customer.subscription.deleted":
            customer = stripe.Customer.retrieve(data.customer)
            user_id = customer.metadata.get("user_id")
            
            if user_id:
                await update_user(user_id, {
                    "subscription_status": "inactive",
                    "subscription_end_date": None
                })
        
        return {"status": "success"}
        
    except stripe.error.SignatureVerificationError as e:
        logging.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ============== Root Routes ==============

@api_router.get("/")
async def root():
    return {"message": "Conqueror's Court API"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

FRONTEND_BUILD_DIR = Path(__file__).parent.parent / "frontend" / "build"

if FRONTEND_BUILD_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_BUILD_DIR / "static"), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_path = FRONTEND_BUILD_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_BUILD_DIR / "index.html")
