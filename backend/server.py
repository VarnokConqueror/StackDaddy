from fastapi import FastAPI, APIRouter, HTTPException, Request, Header
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
import jwt
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
from emergentintegrations.llm.chat import LlmChat, UserMessage
import requests

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-this')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 720

app = FastAPI()
api_router = APIRouter(prefix="/api")

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
    goal: Optional[str] = None  # lose_weight, gain_weight, gain_muscle, eat_healthy, etc.
    dietary_preferences: List[str] = []
    cooking_methods: List[str] = []
    generate_with_ai: bool = False

class MealPlanDay(BaseModel):
    day: str
    meals: Dict[str, Optional[str]]
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
    created_at: str

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

async def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============== Seed Data ==============

async def seed_supplements():
    count = await db.supplements.count_documents({})
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
        await db.supplements.insert_many(supplements)

# ============== Auth Routes ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
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
    
    await db.users.insert_one(user_doc)
    
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
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user["id"]})
    user_response = UserResponse(**user)
    
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
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": update_data}
    )
    
    return {"message": "Preferences updated"}

# ============== OAuth Routes ==============

class OAuthSessionRequest(BaseModel):
    session_id: str

class OAuthCallbackData(BaseModel):
    provider: str
    id_token: Optional[str] = None
    access_token: Optional[str] = None
    user_data: Optional[Dict[str, Any]] = None

