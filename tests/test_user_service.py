# tests/test_user_service.py
import asyncio
from sqlite3 import IntegrityError
from unittest.mock import AsyncMock

from pydantic import ValidationError
from app.models.user import Usuario
from app.schemas.auth import UsuarioRequest
from datetime import datetime, timedelta
import pytest
from app.services.user_service import UserService
from sqlalchemy.exc import IntegrityError


# Fake user y DB para pruebas
class FakeUser:
    def __init__(self, username, password):
        self.nombre_usuario = username
        self.contrasena = password

class FakeDBAuth:
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
    db = FakeDBAuth(user=fake_user)
    monkeypatch.setattr("app.services.user_service.verify_password", lambda plain, hashed: True)
    service = UserService(db)
    user = asyncio.run(service.authenticate_user("ismael", "1234"))
    assert user.nombre_usuario == "ismael"

def test_authenticate_user_not_exist():
    db = FakeDBAuth(user=None)
    service = UserService(db)
    with pytest.raises(ValueError, match="Usuario no existe"):
        asyncio.run(service.authenticate_user("noexist", "1234"))

def test_authenticate_user_wrong_password(monkeypatch):
    fake_user = FakeUser("ismael", "hashedpass")
    db = FakeDBAuth(user=fake_user)
    monkeypatch.setattr("app.services.user_service.verify_password", lambda plain, hashed: False)
    service = UserService(db)
    with pytest.raises(ValueError, match="Contraseña incorrecta"):
        asyncio.run(service.authenticate_user("ismael", "wrong"))

# Pruebas para get_user_by_email
def test_get_user_by_email_exists():
    fake_user = FakeUser("ismael", "hashedpass")
    fake_user.correo_electronico = "ismael@example.com"
    db = FakeDBAuth(user=fake_user)
    service = UserService(db)

    user = asyncio.run(service.get_user_by_email("ismael@example.com"))
    assert user is not None
    assert user.correo_electronico == "ismael@example.com"

def test_get_user_by_email_not_exist():
    db = FakeDBAuth(user=None)
    service = UserService(db)

    user = asyncio.run(service.get_user_by_email("noexist@example.com"))
    assert user is None


# Pruebas para get_user_by_username
def test_get_user_by_username_exists():
    fake_user = FakeUser("ismael", "hashedpass")
    fake_user.nombre_usuario = "ismael"
    db = FakeDBAuth(user=fake_user)
    service = UserService(db)

    user = asyncio.run(service.get_user_by_username("ismael"))
    assert user is not None
    assert user.nombre_usuario == "ismael"

def test_get_user_by_username_not_exist():
    db = FakeDBAuth(user=None)
    service = UserService(db)

    user = asyncio.run(service.get_user_by_username("noexist"))
    assert user is None


# Pruebas para get_user_by_id
def test_get_user_by_id_exists():
    fake_user = FakeUser("ismael", "hashedpass")
    fake_user.id_usuario = 1
    db = FakeDBAuth(user=fake_user)
    service = UserService(db)

    user = asyncio.run(service.get_user_by_id(1))
    assert user is not None
    assert user.id_usuario == 1

def test_get_user_by_id_not_exist():
    db = FakeDBAuth(user=None)
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

class FakeDBVerify:
    def __init__(self, resets=None, raise_error=False):
        self.resets = resets or []
        self.raise_error = raise_error

    async def execute(self, query):
        if self.raise_error:
            raise Exception("DB Error")
        class Result:
            def scalars(inner_self):
                class Inner:
                    def first(inner_self):
                        token = getattr(query, "token", None)
                        if not token:
                            return None
                        for r in self.resets:
                            if r.reset_token == token and r.expires_at > datetime.utcnow():
                                return r
                        return None
                return Inner()
        return Result()

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
  
  
      
# ------------------------
# Fake DB asíncrona
# ------------------------
class FakeDBCreate:
    def __init__(self):
        self.added = None
        self.flushed = False
        self.refreshed = False

    def begin(self):
        class FakeTransaction:
            async def __aenter__(inner_self):
                return self
            async def __aexit__(inner_self, exc_type, exc, tb):
                pass
        return FakeTransaction()

    def add(self, obj):
        self.added = obj

    async def flush(self):
        if hasattr(self, "raise_integrity") and self.raise_integrity:
            # Simula exactamente la excepción que espera el service
            raise IntegrityError("Mock", None, Exception("correo_electronico"))
        self.flushed = True


    async def refresh(self, obj):
        self.refreshed = True


# ------------------------
# Casos de prueba
# ------------------------
@pytest.mark.asyncio
async def test_create_user_success(monkeypatch):
    """✅ Caso exitoso"""
    db = FakeDBCreate()
    service = UserService(db)

    # Mock del hash de contraseña
    monkeypatch.setattr("app.services.user_service.hash_password_async", AsyncMock(return_value="hashedpass"))
    # Mock pyotp
    monkeypatch.setattr("app.services.user_service.pyotp.random_base32", lambda: "mock_secret")

    user_data = UsuarioRequest(
        nombre_usuario="manuel",
        contrasena="Password123!",
        confirmar_contrasena="Password123!",
        correo_electronico="manuel@example.com",
        rol="admin"
    )

    user = await service.create_user(user_data)
    assert isinstance(user, Usuario)
    assert user.contrasena == "hashedpass"
    assert user.secret_2fa == "mock_secret"


