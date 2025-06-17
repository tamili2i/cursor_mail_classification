import pytest
import asyncio
import concurrent.futures
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import patch, MagicMock
import time
import string
import random
import re

from app.main import app
from app.core.config import settings
from app.services.user import create_user, get_user_by_email
from app.schemas.user import UserCreate

client = TestClient(app)

class TestCreateUserEdgeCases:
    """Test cases focusing on edge cases and security vulnerabilities for user creation"""

    @pytest.fixture
    def valid_user_data(self):
        return {
            "email": "test@example.com",
            "username": "testuser",
            "password": "Test@123",
            "full_name": "Test User"
        }

    def test_empty_inputs(self, db: Session):
        """Test various empty input scenarios"""
        test_cases = [
            {},  # Empty object
            {"email": "", "username": "", "password": "", "full_name": ""},  # Empty strings
            {"email": None, "username": None, "password": None, "full_name": None},  # None values
            {"email": "test@example.com"},  # Missing required fields
            {"username": "testuser"},  # Missing required fields
            {"password": "Test@123"},  # Missing required fields
        ]

        for test_data in test_cases:
            response = client.post(f"{settings.API_V1_STR}/users/", json=test_data)
            assert response.status_code in [422, 400]  # Validation error or bad request

    def test_special_characters(self, db: Session):
        """Test input with special characters and Unicode"""
        test_cases = [
            {
                "email": "test!@#$%^&*()@example.com",
                "username": "test!@#$%^&*()",
                "password": "Test!@#$%^&*()",
                "full_name": "Test User!@#$%^&*()"
            },
            {
                "email": "test@example.com",
                "username": "测试用户",
                "password": "Test@123",
                "full_name": "测试用户"
            },
            {
                "email": "test@example.com",
                "username": "test<script>alert('xss')</script>",
                "password": "Test@123",
                "full_name": "Test User"
            },
            {
                "email": "test@example.com",
                "username": "test' OR '1'='1",
                "password": "Test@123",
                "full_name": "Test User"
            }
        ]

        for test_data in test_cases:
            response = client.post(f"{settings.API_V1_STR}/users/", json=test_data)
            assert response.status_code in [200, 422]  # Either success or validation error

    def test_extreme_lengths(self, db: Session):
        """Test extremely long and short inputs"""
        # Generate extremely long strings
        long_string = "a" * 1000
        test_cases = [
            {
                "email": f"{long_string}@example.com",
                "username": long_string,
                "password": long_string,
                "full_name": long_string
            },
            {
                "email": "a@b.c",  # Minimal valid email
                "username": "a",  # Minimal username
                "password": "a",  # Minimal password
                "full_name": "a"  # Minimal full name
            }
        ]

        for test_data in test_cases:
            response = client.post(f"{settings.API_V1_STR}/users/", json=test_data)
            assert response.status_code in [200, 422]  # Either success or validation error

    def test_concurrent_creation(self, db: Session):
        """Test concurrent user creation to detect race conditions"""
        def create_user_concurrent(user_data):
            return client.post(f"{settings.API_V1_STR}/users/", json=user_data)

        # Create multiple users with the same email concurrently
        user_data = {
            "email": "concurrent@example.com",
            "username": "concurrent_user",
            "password": "Test@123",
            "full_name": "Concurrent User"
        }

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_user_concurrent, user_data) for _ in range(5)]
            responses = [future.result() for future in futures]

        # Only one creation should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count == 1

    def test_sql_injection_attempts(self, db: Session):
        """Test various SQL injection attempts"""
        injection_attempts = [
            {
                "email": "test@example.com",
                "username": "test' OR '1'='1",
                "password": "Test@123",
                "full_name": "Test User"
            },
            {
                "email": "test@example.com",
                "username": "test; DROP TABLE users;",
                "password": "Test@123",
                "full_name": "Test User"
            },
            {
                "email": "test@example.com",
                "username": "test' UNION SELECT * FROM users;",
                "password": "Test@123",
                "full_name": "Test User"
            }
        ]

        for attempt in injection_attempts:
            response = client.post(f"{settings.API_V1_STR}/users/", json=attempt)
            assert response.status_code in [200, 422]  # Should either succeed or fail validation

    def test_xss_attempts(self, db: Session):
        """Test various XSS attempts"""
        xss_attempts = [
            {
                "email": "test@example.com",
                "username": "<script>alert('xss')</script>",
                "password": "Test@123",
                "full_name": "<img src=x onerror=alert('xss')>"
            },
            {
                "email": "test@example.com",
                "username": "javascript:alert('xss')",
                "password": "Test@123",
                "full_name": "Test User"
            }
        ]

        for attempt in xss_attempts:
            response = client.post(f"{settings.API_V1_STR}/users/", json=attempt)
            assert response.status_code in [200, 422]  # Should either succeed or fail validation

    def test_password_strength(self, db: Session):
        """Test various password strength scenarios"""
        password_cases = [
            "a",  # Too short
            "a" * 1000,  # Too long
            "password",  # Common password
            "12345678",  # Numbers only
            "abcdefgh",  # Letters only
            "!@#$%^&*",  # Special chars only
            "Test@123",  # Valid password
            " " * 8,  # Spaces only
            "\t" * 8,  # Tabs only
            "null",  # Reserved word
            "undefined",  # Reserved word
            "None",  # Reserved word
        ]

        for password in password_cases:
            user_data = {
                "email": f"test_{password}@example.com",
                "username": f"test_{password}",
                "password": password,
                "full_name": "Test User"
            }
            response = client.post(f"{settings.API_V1_STR}/users/", json=user_data)
            assert response.status_code in [200, 422]  # Should either succeed or fail validation

    def test_email_validation(self, db: Session):
        """Test various email validation scenarios"""
        email_cases = [
            "test@example.com",  # Valid
            "test@example",  # Invalid TLD
            "@example.com",  # No local part
            "test@",  # No domain
            "test@.com",  # No domain name
            "test@example..com",  # Double dot
            "test@-example.com",  # Leading hyphen
            "test@example.com-",  # Trailing hyphen
            "test@example.com.",  # Trailing dot
            ".test@example.com",  # Leading dot
            "test..test@example.com",  # Double dot in local part
            "test@example.com@example.com",  # Multiple @
            "test@example.com ",  # Trailing space
            " test@example.com",  # Leading space
            "test @example.com",  # Space in local part
            "test@ example.com",  # Space in domain
            "test@example.com\n",  # Newline
            "test@example.com\t",  # Tab
            "test@example.com\r",  # Carriage return
        ]

        for email in email_cases:
            user_data = {
                "email": email,
                "username": "testuser",
                "password": "Test@123",
                "full_name": "Test User"
            }
            response = client.post(f"{settings.API_V1_STR}/users/", json=user_data)
            assert response.status_code in [200, 422]  # Should either succeed or fail validation

    def test_username_validation(self, db: Session):
        """Test various username validation scenarios"""
        username_cases = [
            "testuser",  # Valid
            "a",  # Too short
            "a" * 100,  # Too long
            "test user",  # Contains space
            "test@user",  # Contains special char
            "test\nuser",  # Contains newline
            "test\tuser",  # Contains tab
            "test\ruser",  # Contains carriage return
            "test/user",  # Contains forward slash
            "test\\user",  # Contains backslash
            "test.user",  # Contains dot
            "test..user",  # Contains double dot
            ".testuser",  # Starts with dot
            "testuser.",  # Ends with dot
            "test-user",  # Contains hyphen
            "-testuser",  # Starts with hyphen
            "testuser-",  # Ends with hyphen
        ]

        for username in username_cases:
            user_data = {
                "email": f"test_{username}@example.com",
                "username": username,
                "password": "Test@123",
                "full_name": "Test User"
            }
            response = client.post(f"{settings.API_V1_STR}/users/", json=user_data)
            assert response.status_code in [200, 422]  # Should either succeed or fail validation

    def test_network_timeout(self, db: Session):
        """Test behavior when database operations timeout"""
        with patch('app.services.user.create_user', side_effect=SQLAlchemyError):
            user_data = {
                "email": "test@example.com",
                "username": "testuser",
                "password": "Test@123",
                "full_name": "Test User"
            }
            response = client.post(f"{settings.API_V1_STR}/users/", json=user_data)
            assert response.status_code == 500  # Internal server error

    def test_memory_limits(self, db: Session):
        """Test behavior with extremely large payloads"""
        # Generate a payload that's larger than typical memory limits
        large_payload = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "Test@123",
            "full_name": "a" * (1024 * 1024)  # 1MB of data
        }
        
        response = client.post(f"{settings.API_V1_STR}/users/", json=large_payload)
        assert response.status_code in [413, 422]  # Payload too large or validation error

    def test_race_condition_duplicate_email(self, db: Session):
        """Test race condition with duplicate email creation"""
        def create_user_with_delay(user_data):
            time.sleep(0.1)  # Introduce delay
            return client.post(f"{settings.API_V1_STR}/users/", json=user_data)

        user_data = {
            "email": "race@example.com",
            "username": "race_user",
            "password": "Test@123",
            "full_name": "Race User"
        }

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(create_user_with_delay, user_data),
                executor.submit(create_user_with_delay, user_data)
            ]
            responses = [future.result() for future in futures]

        # Only one creation should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count == 1

    def test_invalid_data_types(self, db: Session):
        """Test various invalid data type scenarios"""
        invalid_cases = [
            {
                "email": 123,  # Number instead of string
                "username": True,  # Boolean instead of string
                "password": None,  # None instead of string
                "full_name": 123.45  # Float instead of string
            },
            {
                "email": ["test@example.com"],  # List instead of string
                "username": {"name": "test"},  # Dict instead of string
                "password": (),  # Tuple instead of string
                "full_name": set(["Test"])  # Set instead of string
            }
        ]

        for test_data in invalid_cases:
            response = client.post(f"{settings.API_V1_STR}/users/", json=test_data)
            assert response.status_code == 422  # Validation error 