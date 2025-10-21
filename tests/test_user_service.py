# tests/test_user_service.py
import asyncio
import pytest
from app.services.user_service import UserService

# Fake user y DB para pruebas
class FakeUser:
    def __init__(self, username, password):
        self.nombre_usuario = username
        self.contrasena = password

class FakeDB:
    def __init__(self, user=None):
        self.user = user

    async def execute(self, query):
        class Result:
            def scalars(inner_self):
                class Inner:
                    def first(inner_self):
                        return self.user
                return Inner()
        return Result()

# Pruebas unitarias
def test_authenticate_user_success(monkeypatch):
    fake_user = FakeUser("ismael", "hashedpass")
    db = FakeDB(user=fake_user)
    monkeypatch.setattr("app.services.user_service.verify_password", lambda plain, hashed: True)
    service = UserService(db)
    user = asyncio.run(service.authenticate_user("ismael", "1234"))
    assert user.nombre_usuario == "ismael"

def test_authenticate_user_not_exist():
    db = FakeDB(user=None)
    service = UserService(db)
    with pytest.raises(ValueError, match="Usuario no existe"):
        asyncio.run(service.authenticate_user("noexist", "1234"))

def test_authenticate_user_wrong_password(monkeypatch):
    fake_user = FakeUser("ismael", "hashedpass")
    db = FakeDB(user=fake_user)
    monkeypatch.setattr("app.services.user_service.verify_password", lambda plain, hashed: False)
    service = UserService(db)
    with pytest.raises(ValueError, match="Contraseña incorrecta"):
        asyncio.run(service.authenticate_user("ismael", "wrong"))