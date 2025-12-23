import asyncio
import pytest

from fastapi.testclient import TestClient

from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from main import app
from src.api.deps import get_session
from src.models import Base
from src.core.security import create_access_token


client = TestClient(app)


def test_app_start():
    response = client.get("/")
    assert response.status_code == 200


engine = create_async_engine(url="sqlite+aiosqlite:///:memory:", poolclass=StaticPool, echo=True)
AsyncSessionMaker = async_sessionmaker(bind=engine, expire_on_commit=False)


async def init_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


asyncio.run(init_schema())


async def override_get_session():
    async with AsyncSessionMaker() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


def test_register_user():
    response = client.post("/auth/register", json={ "username": "TestUser1", "password": "NotLongPassword" })
    assert response.is_success


@pytest.mark.parametrize("login, password, expected_status_code", [
    ("login123", "password123", 401),
    ("123", "123", 422),
    ("", "", 422),
    ("TestUser1", "NotLongPassword", 200)
])
def test_login(login, password, expected_status_code):
    response = client.post("/auth/login", json={ "username": login, "password": password })
    assert response.status_code == expected_status_code


@pytest.mark.parametrize("jwt_token, expected_status_code", [
    (None, 401),
    ("", 401),
    ("123123", 401),
    ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6IkludmFsaWRMb2dpbiJ9.y5elFG4NLlfPM77_HiodzPu8-pdIb4opg1tBVQH06po", 401),
    ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6IlRlc3RVc2VyMSIsImV4cCI6MTkyMzczODMzN30.ywRPTwDlDbWGb_aTFzb9TqVe69Llr06Ve0Yh66ndX-I", 200)
])
def test_create_session(jwt_token, expected_status_code):
    response = client.post("/chat/session", headers={ "Authorization": f"Bearer {jwt_token}"})
    assert response.status_code == expected_status_code


@pytest.fixture
def jwt_token():
    token = create_access_token(data={ "username": "TestUser1" })
    return token


@pytest.fixture
def session_id():
    jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6IlRlc3RVc2VyMSIsImV4cCI6MTkyMzczODMzN30.ywRPTwDlDbWGb_aTFzb9TqVe69Llr06Ve0Yh66ndX-I"
    response = client.post("/chat/session", headers={ "Authorization": f"Bearer {jwt_token}"})
    data = response.json()
    session_id = data.get("id")
    return session_id


@pytest.mark.parametrize("sender_type, message_text, expected_status_code", [
    (None, None, 422),
    ("other", None, 422),
    ("other", "Message", 422),
    ("user", "Привет", 201),
    ("bot", "Привет", 201)
])
def test_send_message(jwt_token, session_id, sender_type, message_text, expected_status_code):
    response = client.post("/chat/message",
                           headers={ "Authorization": f"Bearer {jwt_token}" },
                           json={ "session_id": session_id, "sender_type": sender_type, "text": message_text })
    assert response.status_code == expected_status_code


@pytest.mark.parametrize("message_text, expected_answer", [
    ("ПриВЕТ", "Привет! Я бот, который был создан для ресторана VResta. Если хотите узнать все команды, напиши <b> помощь </b> или <b> команды </b>."),
    ("ПОКА", "До свидания!")
])
def test_get_bot_answer(jwt_token, session_id, message_text, expected_answer):
    response = client.post("/chat/message",
                           headers={ "Authorization": f"Bearer {jwt_token}" },
                           json={ "session_id": session_id, "sender_type": "user", "text": message_text })
    answer = response.json().get("answer")
    assert answer == expected_answer


def test_get_history_messages(jwt_token, session_id):
    response = client.get(f"/chat/history/{session_id}", headers={ "Authorization": f"Bearer {jwt_token}"})
    assert response.status_code == 200

    history = response.json()
    assert isinstance(history, list)
    assert history == []

    client.post("/chat/message", headers={ "Authorization": f"Bearer {jwt_token}" }, json={ "session_id": session_id, "sender_type": "user", "text": "Привет" })

    response = client.get(f"/chat/history/{session_id}", headers={ "Authorization": f"Bearer {jwt_token}"})
    history = response.json()
    assert isinstance(history, list)
    assert history[0].get("text") == "Привет"
    assert history[1].get("text") == "Привет! Я бот, который был создан для ресторана VResta. Если хотите узнать все команды, напиши <b> помощь </b> или <b> команды </b>."
