# Conqueror's Court - Meal Planning & Supplement Tracking App

## Original Problem Statement
Build a subscription-based application that provides weekly meal plans with corresponding shopping lists and allows users to track their supplement intake.

## User Personas
1. **Health-conscious individuals** seeking meal planning assistance
2. **Fitness enthusiasts** tracking nutrition and supplements
3. **Busy professionals** who want simple meal prep with shopping lists

## Core Requirements

### 1. Meal Planning
- [x] Generate weekly meal plans based on user dietary preferences
- [x] Support dietary options: Meat Eating, Poultry Only, Fish Only, Vegetarian, Vegan
- [x] Cooking method selection: Air Fryer, Microwave, Stovetop, Toaster, Instant Pot
- [x] AI-powered meal generation with FULL recipes (ingredients + detailed instructions)
- [x] Manual meal editing and customization
- [x] "View Royal Recipe" popup with ingredients and cooking instructions
- [x] Health goal integration (lose weight, gain muscle, etc.)
- [x] Delete meal plans with themed confirmation dialog ("Banish from realm")
- [x] **Servings selector** - Choose 1-6 people, adjusts ingredient quantities
- [x] **Leftover meals** - Dinner → next day's lunch to minimize ingredients
- [x] **Meal timestamps** - Default times for breakfast, lunch, dinner, snack

### 2. Shopping List
- [x] Generate shopping list from meal plan recipes
- [x] Smart ingredient aggregation (combines same ingredients)
- [x] Parse quantities and units automatically
- [x] Categorize items (Produce, Proteins, Dairy, etc.)
- [x] Progress bar with check-off functionality
- [x] Delete shopping lists
- [x] Skip leftover meal ingredients (no double counting)
- [x] Subtract pantry items from shopping list

### 3. Pantry Tracking (NEW)
- [x] Track spices, oils, staples, and other pantry items
- [x] Low stock alerts with customizable thresholds
- [x] Categories: Spices, Oils & Vinegars, Grains & Pasta, Canned Goods, Condiments, Baking
- [x] Edit/delete pantry items
- [x] Pantry items subtracted from shopping list automatically

### 4. Supplement Tracking
- [x] Pre-populated supplement database (8+ supplements)
- [x] Add supplements to personal inventory
- [x] Track dose, timing, frequency, stock quantity
- [x] Log daily supplement intake

### 4. AI Integration
- [x] AI provider selection: OpenAI, Claude, Gemini
- [x] User provides their own API key
- [x] AI generates meal suggestions based on health goals
- [x] AI considers dietary restrictions and allergies

### 5. Subscription & Monetization
- [x] Stripe recurring subscriptions (monthly $9.99, yearly $99.99)
- [x] Auto-renewal until cancelled
- [x] Subscription cancellation support
- [x] Promo code system for lifetime premium access
- [x] Owner bypass for premium status

### 6. Authentication
- [x] Email/password registration and login
- [x] JWT-based authentication
- [x] Google OAuth (via Emergent)
- [ ] Facebook OAuth (scaffolded, needs credentials)

## Technical Architecture

### Backend (FastAPI)
- `/app/backend/server.py` - Main API server
- MongoDB for data storage
- JWT authentication with 720-hour expiration
- Stripe SDK for recurring subscriptions

### Frontend (React)
- `/app/frontend/src/` - React application
- Tailwind CSS with "Conqueror's Court" dark theme
- Shadcn/UI components
- React Router for navigation

### Database Collections
- `users` - User accounts and preferences
- `meal_plans` - Weekly meal plans with days and meals
- `supplements` - Supplement library
- `user_supplements` - User's supplement tracking
- `supplement_logs` - Daily intake logs
- `shopping_lists` - Shopping lists from meal plans
- `ai_configs` - User AI provider settings
- `promo_codes` - Promotional codes
- `payment_transactions` - Stripe transactions
- `stripe_prices` - Cached Stripe price IDs

## What's Been Implemented (as of Jan 2026)

### Session 1 - Initial Build
- Basic authentication (JWT + Google OAuth)
- User profile with preferences
- Meal planner scaffolding
- Supplement library with seeded data
- Dark theme UI

### Session 2 - Core Fixes & Subscriptions
- **Fixed**: AI config endpoint (was returning 520 error)
- **Fixed**: Stripe subscription buttons visibility issue
- **Implemented**: Recurring Stripe subscriptions (monthly/yearly)
- **Implemented**: Subscription cancellation
- **Implemented**: Meal plan deletion
- **Implemented**: Cooking instructions in meal plans
- **Implemented**: MealPlanDay model with instructions field

## Known Limitations

1. **AI Meal Generation**: Requires user to provide their own OpenAI/Claude/Gemini API key
2. **Stripe Checkout**: Test key `sk_test_emergent` doesn't have real products - needs real Stripe setup for production
3. **Facebook OAuth**: Scaffolded but requires Facebook App credentials

## API Endpoints Summary

### Auth
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user
- `PUT /api/auth/preferences` - Update user preferences
- `POST /api/auth/oauth/google` - Google OAuth

### Meal Plans
- `POST /api/meal-plans` - Create meal plan
- `GET /api/meal-plans` - Get user's meal plans
- `GET /api/meal-plans/{id}` - Get single meal plan
- `PUT /api/meal-plans/{id}` - Update meal plan
- `DELETE /api/meal-plans/{id}` - Delete meal plan

### Supplements
- `GET /api/supplements` - Get supplement library
- `POST /api/user-supplements` - Add to user's tracking
- `GET /api/user-supplements` - Get user's supplements
- `POST /api/supplement-logs` - Log intake

### Subscriptions
- `POST /api/subscriptions/checkout` - Create Stripe checkout
- `GET /api/subscriptions/status/{session_id}` - Check payment status
- `POST /api/subscriptions/cancel` - Cancel subscription
- `GET /api/subscriptions/details` - Get subscription details

### Shopping Lists
- `POST /api/shopping-lists?meal_plan_id={id}` - Generate shopping list
- `GET /api/shopping-lists` - Get user's shopping lists

## Test Credentials
- Email: `test@example.com`
- Password: `test123`

## Backlog / Future Tasks

### P1 - High Priority
- [ ] Admin Panel for promo code management
- [ ] Facebook OAuth integration

### P2 - Medium Priority
- [x] AI-based allergy editing ("regenerate without peanuts")
- [x] User allergies saved in profile and auto-applied to AI generation
- [ ] Timestamps for meals and supplements
- [ ] Ingredient tracking in shopping list

### P3 - Lower Priority
- [ ] Social profile picture integration
- [ ] Meal plan templates/favorites
- [ ] Supplement reminders/notifications
