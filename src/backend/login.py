from fastapi_login import LoginManager
from .config import settings

login_manager = LoginManager(settings.login_key, "/login", use_cookie=True)
