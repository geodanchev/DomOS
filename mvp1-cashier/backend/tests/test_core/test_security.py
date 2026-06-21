"""Tests for security utilities - password hashing and JWT tokens."""

import pytest
from datetime import timedelta
import time

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
)
from app.core.config import settings


class TestPasswordHashing:
    """Tests for password hashing functions."""
    
    def test_password_hash_not_plaintext(self):
        """Hash should not equal the original password."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > len(password)
    
    def test_password_hash_is_bcrypt_format(self):
        """Hash should be in bcrypt format."""
        password = "testpassword"
        hashed = get_password_hash(password)
        
        # bcrypt hashes start with $2b$ or $2a$
        assert hashed.startswith("$2"), f"Expected bcrypt hash, got: {hashed[:10]}..."
    
    def test_password_verify_correct(self):
        """verify_password should return True for correct password."""
        password = "correctpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verify_incorrect(self):
        """verify_password should return False for wrong password."""
        password = "correctpassword"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_password_verify_empty_password(self):
        """verify_password should return False for empty password."""
        password = "somepassword"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False
    
    def test_same_password_different_hashes(self):
        """Same password should produce different hashes (due to salt)."""
        password = "testpassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_unicode_password(self):
        """Should handle Bulgarian/unicode passwords."""
        password = "парола123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False


class TestJWTTokens:
    """Tests for JWT token functions."""
    
    def test_jwt_create_decode_roundtrip(self):
        """Token creation and decoding should preserve data."""
        data = {"sub": 123, "role": "admin"}
        token = create_access_token(data=data)
        
        payload = decode_token(token)
        
        assert payload is not None
        # Note: sub is converted to string per JWT spec
        assert payload["sub"] == "123"
        assert payload["role"] == "admin"
    
    def test_jwt_contains_expiry(self):
        """Token should contain exp claim."""
        data = {"sub": 1}
        token = create_access_token(data=data)
        
        payload = decode_token(token)
        
        assert payload is not None
        assert "exp" in payload
    
    def test_jwt_custom_expiry(self):
        """Token should respect custom expiry delta."""
        data = {"sub": 1}
        # Very short expiry
        token = create_access_token(
            data=data,
            expires_delta=timedelta(seconds=1)
        )
        
        # Should be valid immediately
        payload = decode_token(token)
        assert payload is not None
        
        # Wait for expiry
        time.sleep(2)
        
        # Should be expired now
        expired_payload = decode_token(token)
        assert expired_payload is None
    
    def test_jwt_invalid_token(self):
        """Invalid token should return None."""
        invalid_tokens = [
            "not.a.valid.token",
            "completely_invalid",
            "",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
        ]
        
        for token in invalid_tokens:
            assert decode_token(token) is None, f"Token should be invalid: {token}"
    
    def test_jwt_wrong_secret(self):
        """Token signed with wrong secret should not decode."""
        from jose import jwt
        
        data = {"sub": 1}
        wrong_secret = "wrong-secret-key"
        
        # Create token with wrong secret
        token = jwt.encode(data, wrong_secret, algorithm=settings.ALGORITHM)
        
        # Should not decode with our secret
        payload = decode_token(token)
        assert payload is None
    
    def test_jwt_user_id_in_sub(self):
        """Standard pattern: user ID stored in 'sub' claim."""
        user_id = 42
        token = create_access_token(data={"sub": user_id})
        
        payload = decode_token(token)
        
        # sub is converted to string per JWT spec
        assert payload["sub"] == str(user_id)
    
    def test_jwt_preserves_additional_claims(self):
        """Additional claims should be preserved."""
        data = {
            "sub": 1,
            "role": "cashier",
            "name": "Цецка",
            "building_id": 5,
        }
        token = create_access_token(data=data)
        
        payload = decode_token(token)
        
        # sub is converted to string per JWT spec
        assert payload["sub"] == "1"
        assert payload["role"] == "cashier"
        assert payload["name"] == "Цецка"
        assert payload["building_id"] == 5


class TestSecurityIntegration:
    """Integration tests combining password and JWT."""
    
    def test_full_auth_flow_simulation(self):
        """Simulate complete auth flow: hash password, verify, create token."""
        # User registration - hash password
        password = "userpassword123"
        password_hash = get_password_hash(password)
        user_id = 42
        
        # User login - verify password
        assert verify_password(password, password_hash) is True
        
        # Create access token
        token = create_access_token(data={"sub": user_id})
        
        # Later request - decode token
        payload = decode_token(token)
        # sub is converted to string per JWT spec
        assert payload["sub"] == str(user_id)
