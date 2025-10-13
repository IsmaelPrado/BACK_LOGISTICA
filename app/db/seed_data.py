import pyotp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.rol import Rol
from app.models.permiso import Permiso
from app.core.security import hash_password
from app.models.user import Usuario

async def seed_roles_and_permissions(db: AsyncSession):
    # Roles base
    roles_data = [
        {"nombre": "admin", "descripcion": "Administrador con todos los permisos"},
        {"nombre": "usuario", "descripcion": "Usuario con permisos limitados"},
    ]

    # Permisos base
    permisos_data = [
        {"nombre": "crear_producto", "descripcion": "Puede crear productos"},
        {"nombre": "modificar_producto", "descripcion": "Puede modificar productos"},
        {"nombre": "eliminar_producto", "descripcion": "Puede eliminar productos"},
        {"nombre": "ver_productos", "descripcion": "Puede ver productos"},

        # Permisos de categorías
        {"nombre": "crear_categoria", "descripcion": "Puede crear categorías"},
        {"nombre": "modificar_categoria", "descripcion": "Puede modificar categorías"},
        {"nombre": "eliminar_categoria", "descripcion": "Puede eliminar categorías"},
        {"nombre": "ver_categorias", "descripcion": "Puede ver categorías"},
    ]

    # Insertar roles si no existen
    for rol_info in roles_data:
        result = await db.execute(select(Rol).filter_by(nombre=rol_info["nombre"]))
        rol = result.scalar_one_or_none()
        if not rol:
            db.add(Rol(**rol_info))

    # Insertar permisos si no existen
    for perm_info in permisos_data:
        result = await db.execute(select(Permiso).filter_by(nombre=perm_info["nombre"]))
        permiso = result.scalar_one_or_none()
        if not permiso:
            db.add(Permiso(**perm_info))

    await db.commit()

    # Crear usuario admin si no existe
    result = await db.execute(select(Usuario).filter_by(nombre_usuario="admin"))
    usuario_admin = result.scalar_one_or_none()
    if not usuario_admin:
        # Obtener todos los permisos existentes
        result = await db.execute(select(Permiso))
        all_permisos = result.scalars().all()

        # Crear admin con hash de contraseña "Linux123!"
        nuevo_admin = Usuario(
            nombre_usuario="admin",
            correo_electronico="vansestilo200@gmail.com",
            contrasena=hash_password("Linux123!"),
            rol="admin",
            secret_2fa=pyotp.random_base32(),
            permisos=all_permisos
        )
        db.add(nuevo_admin)
        await db.commit()
