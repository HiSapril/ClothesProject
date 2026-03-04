import pytest
import os

# Set environment variables for tests BEFORE importing app components
os.environ["DEBUG"] = "True"
os.environ["SECRET_KEY"] = "test_secret_key_123"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, get_db
from app.core.config import settings

# --- Test Database Setup (In-Memory SQLite) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create tables once for the test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    """Provide a clean database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    """Provide a TestClient that uses the test database and mocks rate limiting."""
    try:
        from fastapi_limiter.depends import RateLimiter
    except (ImportError, TypeError):
        # Use a dummy if library is broken
        def RateLimiter(*args, **kwargs):
            async def dummy_limiter(): return True
            return dummy_limiter
    
    async def mock_limiter():
        return True

    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[RateLimiter] = mock_limiter
    
    with TestClient(app) as c:
        yield c
        
    app.dependency_overrides.clear()

# --- Shared Mocks ---
@pytest.fixture(autouse=True)
def mock_external_calls(mocker):
    """Mock Redis, Weather, and Calendar by default to avoid network calls."""
    from app.main import FastApiLimiter
    if FastApiLimiter:
        mocker.patch("app.main.FastApiLimiter.init", return_value=None)
    mocker.patch("redis.asyncio.from_url", return_value=mocker.Mock())
    mocker.patch("app.services.weather_service.weather_service.get_current_weather", return_value={"temp": 25, "condition": "Clear"})
    mocker.patch("app.services.calendar_service.calendar_service.get_upcoming_events", return_value=([], None))
