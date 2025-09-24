from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # Configuración del correo electrónico
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool

    # Configuración de OTP
    OTP_EXPIRE_MINUTES: int
    OTP_LENGTH: int

    # Configuracion OAuth2
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    GOOGLE_AUTH_URI: str
    GOOGLE_TOKEN_URI: str
    GOOGLE_USER_INFO_URI: str

    # Configuración de geolocalización con Google
    GOOGLE_GEO_URL: str
    GOOGLE_GEO_API_KEY: str

    class Config:
        env_file = ".env"   # indica de dónde leer variables

settings = Settings()
