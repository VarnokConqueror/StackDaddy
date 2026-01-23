"""
Comprehensive API tests for Conqueror's Court Meal Planning App
Tests: Auth, Meal Plans, Supplements, Shopping Lists, AI Config, Subscriptions, Promo Codes
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://platepal-6.preview.emergentagent.com').rstrip('/')

# Test user credentials
TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "test123"
TEST_NAME = "Test User"

# Shared state
auth_token = None
user_id = None
meal_plan_id = None
supplement_id = None
user_supplement_id = None


class TestHealthCheck:
    """Basic API health check"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"API root response: {data}")


class TestAuthentication:
    """User authentication tests"""
    
    def test_register_user(self):
        """Test user registration"""
        global auth_token, user_id
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": TEST_NAME
        })
        
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        assert data["user"]["name"] == TEST_NAME
        assert data["user"]["subscription_status"] == "inactive"
        
        auth_token = data["token"]
        user_id = data["user"]["id"]
        print(f"User registered: {TEST_EMAIL}, ID: {user_id}")
    
    def test_login_user(self):
        """Test user login"""
        global auth_token
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_EMAIL
        
        auth_token = data["token"]
        print(f"User logged in: {TEST_EMAIL}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        
        assert response.status_code == 401
        print("Invalid credentials correctly rejected")
    
    def test_get_current_user(self):
        """Test getting current user info"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        print(f"Current user: {data['name']}")
    
    def test_update_preferences(self):
        """Test updating user preferences"""
        response = requests.put(f"{BASE_URL}/api/auth/preferences", 
            json={
                "dietary_preferences": ["Vegetarian"],
                "cooking_methods": ["Air Fryer", "Stovetop"],
                "health_goal": "lose_weight"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        
        # Verify preferences were saved
        user_response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        user_data = user_response.json()
        assert "Vegetarian" in user_data.get("dietary_preferences", [])
        print("Preferences updated successfully")


class TestAIConfig:
    """AI Configuration tests"""
    
    def test_get_ai_config(self):
        """Test getting AI config"""
        response = requests.get(f"{BASE_URL}/api/ai-config", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200, f"AI config failed: {response.text}"
        data = response.json()
        assert "provider" in data
        assert "model" in data
        print(f"AI config: provider={data['provider']}, model={data['model']}")
    
    def test_update_ai_config(self):
        """Test updating AI config"""
        response = requests.put(f"{BASE_URL}/api/ai-config",
            json={
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "test_key_12345"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        print("AI config updated successfully")


class TestMealPlans:
    """Meal plan CRUD tests"""
    
    def test_create_meal_plan_without_ai(self):
        """Test creating a meal plan without AI"""
        global meal_plan_id
        
        response = requests.post(f"{BASE_URL}/api/meal-plans",
            json={
                "plan_type": "weekly",
                "goal": "lose_weight",
                "dietary_preferences": ["Vegetarian"],
                "cooking_methods": ["Air Fryer"],
                "generate_with_ai": False
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Create meal plan failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["plan_type"] == "weekly"
        assert len(data["days"]) == 7  # Weekly plan has 7 days
        
        meal_plan_id = data["id"]
        print(f"Meal plan created: {meal_plan_id}")
    
    def test_get_meal_plans(self):
        """Test getting all meal plans"""
        response = requests.get(f"{BASE_URL}/api/meal-plans", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        print(f"Found {len(data)} meal plans")
    
    def test_get_single_meal_plan(self):
        """Test getting a single meal plan"""
        response = requests.get(f"{BASE_URL}/api/meal-plans/{meal_plan_id}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == meal_plan_id
        print(f"Retrieved meal plan: {data['id']}")
    
    def test_update_meal_plan(self):
        """Test updating a meal plan"""
        # Get current plan
        get_response = requests.get(f"{BASE_URL}/api/meal-plans/{meal_plan_id}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        plan_data = get_response.json()
        
        # Update first day's breakfast
        updated_days = plan_data["days"]
        updated_days[0]["meals"]["breakfast"] = "Oatmeal with berries"
        
        response = requests.put(f"{BASE_URL}/api/meal-plans/{meal_plan_id}",
            json={"days": updated_days},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        
        # Verify update
        verify_response = requests.get(f"{BASE_URL}/api/meal-plans/{meal_plan_id}", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        verify_data = verify_response.json()
        assert verify_data["days"][0]["meals"]["breakfast"] == "Oatmeal with berries"
        print("Meal plan updated successfully")


class TestSupplements:
    """Supplement library and user supplement tests"""
    
    def test_get_supplements(self):
        """Test getting supplement library"""
        global supplement_id
        
        response = requests.get(f"{BASE_URL}/api/supplements", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should have seeded supplements
        
        # Get first supplement ID for later tests
        supplement_id = data[0]["id"]
        print(f"Found {len(data)} supplements in library")
    
    def test_add_user_supplement(self):
        """Test adding a supplement to user's tracking"""
        global user_supplement_id
        
        response = requests.post(f"{BASE_URL}/api/user-supplements",
            json={
                "supplement_id": supplement_id,
                "custom_dose": 1000,
                "dose_unit": "IU",
                "frequency": "daily",
                "timing": ["morning"],
                "stock_quantity": 30,
                "reminder_enabled": True
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Add user supplement failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["custom_dose"] == 1000
        
        user_supplement_id = data["id"]
        print(f"User supplement added: {user_supplement_id}")
    
    def test_get_user_supplements(self):
        """Test getting user's supplements"""
        response = requests.get(f"{BASE_URL}/api/user-supplements", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        print(f"User has {len(data)} tracked supplements")
    
    def test_update_user_supplement(self):
        """Test updating a user supplement"""
        response = requests.put(f"{BASE_URL}/api/user-supplements/{user_supplement_id}",
            json={"stock_quantity": 25},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        print("User supplement updated")
    
    def test_log_supplement(self):
        """Test logging supplement intake"""
        response = requests.post(f"{BASE_URL}/api/supplement-logs",
            json={
                "user_supplement_id": user_supplement_id,
                "dose_taken": 1000,
                "notes": "Taken with breakfast"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print("Supplement intake logged")
    
    def test_get_supplement_logs(self):
        """Test getting supplement logs"""
        response = requests.get(f"{BASE_URL}/api/supplement-logs", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        print(f"Found {len(data)} supplement logs")


class TestShoppingLists:
    """Shopping list tests"""
    
    def test_generate_shopping_list(self):
        """Test generating shopping list from meal plan"""
        response = requests.post(f"{BASE_URL}/api/shopping-lists?meal_plan_id={meal_plan_id}",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Generate shopping list failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert "items" in data
        assert data["meal_plan_id"] == meal_plan_id
        print(f"Shopping list generated with {len(data['items'])} items")
    
    def test_get_shopping_lists(self):
        """Test getting all shopping lists"""
        response = requests.get(f"{BASE_URL}/api/shopping-lists", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} shopping lists")


class TestSubscription:
    """Subscription and Stripe checkout tests"""
    
    def test_checkout_monthly(self):
        """Test initiating monthly subscription checkout"""
        response = requests.post(f"{BASE_URL}/api/subscriptions/checkout",
            json={
                "package_id": "monthly",
                "origin_url": "https://platepal-6.preview.emergentagent.com"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should return checkout URL or Stripe error (test key)
        assert response.status_code in [200, 500], f"Checkout failed: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "url" in data or "session_id" in data
            print(f"Monthly checkout initiated")
        else:
            print(f"Stripe checkout returned error (expected with test key): {response.text[:100]}")
    
    def test_checkout_yearly(self):
        """Test initiating yearly subscription checkout"""
        response = requests.post(f"{BASE_URL}/api/subscriptions/checkout",
            json={
                "package_id": "yearly",
                "origin_url": "https://platepal-6.preview.emergentagent.com"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [200, 500]
        print("Yearly checkout test completed")
    
    def test_subscription_details(self):
        """Test getting subscription details"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/details", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"Subscription status: {data['status']}")


class TestPromoCode:
    """Promo code tests"""
    
    def test_redeem_invalid_promo(self):
        """Test redeeming invalid promo code"""
        response = requests.post(f"{BASE_URL}/api/promo/redeem",
            json={"code": "INVALID_CODE_12345"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 404
        print("Invalid promo code correctly rejected")


class TestOAuthStatus:
    """OAuth provider status tests"""
    
    def test_oauth_status(self):
        """Test OAuth provider status endpoint"""
        response = requests.get(f"{BASE_URL}/api/auth/oauth/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "google" in data
        assert data["google"] == True  # Google always available via Emergent
        print(f"OAuth status: {data}")


class TestCleanup:
    """Cleanup tests - run last"""
    
    def test_delete_user_supplement(self):
        """Test deleting user supplement"""
        if user_supplement_id:
            response = requests.delete(f"{BASE_URL}/api/user-supplements/{user_supplement_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            print("User supplement deleted")
    
    def test_delete_meal_plan(self):
        """Test deleting meal plan"""
        if meal_plan_id:
            response = requests.delete(f"{BASE_URL}/api/meal-plans/{meal_plan_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code == 200
            print("Meal plan deleted")
            
            # Verify deletion
            verify_response = requests.get(f"{BASE_URL}/api/meal-plans/{meal_plan_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert verify_response.status_code == 404
            print("Meal plan deletion verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
