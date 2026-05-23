from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_compress import Compress
from flask_caching import Cache

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])
talisman = Talisman()
compress = Compress()
cache = Cache()
