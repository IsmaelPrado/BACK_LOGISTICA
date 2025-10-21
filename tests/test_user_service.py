# tests/test_user_service.py
import asyncio
from datetime import datetime
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

# Pruebas para get_user_by_email
def test_get_user_by_email_exists():
    fake_user = FakeUser("ismael", "hashedpass")
    fake_user.correo_electronico = "ismael@example.com"
    db = FakeDB(user=fake_user)
    service = UserService(db)

    user = asyncio.run(service.get_user_by_email("ismael@example.com"))
    assert user is not None
    assert user.correo_electronico == "ismael@example.com"

def test_get_user_by_email_not_exist():
    db = FakeDB(user=None)
    service = UserService(db)

    user = asyncio.run(service.get_user_by_email("noexist@example.com"))
    assert user is None


# Pruebas para get_user_by_username
def test_get_user_by_username_exists():
    fake_user = FakeUser("ismael", "hashedpass")
    fake_user.nombre_usuario = "ismael"
    db = FakeDB(user=fake_user)
    service = UserService(db)

    user = asyncio.run(service.get_user_by_username("ismael"))
    assert user is not None
    assert user.nombre_usuario == "ismael"

def test_get_user_by_username_not_exist():
    db = FakeDB(user=None)
    service = UserService(db)

    user = asyncio.run(service.get_user_by_username("noexist"))
    assert user is None


# Pruebas para get_user_by_id
def test_get_user_by_id_exists():
    fake_user = FakeUser("ismael", "hashedpass")
    fake_user.id_usuario = 1
    db = FakeDB(user=fake_user)
    service = UserService(db)

    user = asyncio.run(service.get_user_by_id(1))
    assert user is not None
    assert user.id_usuario == 1

def test_get_user_by_id_not_exist():
    db = FakeDB(user=None)
    service = UserService(db)

    user = asyncio.run(service.get_user_by_id(999))
    assert user is None


# Fake User
class FakeUserPasswordReset:
    def __init__(self, user_id):
        self.id_usuario = user_id

class FakePasswordReset:
    def __init__(self, user_id, reset_token, expires_at):
        self.user_id = user_id
        self.reset_token = reset_token
        self.expires_at = expires_at


class FakeDBPasswordReset:
    def __init__(self):
        self.data = []           # Para almacenar PasswordReset
        self.committed = False
        self.refreshed = False

    async def execute(self, query):
        # Eliminamos resets previos de todos los PasswordReset que tengan user_id igual a user.id_usuario
        if hasattr(query, "user_id"):
            user_id = query.user_id
        else:
            # En los tests, usamos siempre db.data[0].user_id si existe
            if self.data:
                user_id = self.data[0].user_id
            else:
                return None
        self.data = [r for r in self.data if r.user_id != user_id]
        return None

    def add(self, obj):
        self.data.append(obj)

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        self.refreshed = True

@pytest.mark.asyncio
async def test_create_password_reset_creates_reset(monkeypatch):
    db = FakeDBPasswordReset()
    user = FakeUserPasswordReset(1)
    service = UserService(db)

    reset = await service.create_password_reset(user)

    assert reset.user_id == user.id_usuario
    assert isinstance(reset.reset_token, str)
    assert len(reset.reset_token) > 20  # token suficientemente largo
    assert reset.expires_at > datetime.utcnow()
    assert db.committed is True
    assert db.refreshed is True

@pytest.mark.asyncio
async def test_create_password_reset_removes_old(monkeypatch):
    db = FakeDBPasswordReset()
    user = FakeUserPasswordReset(1)

    # Agregamos un reset previo
    old_reset = FakePasswordReset(user_id=1, reset_token="oldtoken", expires_at=datetime.utcnow())
    db.data.append(old_reset)

    service = UserService(db)
    reset = await service.create_password_reset(user)

    # Debe eliminar el anterior
    assert all(r.user_id != 1 or r.reset_token != "oldtoken" for r in db.data)
    # Solo queda el nuevo reset
    assert any(r.reset_token == reset.reset_token for r in db.data)

@pytest.mark.asyncio
async def test_create_password_reset_with_custom_expire():
    db = FakeDBPasswordReset()
    user = FakeUserPasswordReset(1)
    service = UserService(db)

    reset = await service.create_password_reset(user, expire_minutes=5)
    assert abs((reset.expires_at - datetime.utcnow()).total_seconds() - 5*60) < 5  # margen de 5 seg

@pytest.mark.asyncio
async def test_create_password_reset_user_none():
    db = FakeDBPasswordReset()
    service = UserService(db)

    with pytest.raises(AttributeError):
        await service.create_password_reset(None)