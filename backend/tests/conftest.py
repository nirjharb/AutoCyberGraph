"""Test environment: relax rate limits before the app is imported."""
import os

os.environ.setdefault("RATE_LIMIT_AUTH", "10000/minute")
os.environ.setdefault("RATE_LIMIT_ADVISOR", "10000/minute")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-only-0123456789")
