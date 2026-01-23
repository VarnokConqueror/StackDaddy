import requests
import sys
import json
from datetime import datetime

class MealPlanningAPITester:
    def __init__(self, base_url="https://platepal-6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.content else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text[:200]
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "", 200)

    def test_register(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_user_data = {
            "email": f"test_user_{timestamp}@example.com",
            "password": "TestPass123!",
            "name": f"Test User {timestamp}"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            print(f"   Token obtained: {self.token[:20]}...")
            return True
        return False

    def test_login(self):
        """Test user login with existing credentials"""
        if not self.token:
            print("❌ No token available for login test")
            return False
            
        # Test getting current user info first
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_supplements_library(self):
        """Test supplement library endpoints"""
        success, response = self.run_test(
            "Get Supplements Library",
            "GET",
            "supplements",
            200
        )
        
        if success and len(response) > 0:
            print(f"   Found {len(response)} supplements in library")
            return True
        return False

    def test_meal_plan_creation(self):
        """Test meal plan creation"""
        meal_plan_data = {
            "plan_type": "weekly",
            "dietary_preferences": ["vegetarian"],
            "cooking_methods": ["stovetop", "oven"],
            "generate_with_ai": False
        }
        
        success, response = self.run_test(
            "Create Meal Plan",
            "POST",
            "meal-plans",
            200,
            data=meal_plan_data
        )
        
        if success and 'id' in response:
            self.meal_plan_id = response['id']
            print(f"   Meal plan created with ID: {self.meal_plan_id}")
            return True
        return False

    def test_get_meal_plans(self):
        """Test getting user's meal plans"""
        return self.run_test(
            "Get Meal Plans",
            "GET",
            "meal-plans",
            200
        )[0]

    def test_user_supplement_management(self):
        """Test adding supplement to user inventory"""
        # First get available supplements
        success, supplements = self.run_test(
            "Get Supplements for User Management",
            "GET",
            "supplements",
            200
        )
        
        if not success or not supplements:
            return False
            
        # Add first supplement to user inventory
        supplement_data = {
            "supplement_id": supplements[0]['id'],
            "custom_dose": 1000,
            "dose_unit": "mg",
            "frequency": "daily",
            "timing": ["morning"],
            "stock_quantity": 30,
            "reminder_enabled": True
        }
        
        success, response = self.run_test(
            "Add User Supplement",
            "POST",
            "user-supplements",
            200,
            data=supplement_data
        )
        
        if success and 'id' in response:
            self.user_supplement_id = response['id']
            print(f"   User supplement added with ID: {self.user_supplement_id}")
            return True
        return False

    def test_get_user_supplements(self):
        """Test getting user's supplements"""
        return self.run_test(
            "Get User Supplements",
            "GET",
            "user-supplements",
            200
        )[0]

    def test_supplement_logging(self):
        """Test logging supplement intake"""
        if not hasattr(self, 'user_supplement_id'):
            print("❌ No user supplement ID available for logging test")
            return False
            
        log_data = {
            "user_supplement_id": self.user_supplement_id,
            "dose_taken": 1000,
            "notes": "Morning dose with breakfast"
        }
        
        return self.run_test(
            "Log Supplement Intake",
            "POST",
            "supplement-logs",
            200,
            data=log_data
        )[0]

    def test_ai_config(self):
        """Test AI configuration endpoints"""
        # Get AI config
        success, response = self.run_test(
            "Get AI Config",
            "GET",
            "ai-config",
            200
        )
        
        if not success:
            return False
            
        # Update AI config
        config_data = {
            "provider": "openai",
            "model": "gpt-5.2",
            "api_key": "test_key_placeholder"
        }
        
        return self.run_test(
            "Update AI Config",
            "PUT",
            "ai-config",
            200,
            data=config_data
        )[0]

    def test_subscription_checkout(self):
        """Test subscription checkout creation"""
        checkout_data = {
            "package_id": "monthly",
            "origin_url": self.base_url
        }
        
        success, response = self.run_test(
            "Create Subscription Checkout",
            "POST",
            "subscriptions/checkout",
            200,
            data=checkout_data
        )
        
        if success and 'url' in response:
            print(f"   Checkout URL created: {response['url'][:50]}...")
            return True
        return False

    def test_preferences_update(self):
        """Test updating user preferences"""
        preferences_data = {
            "dietary_preferences": ["vegetarian", "gluten-free"],
            "cooking_methods": ["air-fryer", "microwave"]
        }
        
        return self.run_test(
            "Update User Preferences",
            "PUT",
            "auth/preferences",
            200,
            data=preferences_data
        )[0]

def main():
    print("🚀 Starting Meal Planning API Tests")
    print("=" * 50)
    
    tester = MealPlanningAPITester()
    
    # Test sequence
    tests = [
        ("Root API", tester.test_root_endpoint),
        ("User Registration", tester.test_register),
        ("User Authentication", tester.test_login),
        ("Supplements Library", tester.test_supplements_library),
        ("Meal Plan Creation", tester.test_meal_plan_creation),
        ("Get Meal Plans", tester.test_get_meal_plans),
        ("User Supplement Management", tester.test_user_supplement_management),
        ("Get User Supplements", tester.test_get_user_supplements),
        ("Supplement Logging", tester.test_supplement_logging),
        ("AI Configuration", tester.test_ai_config),
        ("Subscription Checkout", tester.test_subscription_checkout),
        ("User Preferences Update", tester.test_preferences_update),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if not result:
                print(f"⚠️  {test_name} failed - continuing with other tests")
        except Exception as e:
            print(f"💥 {test_name} crashed: {str(e)}")
            tester.failed_tests.append({
                "test": test_name,
                "error": str(e)
            })
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%")
    
    if tester.failed_tests:
        print(f"\n❌ FAILED TESTS ({len(tester.failed_tests)}):")
        for i, failure in enumerate(tester.failed_tests, 1):
            print(f"{i}. {failure.get('test', 'Unknown')}")
            if 'error' in failure:
                print(f"   Error: {failure['error']}")
            elif 'expected' in failure:
                print(f"   Expected: {failure['expected']}, Got: {failure['actual']}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())