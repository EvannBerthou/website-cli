from fastapi_login import LoginManager
from .config import settings

assert settings.login_key, "Please provide a Login Secret Key."
login_manager = LoginManager(settings.login_key, "/login", use_cookie=True)
