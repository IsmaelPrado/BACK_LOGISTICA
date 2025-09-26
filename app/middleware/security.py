import base64
from fastapi import Request, Response

USERNAME = "admin"
PASSWORD = "admin"

async def basic_auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/docs") or request.url.path.startswith("/openapi.json"):
        auth = request.headers.get("Authorization")
        if auth:
            try:
                scheme, credentials = auth.split()
                if scheme.lower() == "basic":
                    decoded = base64.b64decode(credentials).decode("utf-8")
                    username, password = decoded.split(":")
                    if username == USERNAME and password == PASSWORD:
                        return await call_next(request)
            except Exception:
                pass

        return Response(
            headers={"WWW-Authenticate": "Basic"},
            status_code=401,
            content="Authentication required"
        )
    return await call_next(request)
