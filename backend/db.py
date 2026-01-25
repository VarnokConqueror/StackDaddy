import asyncpg
import os
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

pool: Optional[asyncpg.Pool] = None

async def init_pool():
    global pool
    pool = await asyncpg.create_pool(os.environ['DATABASE_URL'])
    return pool

async def close_pool():
    global pool
    if pool:
        await pool.close()

def _serialize_jsonb(value: Any) -> str:
    if value is None:
        return None
    return json.dumps(value)

async def fetch_one(query: str, *args) -> Optional[Dict[str, Any]]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None

async def fetch_all(query: str, *args) -> List[Dict[str, Any]]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]

async def execute(query: str, *args) -> str:
    async with pool.acquire() as conn:
        return await conn.execute(query, *args)

async def fetch_count(query: str, *args) -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        return row[0] if row else 0

async def find_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    return await fetch_one("SELECT * FROM users WHERE id = $1", user_id)

async def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return await fetch_one("SELECT * FROM users WHERE email = $1", email)

async def find_user_by_oauth(provider: str, oauth_id: str) -> Optional[Dict[str, Any]]:
    return await fetch_one(
        "SELECT * FROM users WHERE oauth_provider = $1 AND oauth_id = $2",
        provider, oauth_id
    )

async def insert_user(user_doc: Dict[str, Any]) -> None:
    await execute(
        """INSERT INTO users (id, email, password, name, subscription_status, subscription_end_date,
           dietary_preferences, cooking_methods, health_goal, allergies, role, oauth_provider, oauth_id,
           picture_url, stripe_customer_id, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)""",
        user_doc.get("id"),
        user_doc.get("email"),
        user_doc.get("password"),
        user_doc.get("name"),
        user_doc.get("subscription_status", "inactive"),
        user_doc.get("subscription_end_date"),
        _serialize_jsonb(user_doc.get("dietary_preferences", [])),
        _serialize_jsonb(user_doc.get("cooking_methods", [])),
        user_doc.get("health_goal"),
        _serialize_jsonb(user_doc.get("allergies", [])),
        user_doc.get("role"),
        user_doc.get("oauth_provider"),
        user_doc.get("oauth_id"),
        user_doc.get("picture_url"),
        user_doc.get("stripe_customer_id"),
        user_doc.get("created_at")
    )

async def update_user(user_id: str, updates: Dict[str, Any]) -> None:
    set_clauses = []
    values = []
    param_idx = 1
    
    for key, value in updates.items():
        if key in ["dietary_preferences", "cooking_methods", "allergies"]:
            value = _serialize_jsonb(value)
        set_clauses.append(f"{key} = ${param_idx}")
        values.append(value)
        param_idx += 1
    
    values.append(user_id)
    query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ${param_idx}"
    await execute(query, *values)

async def count_supplements() -> int:
    return await fetch_count("SELECT COUNT(*) FROM supplements")

async def insert_supplements(supplements: List[Dict[str, Any]]) -> None:
    async with pool.acquire() as conn:
        for supp in supplements:
            await conn.execute(
                """INSERT INTO supplements (id, name, description, benefits, dosage, timing, warnings, category, image_url, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())
                   ON CONFLICT (id) DO NOTHING""",
                supp.get("id"),
                supp.get("name"),
                supp.get("purpose"),
                _serialize_jsonb({"typical_dose_min": supp.get("typical_dose_min"), "typical_dose_max": supp.get("typical_dose_max")}),
                supp.get("dose_unit"),
                None,
                _serialize_jsonb({"warnings": supp.get("warnings"), "interactions": supp.get("interactions")}),
                None,
                None
            )

async def find_all_supplements() -> List[Dict[str, Any]]:
    return await fetch_all("SELECT * FROM supplements ORDER BY name")

async def find_supplement_by_id(supp_id: str) -> Optional[Dict[str, Any]]:
    return await fetch_one("SELECT * FROM supplements WHERE id = $1", supp_id)

