import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


def signup_endpoint(activity_name: str) -> str:
    return f"/activities/{quote(activity_name, safe='')}/signup"


@pytest.fixture(autouse=True)
def reset_activities_state():
    original_state = copy.deepcopy(activities)

    yield

    activities.clear()
    activities.update(copy.deepcopy(original_state))


def test_get_activities_returns_expected_structure():
    # Arrange
    expected_keys = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, dict)
    assert len(payload) > 0

    first_activity = next(iter(payload.values()))
    assert expected_keys.issubset(first_activity.keys())


def test_signup_success_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "aaa-signup-success@mergington.edu"

    # Act
    response = client.post(signup_endpoint(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}

    activities_response = client.get("/activities")
    participants = activities_response.json()[activity_name]["participants"]
    assert email in participants


def test_signup_duplicate_returns_400():
    # Arrange
    activity_name = "Chess Club"
    email = "aaa-signup-duplicate@mergington.edu"
    client.post(signup_endpoint(activity_name), params={"email": email})

    # Act
    response = client.post(signup_endpoint(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_activity_not_found_returns_404():
    # Arrange
    activity_name = "Activity That Does Not Exist"
    email = "aaa-signup-not-found@mergington.edu"

    # Act
    response = client.post(signup_endpoint(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_success_removes_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "aaa-delete-success@mergington.edu"
    client.post(signup_endpoint(activity_name), params={"email": email})

    # Act
    response = client.delete(signup_endpoint(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}

    activities_response = client.get("/activities")
    participants = activities_response.json()[activity_name]["participants"]
    assert email not in participants


def test_unregister_activity_not_found_returns_404():
    # Arrange
    activity_name = "Activity That Does Not Exist"
    email = "aaa-delete-not-found@mergington.edu"

    # Act
    response = client.delete(signup_endpoint(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_not_found_returns_404():
    # Arrange
    activity_name = "Chess Club"
    email = "aaa-delete-missing@mergington.edu"

    # Act
    response = client.delete(signup_endpoint(activity_name), params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
