"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that the activities endpoint returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that the activities endpoint returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_has_expected_activities(self):
        """Test that the activities endpoint returns the expected activities"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Basketball",
            "Tennis Club",
            "Drama Club",
            "Visual Arts",
            "Debate Team",
            "Science Club",
            "Gym Class"
        ]
        for activity in expected_activities:
            assert activity in data

    def test_activity_has_required_fields(self):
        """Test that each activity has the required fields"""
        response = client.get("/activities")
        data = response.json()
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Activity {activity_name} missing field {field}"


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]

    def test_signup_nonexistent_activity(self):
        """Test signup for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email(self):
        """Test signup with an email already signed up"""
        # Try to sign up someone already in Programming Class
        response = client.post(
            "/activities/Programming Class/signup",
            params={"email": "emma@mergington.edu"}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_activity_full(self):
        """Test signup when activity is at capacity"""
        # First, get a full activity (if any)
        response = client.get("/activities")
        activities = response.json()
        
        # Find an activity that's close to full and fill it up
        for activity_name, activity_data in activities.items():
            if len(activity_data["participants"]) < activity_data["max_participants"]:
                # Fill up the activity
                for i in range(activity_data["max_participants"] - len(activity_data["participants"])):
                    client.post(
                        f"/activities/{activity_name}/signup",
                        params={"email": f"student{i}@test.edu"}
                    )
                
                # Now try to sign up when full
                response = client.post(
                    f"/activities/{activity_name}/signup",
                    params={"email": "overfull@test.edu"}
                )
                assert response.status_code == 400
                assert "full" in response.json()["detail"]
                break


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/participants endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        # First sign up
        client.post(
            "/activities/Tennis Club/signup",
            params={"email": "student@test.edu"}
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Tennis Club/participants",
            params={"email": "student@test.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Removed" in data["message"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistration from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Activity/participants",
            params={"email": "student@test.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_participant_not_found(self):
        """Test unregistration when participant is not in the activity"""
        response = client.delete(
            "/activities/Chess Club/participants",
            params={"email": "notinactivity@test.edu"}
        )
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]
