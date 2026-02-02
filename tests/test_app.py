"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    from app import activities
    
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Soccer Team": {
            "description": "Join the school soccer team and compete in matches",
            "schedule": "Wednesdays, 4:00 PM - 6:00 PM",
            "max_participants": 18,
            "participants": []
        },
        "Basketball Club": {
            "description": "Practice basketball skills and play friendly games",
            "schedule": "Mondays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Art Workshop": {
            "description": "Explore painting, drawing, and sculpture techniques",
            "schedule": "Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 10,
            "participants": []
        },
        "Drama Club": {
            "description": "Act, direct, and produce school plays and performances",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": []
        },
        "Math Olympiad": {
            "description": "Prepare for math competitions and solve challenging problems",
            "schedule": "Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": []
        },
        "Science Club": {
            "description": "Conduct experiments and explore scientific concepts",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": []
        }
    }
    
    # Clear current activities and restore original state
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(original_activities)


class TestRoot:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the get activities endpoint"""
    
    def test_get_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_get_activities_structure(self, client):
        """Test that activity structure is correct"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_get_activities_contains_participants(self, client):
        """Test that activities contain participant information"""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have initial participants
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignup:
    """Tests for the signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Soccer Team/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "alex@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant"""
        client.post(
            "/activities/Basketball Club/signup",
            params={"email": "jessica@mergington.edu"}
        )
        
        response = client.get("/activities")
        data = response.json()
        assert "jessica@mergington.edu" in data["Basketball Club"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_duplicate_activity(self, client):
        """Test that a student cannot signup for multiple activities"""
        # Student signs up for Soccer Team
        client.post(
            "/activities/Soccer Team/signup",
            params={"email": "thomas@mergington.edu"}
        )
        
        # Try to sign up for another activity
        response = client.post(
            "/activities/Basketball Club/signup",
            params={"email": "thomas@mergington.edu"}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_already_registered_student(self, client):
        """Test that already registered students can't sign up again"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400


class TestMultipleSignups:
    """Tests for multiple signup scenarios"""
    
    def test_multiple_different_students(self, client):
        """Test multiple different students can sign up"""
        emails = ["alice@mergington.edu", "bob@mergington.edu", "charlie@mergington.edu"]
        
        for email in emails:
            response = client.post(
                "/activities/Art Workshop/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all were added
        response = client.get("/activities")
        data = response.json()
        for email in emails:
            assert email in data["Art Workshop"]["participants"]
    
    def test_capacity_tracking(self, client):
        """Test that participant count is tracked correctly"""
        response = client.get("/activities")
        data = response.json()
        initial_count = len(data["Drama Club"]["participants"])
        
        client.post(
            "/activities/Drama Club/signup",
            params={"email": "new_student@mergington.edu"}
        )
        
        response = client.get("/activities")
        data = response.json()
        new_count = len(data["Drama Club"]["participants"])
        
        assert new_count == initial_count + 1
