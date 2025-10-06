import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeoService:
    @staticmethod
    async def get_geolocation_from_ip(ip: str) -> tuple[float | None, float | None]:
        """
        Obtiene latitud y longitud aproximadas de un usuario usando la IP
        mediante Google Geolocation API. Devuelve (lat, lon) o (None, None)
        si no hay datos.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                payload = {
                    "considerIp": True  # Solo IP, sin Wi-Fi ni celular
                }
                url = f"{settings.GOOGLE_GEO_URL}key={settings.GOOGLE_GEO_API_KEY}"
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    location = data.get("location")
                    if location:
                        lat = location.get("lat")
                        lon = location.get("lng")
                        logger.info("Geo localizado Google API IP %s: lat=%s, lon=%s", ip, lat, lon)
                        return lat, lon
                    else:
                        logger.warning("Google API no devolvió location para IP %s", ip)
                else:
                    logger.warning("Error Google API (%s) para IP %s: %s", response.status_code, ip, response.text)
        except Exception as e:
            logger.exception("Excepción al consultar Google Geo API para IP %s: %s", ip, e)
        return None, None
