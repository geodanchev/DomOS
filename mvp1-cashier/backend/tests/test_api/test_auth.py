"""Tests for authentication API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.models.user import User, UserRole


class TestLogin:
    """Tests for POST /api/auth/login endpoint."""
    
    def test_login_success(self, client: TestClient, cashier_user: User):
        """Should return token for valid credentials."""
        response = client.post(
            "/api/auth/login",
            data={"username": "cecka", "password": "1234"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "cecka"
    
    def test_login_wrong_password(self, client: TestClient, cashier_user: User):
        """Should return 401 for wrong password."""
        response = client.post(
            "/api/auth/login",
            data={"username": "cecka", "password": "wrongpassword"},
        )
        
        assert response.status_code == 401
        assert "Грешно потребителско име или парола" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client: TestClient):
        """Should return 401 for non-existent user."""
        response = client.post(
            "/api/auth/login",
            data={"username": "nonexistent", "password": "anypassword"},
        )
        
        assert response.status_code == 401
    
    def test_login_inactive_user(self, client: TestClient, inactive_user: User):
        """Should return 403 for inactive user."""
        response = client.post(
            "/api/auth/login",
            data={"username": "inactive", "password": "pass123"},
        )
        
        assert response.status_code == 403
        assert "деактивиран" in response.json()["detail"]
    
    def test_login_empty_username(self, client: TestClient):
        """Should return 422 for empty username."""
        response = client.post(
            "/api/auth/login",
            data={"username": "", "password": "password"},
        )
        
        assert response.status_code == 422
    
    def test_login_empty_password(self, client: TestClient, cashier_user: User):
        """Should return 422 for empty password (validation error)."""
        response = client.post(
            "/api/auth/login",
            data={"username": "cecka", "password": ""},
        )
        
        # FastAPI's OAuth2PasswordRequestForm validates that password is not empty
        assert response.status_code == 422
    
    def test_login_returns_user_info(self, client: TestClient, admin_user: User):
        """Should return user info in response."""
        response = client.post(
            "/api/auth/login",
            data={"username": "test_admin", "password": "admin123"},
        )
        
        assert response.status_code == 200
        user = response.json()["user"]
        assert user["username"] == "test_admin"
        assert user["display_name"] == "Test Admin"
        assert user["role"] == "admin"
        assert "password_hash" not in user


class TestRegister:
    """Tests for POST /api/auth/register endpoint.
    
    SECURITY: As of security fix 2026-06-25, /register requires admin authentication.
    """
    
    def test_register_requires_authentication(self, client: TestClient, test_db):
        """Should return 401 when not authenticated."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "password": "newpass123",
                "display_name": "New User",
                "role": "viewer",
            },
        )
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_register_requires_admin(self, client: TestClient, cashier_headers: dict):
        """Should return 403 when authenticated as non-admin."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "password": "newpass123",
                "display_name": "New User",
                "role": "viewer",
            },
            headers=cashier_headers,
        )
        
        assert response.status_code == 403
        assert "администратори" in response.json()["detail"].lower()
    
    def test_register_success(self, client: TestClient, admin_headers: dict):
        """Should create new user successfully when authenticated as admin."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "password": "newpass123",
                "display_name": "New User",
                "role": "viewer",
            },
            headers=admin_headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["display_name"] == "New User"
        assert data["role"] == "viewer"
        assert "password_hash" not in data
    
    def test_register_duplicate_username(self, client: TestClient, cashier_user: User, admin_headers: dict):
        """Should return 400 for duplicate username."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "cecka",  # Already exists
                "password": "anotherpass",
                "display_name": "Another Cecka",
            },
            headers=admin_headers,
        )
        
        assert response.status_code == 400
        assert "вече съществува" in response.json()["detail"]
    
    def test_register_default_role(self, client: TestClient, admin_headers: dict):
        """Should use CASHIER as default role."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "defaultrole",
                "password": "password123",
                "display_name": "Default Role User",
            },
            headers=admin_headers,
        )
        
        assert response.status_code == 201
        assert response.json()["role"] == "cashier"
    
    def test_register_admin_role(self, client: TestClient, admin_headers: dict):
        """Should allow creating admin user."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newadmin",
                "password": "adminpass",
                "display_name": "New Admin",
                "role": "admin",
            },
            headers=admin_headers,
        )
        
        assert response.status_code == 201
        assert response.json()["role"] == "admin"
    
    def test_register_missing_username(self, client: TestClient, admin_headers: dict):
        """Should return 422 for missing username."""
        response = client.post(
            "/api/auth/register",
            json={
                "password": "password",
                "display_name": "No Username",
            },
            headers=admin_headers,
        )
        
        assert response.status_code == 422
    
    def test_register_missing_password(self, client: TestClient, admin_headers: dict):
        """Should return 422 for missing password."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "nopass",
                "display_name": "No Password",
            },
            headers=admin_headers,
        )
        
        assert response.status_code == 422
    
    def test_register_bulgarian_display_name(self, client: TestClient, admin_headers: dict):
        """Should handle Bulgarian characters in display name."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "bulgarian",
                "password": "password123",
                "display_name": "Георги Петров",
            },
            headers=admin_headers,
        )
        
        assert response.status_code == 201
        assert response.json()["display_name"] == "Георги Петров"


class TestMe:
    """Tests for GET /api/auth/me endpoint."""
    
    def test_me_authenticated(self, client: TestClient, cashier_headers: dict):
        """Should return current user info."""
        response = client.get("/api/auth/me", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "cecka"
        assert data["display_name"] == "Цецка"
        assert data["role"] == "cashier"
    
    def test_me_unauthenticated(self, client: TestClient):
        """Should return 401 without token."""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    def test_me_invalid_token(self, client: TestClient):
        """Should return 401 with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        
        assert response.status_code == 401
    
    def test_me_admin_user(self, client: TestClient, admin_headers: dict):
        """Should return admin user info correctly."""
        response = client.get("/api/auth/me", headers=admin_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
    
    def test_me_no_password_in_response(self, client: TestClient, cashier_headers: dict):
        """Should not include password hash in response."""
        response = client.get("/api/auth/me", headers=cashier_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "password" not in data
        assert "password_hash" not in data


class TestAuthFlow:
    """Integration tests for complete auth flow."""
    
    def test_register_then_login(self, client: TestClient, admin_headers: dict):
        """Should be able to register (as admin) and then login."""
        # Register (requires admin authentication)
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "flowtest",
                "password": "flowpass123",
                "display_name": "Flow Test User",
            },
            headers=admin_headers,
        )
        assert register_response.status_code == 201
        
        # Login
        login_response = client.post(
            "/api/auth/login",
            data={"username": "flowtest", "password": "flowpass123"},
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
    
    def test_login_then_me(self, client: TestClient, cashier_user: User):
        """Should be able to login and then access /me."""
        # Login
        login_response = client.post(
            "/api/auth/login",
            data={"username": "cecka", "password": "1234"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Access /me
        me_response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_response.status_code == 200
        assert me_response.json()["username"] == "cecka"
