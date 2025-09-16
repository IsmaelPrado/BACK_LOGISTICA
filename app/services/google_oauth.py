import httpx
from urllib.parse import urlencode
from app.core.config import settings

class GoogleOAuthService:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.auth_url = settings.GOOGLE_AUTH_URI
        self.token_url = settings.GOOGLE_TOKEN_URI
        self.user_info_url = settings.GOOGLE_USER_INFO_URI

    def get_google_login_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> dict:
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=data)
            response.raise_for_status()
            return response.json()
        
    async def get_user_info(self, access_token: str) -> dict:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(self.user_info_url, headers=headers)
            response.raise_for_status()
            return response.json()