# tests/test_predict.py
import pytest
from django.urls import reverse
from career.models import CareerPrediction   # <-- replace myapp with your app name

# Load test cases
import json, os
here = os.path.dirname(__file__)
with open(os.path.join(here, "test_data.json"), "r", encoding="utf-8") as f:
    TEST_CASES = json.load(f)


@pytest.mark.django_db
@pytest.mark.parametrize("input_data", TEST_CASES)
def test_predict_and_save(api_client, input_data, django_user_model):
    """
    Test prediction API with multiple test cases.
    """
    # Create and login user (if API requires auth)
    user = django_user_model.objects.create_user(username="testuser", password="testpass")
    api_client.force_authenticate(user=user)

    url = "/api/predict/"   # or reverse("career-predict") if named in urls.py

    response = api_client.post(url, input_data, format="json")
    assert response.status_code == 200, f"status {response.status_code} body: {response.content!r}"

    json_resp = response.json()
    assert "career_paths" in json_resp and isinstance(json_resp["career_paths"], list)

    # Verify DB saved a CareerPrediction record linked to this user
    prediction = CareerPrediction.objects.filter(user=user).first()
    assert prediction is not None, "CareerPrediction not saved in DB"
    assert prediction.user_input["ug_course"] == input_data["ug_course"]
    if "ug_specialization" in input_data:
        assert prediction.user_input["ug_specialization"] == input_data["ug_specialization"]
