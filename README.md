# BACK_LOGISTICA

Backend desarrollado con **FastAPI** y **PostgreSQL** para la gestión logística.  
Incluye configuración de base de datos con **SQLAlchemy async**, manejo de variables de entorno y entorno virtual.

---

## 📦 Librerías necesarias

Instala las dependencias dentro de tu entorno virtual (`.venv`) con:

```bash
pip install "sqlalchemy[asyncio]"
pip install python-dotenv
pip install pydantic-settings
pip install fastapi
pip install "uvicorn[standard]"
pip install asyncpg
pip install "passlib[bcrypt]" 
pip install "python-jose[cryptography]"
pip install slowapi
pip install pydantic[email]
pip install fastapi-mail
pip install httpx
pip install pyotp
pip install qrcode
pip install "qrcode[pil]"

```

> 🔹 Recomendación: crea un archivo `requirements.txt` para manejar dependencias y facilitar la instalación en otros entornos:

```bash
pip freeze > requirements.txt
pip install -r requirements.txt
```

---

## ⚡ Correr el proyecto

Activa tu entorno virtual y ejecuta:

```bash
source .venv/bin/activate   # Linux / macOS
# o en Windows
# .venv\Scripts\activate

pip install -r requirements.txt

python -m uvicorn app.main:app --reload
```

Por defecto, la aplicación se ejecuta en:  

```
http://127.0.0.1:8000
```

### 📝 Documentación automática

FastAPI genera documentación automáticamente en:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

### TESTS
```
PYTHONPATH=$(pwd) pytest --cov=app --cov-report=html --html=reports/test_report.html --self-contained-html -v
```

---

## 🔧 Configuración de variables de entorno

Crea un archivo `.env` en la raíz del proyecto con tus credenciales y configuraciones sensibles:

```env
DATABASE_URL=postgresql+asyncpg://usuario:contraseña@localhost:5432/mi_base
```
---

## ✅ Buenas prácticas

- Siempre activa tu entorno virtual antes de instalar librerías o correr el proyecto.
- Mantén `.env` fuera del repositorio, usa `.env.example` para documentación.
- Usa `uvicorn --reload` solo en desarrollo. Para producción, configura un servidor como **Gunicorn** con **Uvicorn workers**.
