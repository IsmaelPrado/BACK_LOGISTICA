# tests/test_user_service.py
import asyncio
from sqlite3 import IntegrityError
from unittest.mock import AsyncMock

from pydantic import ValidationError
from app.models.user import Usuario
from app.schemas.auth import UsuarioRequest
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



# ------------------------
# Fake DB para update_password
# ------------------------
class FakeDBUpdate:
    def __init__(self):
        self.added = None
        self.committed = False
        self.refreshed = False

    def add(self, obj):
        self.added = obj

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        self.refreshed = True

# ------------------------
# Tests update_password
# ------------------------
@pytest.mark.asyncio
async def test_update_password_success(monkeypatch):
    """✅ Contraseña válida, actualización correcta"""
    db = FakeDBUpdate()
    service = UserService(db)
    user = Usuario(nombre_usuario="manuel", contrasena="oldpass", correo_electronico="a@b.com", rol="admin")

    # Mock hash_password
    monkeypatch.setattr("app.services.user_service.hash_password", lambda pwd: "hashed_" + pwd)

    updated_user = await service.update_password(user, "Password123!")

    assert updated_user.contrasena == "hashed_Password123!"
    assert db.added == user
    assert db.committed is True
    assert db.refreshed is True

@pytest.mark.asyncio
async def test_update_password_missing_special(monkeypatch):
    """❌ Contraseña sin carácter especial"""
    db = FakeDBUpdate()
    service = UserService(db)
    user = Usuario(nombre_usuario="manuel", contrasena="oldpass", correo_electronico="a@b.com", rol="admin")

    with pytest.raises(ValueError, match="mayúscula, minúscula, número y carácter especial"):
        await service.update_password(user, "Password123")

@pytest.mark.asyncio
async def test_update_password_missing_upper(monkeypatch):
    """❌ Contraseña sin mayúscula"""
    db = FakeDBUpdate()
    service = UserService(db)
    user = Usuario(nombre_usuario="manuel", contrasena="oldpass", correo_electronico="a@b.com", rol="admin")

    with pytest.raises(ValueError, match="mayúscula, minúscula, número y carácter especial"):
        await service.update_password(user, "password123!")

@pytest.mark.asyncio
async def test_update_password_missing_lower(monkeypatch):
    """❌ Contraseña sin minúscula"""
    db = FakeDBUpdate()
    service = UserService(db)
    user = Usuario(nombre_usuario="manuel", contrasena="oldpass", correo_electronico="a@b.com", rol="admin")

    with pytest.raises(ValueError, match="mayúscula, minúscula, número y carácter especial"):
        await service.update_password(user, "PASSWORD123!")

@pytest.mark.asyncio
async def test_update_password_missing_digit(monkeypatch):
    """❌ Contraseña sin número"""
    db = FakeDBUpdate()
    service = UserService(db)
    user = Usuario(nombre_usuario="manuel", contrasena="oldpass", correo_electronico="a@b.com", rol="admin")

    with pytest.raises(ValueError, match="mayúscula, minúscula, número y carácter especial"):
        await service.update_password(user, "Password!!!")

@pytest.mark.asyncio
async def test_update_password_empty(monkeypatch):
    """❌ Contraseña vacía"""
    db = FakeDBUpdate()
    service = UserService(db)
    user = Usuario(nombre_usuario="manuel", contrasena="oldpass", correo_electronico="a@b.com", rol="admin")

    with pytest.raises(ValueError, match="mayúscula, minúscula, número y carácter especial"):
        await service.update_password(user, "")

@pytest.mark.asyncio
async def test_update_password_min_length(monkeypatch):
    """❌ Contraseña demasiado corta"""
    db = FakeDBUpdate()
    service = UserService(db)
    user = Usuario(nombre_usuario="manuel", contrasena="oldpass", correo_electronico="a@b.com", rol="admin")

    # Incluso si cumple patrón, podría agregar otra validación de longitud si el service lo tuviera
    # Por ahora solo validamos con el patrón
    with pytest.raises(ValueError, match="mayúscula, minúscula, número y carácter especial"):
        await service.update_password(user, "P1!")  # demasiado corta