async def verify_emergent_google_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Verify Google OAuth session via Emergent"""
    try:
        response = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logging.error(f"Emergent Google session verification failed: {e}")
        return None

async def verify_apple_token(id_token: str) -> Optional[Dict[str, Any]]:
    """Verify Apple ID token - Phase 2"""
    # Placeholder for Apple Sign-In verification
    # Will be implemented when Apple credentials are provided
    apple_team_id = os.environ.get('APPLE_TEAM_ID')
    if not apple_team_id:
        return None
    # TODO: Implement Apple token verification with apple-signin-auth library
    return None

async def verify_facebook_token(access_token: str) -> Optional[Dict[str, Any]]:
    """Verify Facebook access token - Phase 2"""
    # Placeholder for Facebook token verification
    # Will be implemented when Facebook credentials are provided
    facebook_app_id = os.environ.get('FACEBOOK_APP_ID')
    facebook_app_secret = os.environ.get('FACEBOOK_APP_SECRET')
    
    if not facebook_app_id or not facebook_app_secret:
        return None
    
    try:
        # Verify token
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
        
        # Get user info
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

@api_router.post("/auth/oauth/google")
async def google_oauth_session(request: OAuthSessionRequest):
    """Handle Emergent Google OAuth session exchange"""
    session_data = await verify_emergent_google_session(request.session_id)
    
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    session_token = session_data.get("session_token")
    email = session_data.get("email")
    name = session_data.get("name")
    picture = session_data.get("picture")
    provider_id = session_data.get("id")
    
    # Check if user exists with this OAuth provider
    existing_user = await db.users.find_one({
        "oauth_provider": "google",
        "oauth_id": provider_id
    }, {"_id": 0})
    
    if existing_user:
        # Update session token
        await db.user_sessions.update_one(
            {"user_id": existing_user["id"]},
            {
                "$set": {
                    "session_token": session_token,
                    "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
        
        user_response = UserResponse(**existing_user)
        token = create_access_token({"sub": existing_user["id"]})
        
        return {
            "token": token,
            "session_token": session_token,
            "user": user_response
        }
    
    # Check if email exists (account linking)
    existing_email = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_email:
        # Link OAuth to existing account
        await db.users.update_one(
            {"id": existing_email["id"]},
            {
                "$set": {
                    "oauth_provider": "google",
                    "oauth_id": provider_id,
                    "picture_url": picture
                }
            }
        )
        
        await db.user_sessions.update_one(
            {"user_id": existing_email["id"]},
            {
                "$set": {
                    "session_token": session_token,
                    "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
        
        user_response = UserResponse(**existing_email)
        token = create_access_token({"sub": existing_email["id"]})
        
        return {
            "token": token,
            "session_token": session_token,
            "user": user_response
        }
    
    # Create new user
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
    
    await db.users.insert_one(user_doc)
    
    # Create session
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    user_response = UserResponse(**user_doc)
    token = create_access_token({"sub": user_id})
    
    return {
        "token": token,
        "session_token": session_token,
        "user": user_response
    }

@api_router.post("/auth/oauth/callback")
async def oauth_callback(callback_data: OAuthCallbackData):
    """Unified OAuth callback handler for Apple and Facebook - Phase 2"""
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
    
    # Create or link user (similar to Google flow)
    provider_id = verified_data["provider_id"]
    email = verified_data.get("email")
    name = verified_data.get("name", "User")
    picture = verified_data.get("picture")
    
    existing_user = await db.users.find_one({
        "oauth_provider": provider,
        "oauth_id": provider_id
    }, {"_id": 0})
    
    if existing_user:
        user_response = UserResponse(**existing_user)
        token = create_access_token({"sub": existing_user["id"]})
        return {"token": token, "user": user_response}
    
    # Check email for account linking
    if email:
        existing_email = await db.users.find_one({"email": email}, {"_id": 0})
        if existing_email:
            await db.users.update_one(
                {"id": existing_email["id"]},
                {
                    "$set": {
                        "oauth_provider": provider,
                        "oauth_id": provider_id,
                        "picture_url": picture
                    }
                }
            )
            user_response = UserResponse(**existing_email)
            token = create_access_token({"sub": existing_email["id"]})
            return {"token": token, "user": user_response}
    
    # Create new user
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
    
    await db.users.insert_one(user_doc)
    
    user_response = UserResponse(**user_doc)
    token = create_access_token({"sub": user_id})
    
    return {"token": token, "user": user_response}

@api_router.get("/auth/oauth/status")
async def get_oauth_status():
    """Check which OAuth providers are configured"""
    return {
        "google": True,  # Always available via Emergent
        "apple": bool(os.environ.get('APPLE_TEAM_ID')),
        "facebook": bool(os.environ.get('FACEBOOK_APP_ID') and os.environ.get('FACEBOOK_APP_SECRET'))
    }

# ============== Promo Code Routes ==============

class PromoCodeRedeem(BaseModel):
    code: str

@api_router.post("/promo/redeem")
async def redeem_promo_code(promo_data: PromoCodeRedeem, authorization: str = Header(None)):
    """Redeem a promo code for lifetime premium access"""
    user = await get_current_user(authorization)
    
    # Check if promo code exists and is valid
    promo = await db.promo_codes.find_one({"code": promo_data.code.upper()}, {"_id": 0})
    
    if not promo:
        raise HTTPException(status_code=404, detail="Invalid promo code")
    
    if not promo.get("active", True):
        raise HTTPException(status_code=400, detail="Promo code has been deactivated")
    
    # Check if already used by this user
    if user["id"] in promo.get("used_by", []):
        raise HTTPException(status_code=400, detail="You've already used this promo code")
    
    # Check usage limit
    max_uses = promo.get("max_uses", 0)
    current_uses = len(promo.get("used_by", []))
    if max_uses > 0 and current_uses >= max_uses:
        raise HTTPException(status_code=400, detail="Promo code has reached maximum uses")
    
    # Grant lifetime premium
    lifetime_end = datetime(2099, 12, 31, tzinfo=timezone.utc).isoformat()
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "subscription_status": "active",
            "subscription_end_date": lifetime_end,
            "promo_code_used": promo_data.code.upper()
        }}
    )
    
    # Mark promo code as used
    await db.promo_codes.update_one(
        {"code": promo_data.code.upper()},
        {
            "$push": {"used_by": user["id"]},
            "$inc": {"use_count": 1}
        }
    )
    
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
    """Create a new promo code (admin only)"""
    user = await get_current_user(authorization)
    
    # Check if user is admin
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if code already exists
    existing = await db.promo_codes.find_one({"code": code.upper()}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Promo code already exists")
    
    promo_doc = {
        "code": code.upper(),
        "max_uses": max_uses,  # 0 = unlimited
        "use_count": 0,
        "used_by": [],
        "active": True,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.promo_codes.insert_one(promo_doc)
    
    return {
        "message": "Promo code created successfully",
        "code": code.upper(),
        "max_uses": max_uses
    }

@api_router.get("/admin/promo/list")
async def list_promo_codes(authorization: str = Header(None)):
    """List all promo codes (admin only)"""
    user = await get_current_user(authorization)
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    promos = await db.promo_codes.find({}, {"_id": 0}).to_list(1000)
    return promos


# ============== Meal Routes ==============

@api_router.post("/meals", response_model=Meal)
async def create_meal(meal_data: MealCreate, authorization: str = Header(None)):
    await get_current_user(authorization)
    
    meal_id = str(uuid.uuid4())
    meal_doc = {
        "id": meal_id,
        **meal_data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.meals.insert_one(meal_doc)
    return Meal(**meal_doc)

@api_router.get("/meals", response_model=List[Meal])
async def get_meals(
    cooking_method: Optional[str] = None,
    tags: Optional[str] = None,
    authorization: str = Header(None)
):
    await get_current_user(authorization)
    
    query = {}
    if cooking_method:
        query["cooking_method"] = cooking_method
    if tags:
        tag_list = tags.split(",")
        query["tags"] = {"$in": tag_list}
    
    meals = await db.meals.find(query, {"_id": 0}).to_list(1000)
    return [Meal(**meal) for meal in meals]

@api_router.get("/meals/{meal_id}", response_model=Meal)
async def get_meal(meal_id: str, authorization: str = Header(None)):
    await get_current_user(authorization)
    
    meal = await db.meals.find_one({"id": meal_id}, {"_id": 0})
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    return Meal(**meal)

# ============== Meal Plan Routes ==============

@api_router.post("/meal-plans", response_model=MealPlan)
async def create_meal_plan(plan_data: MealPlanCreate, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    plan_id = str(uuid.uuid4())
    start_date = datetime.now(timezone.utc)
    
    if plan_data.plan_type == "weekly":
        end_date = start_date + timedelta(days=7)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    else:
        end_date = start_date + timedelta(days=30)
        days = [f"Day {i+1}" for i in range(30)]
    
    plan_days = [
        {"day": day, "meals": {"breakfast": None, "lunch": None, "dinner": None, "snack": None}, "locked": False}
        for day in days
    ]
    
    plan_doc = {
        "id": plan_id,
        "user_id": user["id"],
        "plan_type": plan_data.plan_type,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days": plan_days,
        "dietary_preferences": plan_data.dietary_preferences or user.get("dietary_preferences", []),
        "cooking_methods": plan_data.cooking_methods or user.get("cooking_methods", []),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    if plan_data.generate_with_ai:
        ai_config = await db.ai_configs.find_one({"user_id": user["id"]}, {"_id": 0})
        if ai_config and ai_config.get("api_key"):
            try:
                chat = LlmChat(
                    api_key=ai_config["api_key"],
                    session_id=f"meal_plan_{plan_id}",
                    system_message="You are a professional meal planning assistant. Generate meal suggestions based on dietary preferences and cooking methods."
                ).with_model(ai_config.get("provider", "openai"), ai_config.get("model", "gpt-5.2"))
                
                prompt = f"""Generate a {plan_data.plan_type} meal plan with these preferences:
