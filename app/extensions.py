from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Shared extension instances; initialized with app in create_app().
db = SQLAlchemy()
migrate = Migrate()

login_manager = LoginManager()
# Redirect unauthenticated users to the login page.
login_manager.login_view = "auth.login"
