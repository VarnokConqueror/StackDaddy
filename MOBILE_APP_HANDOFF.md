# Conqueror's Court - Mobile App Handoff

## Overview
Build a native Android app (React Native/Expo) for "Conqueror's Court" - a premium meal planning and supplement tracking app with a medieval royal theme.

## Backend API
The backend is already built and deployed. Connect to:
```
API_BASE_URL: https://platepal-6.preview.emergentagent.com/api
```

All endpoints require `Authorization: Bearer <token>` header (except auth endpoints).

---

## Authentication Endpoints

### Register
```
POST /api/auth/register
Body: { "email": string, "password": string, "name": string }
Response: { "id", "email", "name", "token" }
```

### Login
```
POST /api/auth/login
Body: { "email": string, "password": string }
Response: { "id", "email", "name", "token", "subscription_status", "role", ... }
```

### Get Current User
```
GET /api/auth/me
Headers: Authorization: Bearer <token>
Response: User object with preferences, allergies, subscription status
```

### Update Preferences
```
PUT /api/auth/preferences
Body: { "dietary_preferences": [], "cooking_methods": [], "health_goal": string, "allergies": [] }
```

---

## Meal Plan Endpoints

### Create Meal Plan
```
POST /api/meal-plans
Body: {
  "plan_type": "weekly",
  "goal": "lose_weight" | "gain_weight" | "gain_muscle" | "eat_healthy" | "increase_energy" | "improve_digestion",
  "dietary_preferences": ["Meat Eating", "Vegetarian", etc.],
  "cooking_methods": ["Air Fryer", "Microwave", "Stovetop", etc.],
  "generate_with_ai": true/false,
  "servings": 1-6,
  "use_leftovers": true/false
}
Response: Full meal plan with 7 days, recipes, ingredients
```

### Get All Meal Plans
```
GET /api/meal-plans
Response: Array of meal plans
```

### Get Single Meal Plan
```
GET /api/meal-plans/{plan_id}
```

### Update Meal Plan
```
PUT /api/meal-plans/{plan_id}
Body: { "days": [...] }
```

### Delete Meal Plan
```
DELETE /api/meal-plans/{plan_id}
```

### Regenerate with AI (allergies/restrictions)
```
POST /api/meal-plans/{plan_id}/regenerate
Body: { "extra_restriction": "no dairy" }
```

---

## Shopping List Endpoints

### Generate Shopping List
```
POST /api/shopping-lists?meal_plan_id={id}&subtract_pantry=true
Response: Shopping list with categorized items
```

### Get All Shopping Lists
```
GET /api/shopping-lists
```

### Delete Shopping List
```
DELETE /api/shopping-lists/{list_id}
```

---

## Pantry Endpoints

### Get Pantry Items
```
GET /api/pantry
Response: Array of pantry items with quantities
```

### Add Pantry Item
```
POST /api/pantry
Body: {
  "name": "Olive Oil",
  "quantity": 1,
  "unit": "bottle",
  "category": "Oils & Vinegars",
  "low_stock_threshold": 0.25
}
```

### Update Pantry Item
```
PUT /api/pantry/{item_id}
Body: { "quantity": 0.5 }
```

### Delete Pantry Item
```
DELETE /api/pantry/{item_id}
```

---

## Supplement Endpoints

### Get Supplement Library
```
GET /api/supplements
```

### Get User's Supplements
```
GET /api/user-supplements
```

### Add Supplement to Tracking
```
POST /api/user-supplements
Body: { "supplement_id": string, "dose": string, "frequency": string, "time_of_day": string, "stock_quantity": number }
```

### Log Supplement Intake
```
POST /api/supplement-logs
Body: { "user_supplement_id": string, "taken_at": ISO date string }
```

---

## AI Configuration

### Get AI Config
```
GET /api/ai-config
```

### Update AI Config
```
PUT /api/ai-config
Body: { "provider": "openai"|"claude"|"gemini", "model": "gpt-5.2", "api_key": "sk-..." }
```

---

## Subscription Endpoints

### Create Checkout (Stripe)
```
POST /api/subscriptions/checkout
Body: { "package_id": "monthly"|"yearly", "origin_url": string }
Response: { "url": Stripe checkout URL }
```

### Check Status
```
GET /api/subscriptions/status/{session_id}
```

### Cancel Subscription
```
POST /api/subscriptions/cancel
```

### Redeem Promo Code
```
POST /api/promo/redeem?code={CODE}
```

---

## Design Guidelines

### Theme: "Conqueror's Court"
Medieval royal aesthetic - dark, sophisticated, powerful

### Colors
- **Background**: #0a0a0a (obsidian black)
- **Primary**: #8b5cf6 (violet-500)
- **Accent**: #ec4899 (pink-500, "neon-pink")
- **Text Primary**: #fafafa (zinc-50)
- **Text Secondary**: #a1a1aa (zinc-400)
- **Borders**: #27272a (zinc-800)
- **Success**: #22c55e (green-500)
- **Warning**: #f59e0b (amber-500)
- **Error**: #ef4444 (red-500)

### Typography
- **Headlines**: "Cinzel" font (Google Fonts) - royal, serif
- **Body**: System fonts / San Francisco

### Voice & Tone (IMPORTANT!)
All text should have medieval royal flair:
- "Delete" → "Banish" or "Burn"
- "Cancel" → "Spare It"
- "Confirm" → "So Be It"
- "Shopping List" → "Provision Scroll"
- "Supplements" → "Elixirs"
- "Create" → "Forge" or "Inscribe"
- "Loading" → "Consulting the royal archives..."
- "Empty state" → "The stores are bare" / "No scrolls yet"
- "Error" → "The ritual has failed"
- "Success" → "The deed is done"

### App Icon
Purple outline crown on transparent/dark background
Located at: /app/frontend/public/favicon.png
URL: https://static.prod-images.emergentagent.com/jobs/f78db136-44e1-462d-88d0-d47f8d4ff459/images/31983d2dc5cf3e7fa2f15072cd9fdd1dcbd7dc046fa5b6ff0586a9404eb1da48.png

---

## Core Screens to Build

1. **Landing/Splash** - Crown logo, "CONQUEROR'S COURT" title
2. **Login/Register** - Email/password + Google OAuth
3. **Dashboard** - Overview of meal plans, quick actions
4. **Meal Planner** - Create plans, view weekly calendar, edit meals
5. **Recipe Detail** - Full recipe with ingredients and instructions
6. **Shopping List (Provisions)** - Categorized checklist from meal plan
7. **Pantry** - Track staples, spices, oils
8. **Supplements (Elixirs)** - Library + personal tracking
9. **Profile** - Preferences, allergies, AI config, subscription
10. **Subscription** - Stripe checkout for premium

---

## Key Features

1. **AI Meal Generation** - User provides API key, generates full week with recipes
2. **Servings Adjustment** - 1-6 people, affects ingredient quantities
3. **Leftover Meals** - Dinner → next day lunch to reduce waste
4. **Pantry Subtraction** - Shopping list subtracts what user already has
5. **Allergy Support** - User sets allergies, AI respects them
6. **Promo Codes** - Premium access via codes

---

## Test Credentials
- Email: test@example.com
- Password: test123
- This user has admin role

## Promo Codes (for testing premium)
- FOUNDER2024
- FRIENDS100
- VIP