Dietary: {', '.join(plan_data.dietary_preferences or user.get('dietary_preferences', []))}
Cooking methods: {', '.join(plan_data.cooking_methods or user.get('cooking_methods', []))}

Return JSON with meal suggestions for each day. Format:
{{"suggestions": [{{"day": "Monday", "breakfast": "...", "lunch": "...", "dinner": "...", "snack": "..."}}]}}"""
                
                response = await chat.send_message(UserMessage(text=prompt))
                plan_doc["ai_suggestions"] = response
            except Exception as e:
                logging.error(f"AI generation error: {e}")
    
    await db.meal_plans.insert_one(plan_doc)
    return MealPlan(**plan_doc)

@api_router.get("/meal-plans", response_model=List[MealPlan])
async def get_meal_plans(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    plans = await db.meal_plans.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    return [MealPlan(**plan) for plan in plans]

@api_router.get("/meal-plans/{plan_id}", response_model=MealPlan)
async def get_meal_plan(plan_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    plan = await db.meal_plans.find_one({"id": plan_id, "user_id": user["id"]}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    return MealPlan(**plan)

@api_router.put("/meal-plans/{plan_id}")
async def update_meal_plan(
    plan_id: str,
    updates: Dict[str, Any],
    authorization: str = Header(None)
):
    user = await get_current_user(authorization)
    
    await db.meal_plans.update_one(
        {"id": plan_id, "user_id": user["id"]},
        {"$set": updates}
    )
    
    return {"message": "Meal plan updated"}

# ============== Shopping List Routes ==============

@api_router.post("/shopping-lists", response_model=ShoppingList)
async def generate_shopping_list(meal_plan_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    plan = await db.meal_plans.find_one({"id": meal_plan_id, "user_id": user["id"]}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Meal plan not found")
    
    all_ingredients = {}
    
    for day in plan["days"]:
        for meal_type, meal_id in day["meals"].items():
            if meal_id:
                meal = await db.meals.find_one({"id": meal_id}, {"_id": 0})
                if meal:
                    for ingredient in meal.get("ingredients", []):
                        name = ingredient["name"]
                        quantity = ingredient.get("quantity", 1)
                        unit = ingredient.get("unit", "unit")
                        category = ingredient.get("category", "other")
                        
                        key = f"{name}_{unit}_{category}"
                        if key in all_ingredients:
                            all_ingredients[key]["quantity"] += quantity
                        else:
                            all_ingredients[key] = {
                                "name": name,
                                "quantity": quantity,
                                "unit": unit,
                                "category": category,
                                "checked": False
                            }
    
    list_id = str(uuid.uuid4())
    list_doc = {
        "id": list_id,
        "user_id": user["id"],
        "meal_plan_id": meal_plan_id,
        "items": list(all_ingredients.values()),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.shopping_lists.insert_one(list_doc)
    return ShoppingList(**list_doc)

@api_router.get("/shopping-lists", response_model=List[ShoppingList])
async def get_shopping_lists(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    lists = await db.shopping_lists.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    return [ShoppingList(**lst) for lst in lists]

# ============== Supplement Routes ==============

@api_router.get("/supplements", response_model=List[Supplement])
async def get_supplements(authorization: str = Header(None)):
    await get_current_user(authorization)
    
    supplements = await db.supplements.find({}, {"_id": 0}).to_list(1000)
    return [Supplement(**supp) for supp in supplements]

@api_router.post("/supplements", response_model=Supplement)
async def create_supplement(supp_data: SupplementCreate, authorization: str = Header(None)):
    await get_current_user(authorization)
    
    supp_id = str(uuid.uuid4())
    supp_doc = {
        "id": supp_id,
        **supp_data.model_dump()
    }
    
    await db.supplements.insert_one(supp_doc)
    return Supplement(**supp_doc)

@api_router.post("/user-supplements", response_model=UserSupplement)
async def add_user_supplement(supp_data: UserSupplementCreate, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    supplement = await db.supplements.find_one({"id": supp_data.supplement_id}, {"_id": 0})
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
    
    await db.user_supplements.insert_one(user_supp_doc)
    return UserSupplement(**user_supp_doc)

@api_router.get("/user-supplements", response_model=List[UserSupplement])
async def get_user_supplements(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    supps = await db.user_supplements.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    return [UserSupplement(**supp) for supp in supps]

@api_router.put("/user-supplements/{supp_id}")
async def update_user_supplement(
    supp_id: str,
    updates: Dict[str, Any],
    authorization: str = Header(None)
):
    user = await get_current_user(authorization)
    
    await db.user_supplements.update_one(
        {"id": supp_id, "user_id": user["id"]},
        {"$set": updates}
    )
    
    return {"message": "Supplement updated"}

@api_router.delete("/user-supplements/{supp_id}")
async def delete_user_supplement(supp_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    await db.user_supplements.delete_one({"id": supp_id, "user_id": user["id"]})
    return {"message": "Supplement deleted"}

# ============== Supplement Log Routes ==============

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
    
    await db.supplement_logs.insert_one(log_doc)
    return SupplementLog(**log_doc)

@api_router.get("/supplement-logs", response_model=List[SupplementLog])
async def get_supplement_logs(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    logs = await db.supplement_logs.find({"user_id": user["id"]}, {"_id": 0}).sort("taken_at", -1).to_list(1000)
    return [SupplementLog(**log) for log in logs]

# ============== AI Config Routes ==============

@api_router.get("/ai-config")
async def get_ai_config(authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    config = await db.ai_configs.find_one({"user_id": user["id"]}, {"_id": 0})
    if not config:
        config_id = str(uuid.uuid4())
        config_doc = {
            "id": config_id,
            "user_id": user["id"],
            "provider": "openai",
            "model": "gpt-5.2",
            "api_key": None
        }
        await db.ai_configs.insert_one(config_doc)
        # Return without _id
        config = {
            "id": config_id,
            "user_id": user["id"],
            "provider": "openai",
            "model": "gpt-5.2",
            "api_key": None
        }
    
    return config

@api_router.put("/ai-config")
async def update_ai_config(config_data: AIConfigUpdate, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    await db.ai_configs.update_one(
        {"user_id": user["id"]},
        {"$set": config_data.model_dump()},
        upsert=True
    )
    
    return {"message": "AI configuration updated"}

# ============== Subscription Routes ==============

SUBSCRIPTION_PACKAGES = {
    "monthly": 9.99,
    "yearly": 99.99
}

@api_router.post("/subscriptions/checkout")
async def create_checkout(checkout_req: CheckoutRequest, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    if checkout_req.package_id not in SUBSCRIPTION_PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid package")
    
    amount = SUBSCRIPTION_PACKAGES[checkout_req.package_id]
    
    success_url = f"{checkout_req.origin_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{checkout_req.origin_url}/subscription"
    
    stripe_api_key = os.environ.get('STRIPE_API_KEY')
    webhook_url = f"{checkout_req.origin_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    request_data = CheckoutSessionRequest(
        amount=amount,
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": user["id"],
            "package_id": checkout_req.package_id,
            "email": user["email"]
        }
    )
    
    session = await stripe_checkout.create_checkout_session(request_data)
    
    transaction_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "session_id": session.session_id,
        "amount": amount,
        "currency": "usd",
        "package_id": checkout_req.package_id,
        "payment_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction_doc)
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/subscriptions/status/{session_id}")
async def check_subscription_status(session_id: str, authorization: str = Header(None)):
    user = await get_current_user(authorization)
    
    stripe_api_key = os.environ.get('STRIPE_API_KEY')
    webhook_url = f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    
    if status.payment_status == "paid" and transaction and transaction["payment_status"] != "completed":
        days_to_add = 30 if transaction["package_id"] == "monthly" else 365
        end_date = datetime.now(timezone.utc) + timedelta(days=days_to_add)
        
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {
                "subscription_status": "active",
                "subscription_end_date": end_date.isoformat()
            }}
        )
        
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "completed"}}
        )
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount": status.amount_total,
        "currency": status.currency
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    stripe_api_key = os.environ.get('STRIPE_API_KEY')
    webhook_url = f"{os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.payment_status == "paid":
            metadata = webhook_response.metadata
            user_id = metadata.get("user_id")
            package_id = metadata.get("package_id")
            
            if user_id and package_id:
                days_to_add = 30 if package_id == "monthly" else 365
                end_date = datetime.now(timezone.utc) + timedelta(days=days_to_add)
                
                await db.users.update_one(
                    {"id": user_id},
                    {"$set": {
                        "subscription_status": "active",
                        "subscription_end_date": end_date.isoformat()
                    }}
                )
        
        return {"status": "success"}
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

@app.on_event("startup")
async def startup_event():
    await seed_supplements()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