async def insert_supplement(supp_doc: Dict[str, Any]) -> None:
    await execute(
        """INSERT INTO supplements (id, name, description, benefits, dosage, timing, warnings, category, image_url, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW())""",
        supp_doc.get("id"),
        supp_doc.get("name"),
        supp_doc.get("purpose"),
        _serialize_jsonb({"typical_dose_min": supp_doc.get("typical_dose_min"), "typical_dose_max": supp_doc.get("typical_dose_max")}),
        supp_doc.get("dose_unit"),
        None,
        _serialize_jsonb({"warnings": supp_doc.get("warnings"), "interactions": supp_doc.get("interactions")}),
        None,
        None
    )

async def find_promo_by_code(code: str) -> Optional[Dict[str, Any]]:
    return await fetch_one("SELECT * FROM promo_codes WHERE code = $1", code)

async def update_promo_uses(code: str, user_id: str) -> None:
    await execute(
        "UPDATE promo_codes SET uses = uses + 1 WHERE code = $1",
        code
    )

async def insert_promo_code(promo_doc: Dict[str, Any]) -> None:
    await execute(
        """INSERT INTO promo_codes (id, code, discount_percent, discount_amount, valid_from, valid_until, max_uses, uses, active, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
        promo_doc.get("id"),
        promo_doc.get("code"),
        promo_doc.get("discount_percent"),
        promo_doc.get("discount_amount"),
        promo_doc.get("valid_from"),
        promo_doc.get("valid_until"),
        promo_doc.get("max_uses", 0),
        promo_doc.get("uses", 0),
        promo_doc.get("active", True),
        promo_doc.get("created_at")
    )

async def find_all_promo_codes() -> List[Dict[str, Any]]:
    return await fetch_all("SELECT * FROM promo_codes ORDER BY created_at DESC")

async def deactivate_promo_code(code: str) -> int:
    result = await execute("UPDATE promo_codes SET active = false WHERE code = $1", code)
    return int(result.split()[-1]) if result else 0

async def insert_meal(meal_doc: Dict[str, Any]) -> None:
    await execute(
        """INSERT INTO meals (id, user_id, name, description, ingredients, instructions, cooking_method, prep_time, cook_time, servings, nutrition, image_url, tags, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)""",
        meal_doc.get("id"),
        meal_doc.get("user_id"),
        meal_doc.get("name"),
        meal_doc.get("description"),
        _serialize_jsonb(meal_doc.get("ingredients", [])),
        _serialize_jsonb(meal_doc.get("instructions", [])),
        meal_doc.get("cooking_method"),
        meal_doc.get("prep_time"),
        meal_doc.get("cook_time"),
        meal_doc.get("servings"),
        _serialize_jsonb(meal_doc.get("nutrition")),
        meal_doc.get("image_url"),
        _serialize_jsonb(meal_doc.get("tags", [])),
        meal_doc.get("created_at")
    )

async def find_meals(cooking_method: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    query = "SELECT * FROM meals WHERE 1=1"
    params = []
    param_idx = 1
    
    if cooking_method:
        query += f" AND cooking_method = ${param_idx}"
        params.append(cooking_method)
        param_idx += 1
    
    if tags:
        query += f" AND tags ?| ${param_idx}"
        params.append(tags)
        param_idx += 1
    
    return await fetch_all(query, *params)

async def find_meal_by_id(meal_id: str) -> Optional[Dict[str, Any]]:
    return await fetch_one("SELECT * FROM meals WHERE id = $1", meal_id)

async def insert_meal_plan(plan_doc: Dict[str, Any]) -> None:
    await execute(
        """INSERT INTO meal_plans (id, user_id, plan_type, start_date, end_date, days, dietary_preferences, cooking_methods, servings, goal, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""",
        plan_doc.get("id"),
        plan_doc.get("user_id"),
        plan_doc.get("plan_type"),
        plan_doc.get("start_date"),
        plan_doc.get("end_date"),
        _serialize_jsonb(plan_doc.get("days", [])),
        _serialize_jsonb(plan_doc.get("dietary_preferences", [])),
        _serialize_jsonb(plan_doc.get("cooking_methods", [])),
        plan_doc.get("servings", 1),
        plan_doc.get("goal"),
        plan_doc.get("created_at")
    )

async def find_meal_plans_by_user(user_id: str) -> List[Dict[str, Any]]:
    return await fetch_all("SELECT * FROM meal_plans WHERE user_id = $1 ORDER BY created_at DESC", user_id)

async def find_meal_plan_by_id(plan_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    return await fetch_one("SELECT * FROM meal_plans WHERE id = $1 AND user_id = $2", plan_id, user_id)

async def update_meal_plan(plan_id: str, user_id: str, updates: Dict[str, Any]) -> None:
    set_clauses = []
    values = []
    param_idx = 1
    
    for key, value in updates.items():
        if key in ["days", "dietary_preferences", "cooking_methods"]:
            value = _serialize_jsonb(value)
        set_clauses.append(f"{key} = ${param_idx}")
        values.append(value)
        param_idx += 1
    
    values.extend([plan_id, user_id])
    query = f"UPDATE meal_plans SET {', '.join(set_clauses)} WHERE id = ${param_idx} AND user_id = ${param_idx + 1}"
    await execute(query, *values)

async def delete_meal_plan(plan_id: str, user_id: str) -> int:
    result = await execute("DELETE FROM meal_plans WHERE id = $1 AND user_id = $2", plan_id, user_id)
    return int(result.split()[-1]) if result else 0

async def delete_shopping_lists_by_meal_plan(meal_plan_id: str) -> None:
    await execute("DELETE FROM shopping_lists WHERE meal_plan_id = $1", meal_plan_id)

async def insert_shopping_list(list_doc: Dict[str, Any]) -> None:
    await execute(
        """INSERT INTO shopping_lists (id, user_id, meal_plan_id, items, created_at)
           VALUES ($1, $2, $3, $4, $5)""",
        list_doc.get("id"),
        list_doc.get("user_id"),
        list_doc.get("meal_plan_id"),
        _serialize_jsonb(list_doc.get("items", [])),
        list_doc.get("created_at")
    )

async def find_shopping_lists_by_user(user_id: str) -> List[Dict[str, Any]]:
    return await fetch_all("SELECT * FROM shopping_lists WHERE user_id = $1 ORDER BY created_at DESC", user_id)

async def delete_shopping_list(list_id: str, user_id: str) -> int:
    result = await execute("DELETE FROM shopping_lists WHERE id = $1 AND user_id = $2", list_id, user_id)
    return int(result.split()[-1]) if result else 0

async def find_pantry_by_user(user_id: str) -> List[Dict[str, Any]]:
    return await fetch_all("SELECT * FROM pantry WHERE user_id = $1 ORDER BY category, name", user_id)

async def insert_pantry_item(item_doc: Dict[str, Any]) -> None:
    await execute(
        """INSERT INTO pantry (id, user_id, name, quantity, unit, category, low_stock_threshold, created_at, updated_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
        item_doc.get("id"),
        item_doc.get("user_id"),
        item_doc.get("name"),
        item_doc.get("quantity"),
        item_doc.get("unit"),
        item_doc.get("category"),
        item_doc.get("low_stock_threshold"),
        item_doc.get("created_at"),
        item_doc.get("updated_at")
    )

async def find_pantry_item(item_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    return await fetch_one("SELECT * FROM pantry WHERE id = $1 AND user_id = $2", item_id, user_id)

async def update_pantry_item(item_id: str, user_id: str, updates: Dict[str, Any]) -> int:
    set_clauses = []
    values = []
    param_idx = 1
    
    for key, value in updates.items():
        set_clauses.append(f"{key} = ${param_idx}")
        values.append(value)
        param_idx += 1
    
    values.extend([item_id, user_id])
    query = f"UPDATE pantry SET {', '.join(set_clauses)} WHERE id = ${param_idx} AND user_id = ${param_idx + 1}"
    result = await execute(query, *values)
    return int(result.split()[-1]) if result else 0

async def delete_pantry_item(item_id: str, user_id: str) -> int:
    result = await execute("DELETE FROM pantry WHERE id = $1 AND user_id = $2", item_id, user_id)
    return int(result.split()[-1]) if result else 0

async def insert_user_supplement(supp_doc: Dict[str, Any]) -> None:
    await execute(
        """INSERT INTO user_supplements (id, user_id, supplement_id, dosage, frequency, time_of_day, notes, active, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
        supp_doc.get("id"),
        supp_doc.get("user_id"),
        supp_doc.get("supplement_id"),
        supp_doc.get("custom_dose"),
        supp_doc.get("frequency"),
        supp_doc.get("timing", [None])[0] if supp_doc.get("timing") else None,
        supp_doc.get("expiration_date"),
        supp_doc.get("reminder_enabled", True),
        supp_doc.get("created_at")
    )

async def find_user_supplements(user_id: str) -> List[Dict[str, Any]]:
    return await fetch_all(
        """SELECT us.*, s.name as supplement_name 
           FROM user_supplements us 
           JOIN supplements s ON us.supplement_id = s.id 
           WHERE us.user_id = $1 ORDER BY us.created_at DESC""",
        user_id
    )

async def update_user_supplement(supp_id: str, user_id: str, updates: Dict[str, Any]) -> None:
    set_clauses = []
    values = []
    param_idx = 1
    
    for key, value in updates.items():
        set_clauses.append(f"{key} = ${param_idx}")
        values.append(value)
        param_idx += 1
    
    values.extend([supp_id, user_id])
    query = f"UPDATE user_supplements SET {', '.join(set_clauses)} WHERE id = ${param_idx} AND user_id = ${param_idx + 1}"
    await execute(query, *values)

async def delete_user_supplement(supp_id: str, user_id: str) -> None:
    await execute("DELETE FROM user_supplements WHERE id = $1 AND user_id = $2", supp_id, user_id)

async def insert_supplement_log(log_doc: Dict[str, Any]) -> None:
    await execute(
        """INSERT INTO supplement_logs (id, user_id, user_supplement_id, taken_at, notes)
           VALUES ($1, $2, $3, $4, $5)""",
        log_doc.get("id"),
        log_doc.get("user_id"),
        log_doc.get("user_supplement_id"),
        log_doc.get("taken_at"),
        log_doc.get("notes")
    )

async def find_supplement_logs(user_id: str) -> List[Dict[str, Any]]:
    return await fetch_all(
        "SELECT * FROM supplement_logs WHERE user_id = $1 ORDER BY taken_at DESC",
        user_id
    )

async def find_ai_config(user_id: str) -> Optional[Dict[str, Any]]:
    return await fetch_one("SELECT * FROM ai_configs WHERE user_id = $1", user_id)

async def insert_ai_config(config_doc: Dict[str, Any]) -> None:
    await execute(
        """INSERT INTO ai_configs (id, user_id, provider, model, api_key, created_at)
           VALUES ($1, $2, $3, $4, $5, NOW())""",
        config_doc.get("id"),
        config_doc.get("user_id"),
        config_doc.get("provider", "openai"),
        config_doc.get("model", "gpt-5.2"),
        config_doc.get("api_key")
    )

async def update_ai_config(user_id: str, updates: Dict[str, Any]) -> None:
    set_clauses = []
    values = []
    param_idx = 1
    
    for key, value in updates.items():
        set_clauses.append(f"{key} = ${param_idx}")
        values.append(value)
        param_idx += 1
    
    values.append(user_id)
    query = f"UPDATE ai_configs SET {', '.join(set_clauses)} WHERE user_id = ${param_idx}"
    await execute(query, *values)

async def find_stripe_price(package_id: str) -> Optional[Dict[str, Any]]:
    return await fetch_one("SELECT * FROM stripe_prices WHERE name = $1 AND active = true", package_id)

async def insert_stripe_price(price_doc: Dict[str, Any]) -> None:
    await execute(
        """INSERT INTO stripe_prices (id, stripe_price_id, name, amount, currency, interval, active, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())""",
        price_doc.get("id"),
        price_doc.get("price_id"),
        price_doc.get("package_id"),
        price_doc.get("amount"),
        "usd",
        price_doc.get("interval"),
        True
    )

async def insert_payment_transaction(txn_doc: Dict[str, Any]) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO payment_transactions (id, user_id, session_id, amount, currency, package_id, payment_status, subscription_mode, created_at)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
               ON CONFLICT (id) DO NOTHING""",
            txn_doc.get("id"),
            txn_doc.get("user_id"),
            txn_doc.get("session_id"),
            txn_doc.get("amount"),
            txn_doc.get("currency", "usd"),
            txn_doc.get("package_id"),
            txn_doc.get("payment_status", "pending"),
            txn_doc.get("subscription_mode", True),
            txn_doc.get("created_at")
        )

async def find_payment_transaction(session_id: str) -> Optional[Dict[str, Any]]:
    return await fetch_one("SELECT * FROM payment_transactions WHERE session_id = $1", session_id)

async def update_payment_transaction(session_id: str, updates: Dict[str, Any]) -> None:
    set_clauses = []
    values = []
    param_idx = 1
    
    for key, value in updates.items():
        set_clauses.append(f"{key} = ${param_idx}")
        values.append(value)
        param_idx += 1
    
    values.append(session_id)
    query = f"UPDATE payment_transactions SET {', '.join(set_clauses)} WHERE session_id = ${param_idx}"
    await execute(query, *values)

async def find_subscription_by_user(user_id: str) -> Optional[Dict[str, Any]]:
    return await fetch_one("SELECT * FROM subscriptions WHERE user_id = $1", user_id)

async def insert_subscription(sub_doc: Dict[str, Any]) -> None:
    await execute(
        """INSERT INTO subscriptions (id, user_id, stripe_subscription_id, status, plan, 
           current_period_start, current_period_end, cancel_at_period_end, created_at, updated_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
        sub_doc.get('id', str(uuid.uuid4())),
        sub_doc['user_id'],
        sub_doc.get('stripe_subscription_id'),
        sub_doc.get('status', 'active'),
        sub_doc.get('plan'),
        sub_doc.get('current_period_start'),
        sub_doc.get('current_period_end'),
        sub_doc.get('cancel_at_period_end', False),
        sub_doc.get('created_at', datetime.now(timezone.utc)),
        sub_doc.get('updated_at', datetime.now(timezone.utc))
    )

async def update_subscription(user_id: str, updates: Dict[str, Any]) -> None:
    set_clauses = []
    values = []
    param_idx = 1
    
    for key, value in updates.items():
        set_clauses.append(f"{key} = ${param_idx}")
        values.append(value)
        param_idx += 1
    
    values.append(user_id)
    query = f"UPDATE subscriptions SET {', '.join(set_clauses)} WHERE user_id = ${param_idx}"
    await execute(query, *values)

async def insert_payment(payment_doc: Dict[str, Any]) -> None:
    await execute(
        """INSERT INTO payments (id, user_id, stripe_payment_id, amount, currency, status, 
           description, created_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
        payment_doc.get('id', str(uuid.uuid4())),
        payment_doc['user_id'],
        payment_doc.get('stripe_payment_id'),
        payment_doc.get('amount'),
        payment_doc.get('currency', 'usd'),
        payment_doc.get('status', 'succeeded'),
        payment_doc.get('description'),
        payment_doc.get('created_at', datetime.now(timezone.utc))
    )

async def find_payments_by_user(user_id: str) -> List[Dict[str, Any]]:
    return await fetch_all("SELECT * FROM payments WHERE user_id = $1 ORDER BY created_at DESC", user_id)