@pytest.mark.asyncio
async def test_create_user_short_username():
    """❌ Usuario con nombre corto"""
    db = FakeDBCreate()
    service = UserService(db)
    data = UsuarioRequest(
        nombre_usuario="ab",
        contrasena="Password123!",
        confirmar_contrasena="Password123!",
        correo_electronico="a@b.com",
        rol="admin"
    )
    with pytest.raises(ValueError, match="al menos 3 caracteres"):
        await service.create_user(data)


@pytest.mark.asyncio
async def test_create_user_passwords_not_match():
    """❌ Contraseñas no coinciden"""
    db = FakeDBCreate()
    service = UserService(db)

    with pytest.raises(ValidationError, match="Las contraseñas no coinciden"):
        UsuarioRequest(
            nombre_usuario="manuel",
            contrasena="Password123!",
            confirmar_contrasena="Password123",
            correo_electronico="a@b.com",
            rol="admin"
        )

@pytest.mark.asyncio
async def test_create_user_weak_password():
    """❌ Contraseña sin carácter especial"""
    db = FakeDBCreate()
    service = UserService(db)

    with pytest.raises(ValidationError, match="mayúscula, minúscula, número y carácter especial"):
        UsuarioRequest(
            nombre_usuario="manuel",
            contrasena="Password123",
            confirmar_contrasena="Password123",
            correo_electronico="a@b.com",
            rol="admin"
        )

@pytest.mark.asyncio
async def test_create_user_integrity_error(monkeypatch):
    """❌ Duplicado por correo"""
    db = FakeDBCreate()
    db.raise_integrity = True
    service = UserService(db)

    monkeypatch.setattr("app.services.user_service.hash_password_async", AsyncMock(return_value="hashedpass"))
    monkeypatch.setattr("app.services.user_service.pyotp.random_base32", lambda: "mock_secret")

    data = UsuarioRequest(
        nombre_usuario="manuel",
        contrasena="Password123!",
        confirmar_contrasena="Password123!",
        correo_electronico="manuel@example.com",
        rol="admin"
    )

    with pytest.raises(ValueError, match="correo electrónico ya está registrado"):
        await service.create_user(data)


@pytest.mark.asyncio
async def test_verify_password_reset_valid():
    reset = FakePasswordReset(user_id=1, reset_token="tok1", expires_at=datetime.utcnow() + timedelta(minutes=10))
    db = FakeDBVerify(resets=[reset])
    service = UserService(db)
    
    result = await service.verify_password_reset("tok1")
    assert result == reset

@pytest.mark.asyncio
async def test_verify_password_reset_not_exist():
    db = FakeDBVerify(resets=[])
    service = UserService(db)
    
    result = await service.verify_password_reset("noexist")
    assert result is None

@pytest.mark.asyncio
async def test_verify_password_reset_expired():
    reset = FakePasswordReset(user_id=1, reset_token="tok2", expires_at=datetime.utcnow() - timedelta(minutes=1))
    db = FakeDBVerify(resets=[reset])
    service = UserService(db)
    
    result = await service.verify_password_reset("tok2")
    assert result is None

@pytest.mark.asyncio
async def test_verify_password_reset_token_none():
    reset = FakePasswordReset(user_id=1, reset_token="tok3", expires_at=datetime.utcnow() + timedelta(minutes=10))
    db = FakeDBVerify(resets=[reset])
    service = UserService(db)
    
    result = await service.verify_password_reset(None)
    assert result is None

@pytest.mark.asyncio
async def test_verify_password_reset_token_empty():
    reset = FakePasswordReset(user_id=1, reset_token="tok4", expires_at=datetime.utcnow() + timedelta(minutes=10))
    db = FakeDBVerify(resets=[reset])
    service = UserService(db)
    
    result = await service.verify_password_reset("")
    assert result is None

@pytest.mark.asyncio
async def test_verify_password_reset_multiple_same_token():
    reset1 = FakePasswordReset(user_id=1, reset_token="tok5", expires_at=datetime.utcnow() + timedelta(minutes=10))
    reset2 = FakePasswordReset(user_id=2, reset_token="tok5", expires_at=datetime.utcnow() + timedelta(minutes=10))
    db = FakeDBVerify(resets=[reset1, reset2])
    service = UserService(db)
    
    result = await service.verify_password_reset("tok5")
    # debe devolver el primero encontrado
    assert result == reset1

@pytest.mark.asyncio
async def test_verify_password_reset_db_error():
    db = FakeDBVerify(raise_error=True)
    service = UserService(db)
    
    with pytest.raises(Exception, match="DB error simulado"):
        await service.verify_password_reset("tok_any")
