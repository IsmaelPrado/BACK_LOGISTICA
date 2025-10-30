from datetime import datetime
import pyotp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.category import Category
from app.models.product import Product
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

async def seed_categories_and_products(db: AsyncSession):
    # 🔹 Categorías base
    categorias_data = [
        {"name": "Papelería"},
        {"name": "Electrónica"},
        {"name": "Librería"},
        {"name": "Muebles"},
    ]

    categorias_dict = {}  # Guardaremos objetos Category para relacionarlos con productos

    # Insertar categorías si no existen
    for cat_info in categorias_data:
        result = await db.execute(select(Category).filter_by(name=cat_info["name"]))
        categoria = result.scalar_one_or_none()
        if not categoria:
            categoria = Category(**cat_info)
            db.add(categoria)
            await db.flush()  # Necesario para obtener id antes del commit
        categorias_dict[cat_info["name"]] = categoria

    # 🔹 Productos base
    productos_data = [
        {
            "code": "P001",
            "barcode": "1234567890123",
            "name": "Lápiz HB",
            "description": "Lápiz para escribir y dibujar",
            "sale_price": 5.00,
            "inventory": 120,
            "min_inventory": 20,
            "category_name": "Papelería"
        },
        {
            "code": "P002",
            "barcode": "1234567890124",
            "name": "Cuaderno Profesional",
            "description": "Cuaderno tamaño carta, hojas rayadas",
            "sale_price": 35.00,
            "inventory": 60,
            "min_inventory": 10,
            "category_name": "Papelería"
        },
        {
            "code": "P003",
            "barcode": "1234567890125",
            "name": "Marcador Azul",
            "description": "Marcador para pizarras blancas",
            "sale_price": 12.00,
            "inventory": 80,
            "min_inventory": 15,
            "category_name": "Papelería"
        },
        {
            "code": "P004",
            "barcode": "1234567890126",
            "name": "Mouse Inalámbrico",
            "description": "Mouse inalámbrico USB",
            "sale_price": 150.00,
            "inventory": 50,
            "min_inventory": 5,
            "category_name": "Electrónica"
        },
        {
            "code": "P005",
            "barcode": "1234567890127",
            "name": "Silla Oficina",
            "description": "Silla ergonómica para oficina",
            "sale_price": 1200.00,
            "inventory": 20,
            "min_inventory": 2,
            "category_name": "Muebles"
        },
    ]

    # Insertar productos si no existen
    for prod_info in productos_data:
        result = await db.execute(select(Product).filter_by(code=prod_info["code"]))
        producto = result.scalar_one_or_none()
        if not producto:
            categoria = categorias_dict[prod_info["category_name"]]
            producto = Product(
                code=prod_info["code"],
                barcode=prod_info["barcode"],
                name=prod_info["name"],
                description=prod_info["description"],
                sale_price=prod_info["sale_price"],
                inventory=prod_info["inventory"],
                min_inventory=prod_info["min_inventory"],
                category=categoria,
                date_added=datetime.utcnow()
            )
            db.add(producto)

    await db.commit()
