from datetime import datetime
import random
import pyotp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.category import Category
from app.models.product import Product
from app.models.rol import Rol
from app.models.permiso import Permiso
from app.core.security import hash_password
from app.models.user import Usuario
from faker import Faker

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

        # Permiso de ventas
        {"nombre": "crear_venta", "descripcion": "Puede crear ventas"},
        {"nombre": "ver_reportes", "descripcion": "Puede ver un reporte de ventas"},

        # Permiso de ver historial de acciones
        {"nombre": "ver_historial", "descripcion": "Puede ver el historial de acciones de los usuarios"},

        # Permiso para reportes
        {"nombre": "ver_perfil", "descripcion": "Puede ver su perfil de usuario con el token"}
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

fake = Faker()

async def seed_categories_and_products(db: AsyncSession, num_categories=25, num_products=250):
    # 🔹 Generar categorías aleatorias
    categorias_dict = {}
    for i in range(num_categories):
        name = f"{fake.word().capitalize()} {i+1}"  # Evita duplicados
        # Verificar si ya existe
        result = await db.execute(select(Category).filter_by(name=name))
        categoria = result.scalar_one_or_none()
        if not categoria:
            categoria = Category(name=name)
            db.add(categoria)
            await db.flush()
        categorias_dict[name] = categoria

    # 🔹 Generar productos aleatorios
    used_codes = set()
    for i in range(num_products):
        # Generar código único
        while True:
            code = f"P{random.randint(1000, 9999)}"
            if code not in used_codes:
                used_codes.add(code)
                break

        # Elegir categoría aleatoria
        category_name = random.choice(list(categorias_dict.keys()))
        categoria = categorias_dict[category_name]

        # Generar datos del producto
        producto = Product(
            code=code,
            barcode=fake.ean13(),
            name=fake.word().capitalize() + f" {i+1}",
            description=fake.sentence(nb_words=6),
            sale_price=round(random.uniform(5.0, 2000.0), 2),
            inventory=random.randint(5, 200),
            min_inventory=random.randint(1, 20),
            category=categoria,
            date_added=datetime.utcnow()
        )

        db.add(producto)

    await db.commit()
