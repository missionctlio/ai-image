# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from pytest_mock import mocker
from app.api.auth import router, validate_jwt_token, verify_google_oauth_token, generate_tokens
from app.db.database import get_db
from app.db.models import User
from fastapi import HTTPException
#from google.oauth2 import id_token
import google.oauth2
from huggingface_hub import login
import jwt

client = TestClient(router)

def test_verify_token_invalid_token(mocker):
    # Generate an invalid token
    token = "invalid-token"
    # Mock the verify_google_oauth_token function to raise an exception
    with mocker.patch("app.api.auth.verify_google_oauth_token", side_effect=Exception()):
        try:
            client.post("/token", json={"access_token": token})
            assert False, "Expected an exception to be raised"
        except HTTPException as e:
            assert e.status_code == 401

def test_verify_google_oauth_token_valid_token(mocker):
    # Generate a valid token
    token = "valid-token"
    id_info = {"exp": 1643723900, "email": "test-user@example.com"}
    # Mock the id_token.verify_oauth2_token function to return the id_info
    with mocker.patch("id_token.verify_oauth2_token", return_value=id_info):
        result = verify_google_oauth_token(token)
        assert result == id_info

def test_verify_google_oauth_token_expired_token(mocker):
    # Generate an expired token
    token = "expired-token"
    id_info = {"exp": 1643723900 - 1000, "email": "test-user@example.com"}
    # Mock the id_token.verify_oauth2_token function to return the id_info
    with mocker.patch("id_token.verify_oauth2_token", return_value=id_info):
        with pytest.raises(HTTPException):
            verify_google_oauth_token(token)

def test_verify_google_oauth_token_invalid_token(mocker):
    # Generate an invalid token
    token = "invalid-token"
    # Mock the id_token.verify_oauth2_token function to raise an exception
    with mocker.patch("id_token.verify_oauth2_token", side_effect=Exception()):
        with pytest.raises(HTTPException):
            verify_google_oauth_token(token)

def test_generate_tokens():
    # Generate tokens for a user
    user = User(email="test-user@example.com")
    access_token, refresh_token = generate_tokens(user)
    assert access_token is not None
    assert refresh_token is not None

def test_verify_token_valid_token(mocker):
    # Generate a valid token
    token = "valid-token"
    user_info = {"email": "test-user@example.com", "name": "Test User"}
    # Mock the verify_google_oauth_token function to return the user_info
    with mocker.patch("app.api.auth.verify_google_oauth_token", return_value=user_info):
        response = client.post("/token", json={"access_token": token})
        assert response.status_code == 200
        assert response.json()["userInfo"] == user_info

def test_verify_token_invalid_token(mocker):
    # Generate an invalid token
    token = "invalid-token"
    # Mock the verify_google_oauth_token function to raise an exception
    with mocker.patch("app.api.auth.verify_google_oauth_token", side_effect=Exception()):
        response = client.post("/token", json={"access_token": token})
        assert response.status_code == 401
