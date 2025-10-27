from functools import wraps
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.historial_acciones_service import registrar_accion_async

def log_action(accion: str, modulo: str):
    """
    Decorador para registrar automáticamente una acción en el historial.
    Solo registra si la acción fue exitosa (success=True).

    - Para 'crear': datos_nuevos contiene el objeto creado, datos_anteriores es None.
    - Para 'modificar': datos_anteriores contiene el estado previo, datos_nuevos el estado actualizado.
    - Para 'eliminar': datos_anteriores contiene el objeto eliminado, datos_nuevos es None.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Ejecutar la función original
            response = await func(*args, **kwargs)

            # Extraer db, usuario y request de kwargs
            db: AsyncSession = kwargs.get("db")
            usuario = kwargs.get("usuario")
            request: Request = kwargs.get("request")

            # Registrar solo si la acción fue exitosa
            if db and usuario and getattr(response, "success", False):
                datos_anteriores = None
                datos_nuevos = None

                # Convertir el response a dict JSON serializable
                datos_nuevos = jsonable_encoder(response)

                # Para modificar o eliminar, intentar obtener previous_data
                if accion in ["modificar", "eliminar"]:
                    prev_data = getattr(response, "previous_data", None)
                    datos_anteriores = jsonable_encoder(prev_data) if prev_data else None

                    if accion == "eliminar":
                        datos_nuevos = None  # En eliminar, no hay datos nuevos

                # Registrar acción en la base de datos
                await registrar_accion_async(
                    db=db,
                    id_usuario=usuario.id_usuario,
                    accion=accion,
                    modulo=modulo,
                    descripcion=f"{accion.capitalize()} en {modulo}",
                    datos_anteriores=datos_anteriores,
                    datos_nuevos=datos_nuevos,
                )

            return response
        return wrapper
    return decorator
