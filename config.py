import os
from pathlib import Path
from dotenv import load_dotenv

# Always load the project's .env (independent of current working directory).
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-me')
    # Use a stable, repo-relative SQLite path so the app and init_db.py
    # always point at the same database (avoids creating multiple uniride.db files).
    _DEFAULT_SQLITE_PATH = (Path(__file__).resolve().parent / "instance" / "uniride.db").as_posix()
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{_DEFAULT_SQLITE_PATH}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('DEBUG', False)
    # When True, login page shows seeded demo accounts (admin/driver/passenger) from init_db.py.
    SHOW_DEMO_LOGIN = os.environ.get('SHOW_DEMO_LOGIN', '').lower() in ('1', 'true', 'yes')
    # Browser key: enable Maps JavaScript API + Places API; restrict by HTTP referrer in Google Cloud.
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

    # Prototype: force a single origin/destination for all users.
    # (Matches the two maps.app.goo.gl links you shared.)
    PROTOTYPE_FIXED_ORIGIN = os.environ.get(
        'PROTOTYPE_FIXED_ORIGIN',
        'Mosque of the Prophet District, Madinah'
    )
    PROTOTYPE_FIXED_DESTINATION = os.environ.get(
        'PROTOTYPE_FIXED_DESTINATION',
        'Islamic University of Madinah, Madinah'
    )

class DevelopmentConfig(Config):
    DEBUG = True
    SHOW_DEMO_LOGIN = True

class ProductionConfig(Config):
    DEBUG = False
    SHOW_DEMO_LOGIN = os.environ.get('SHOW_DEMO_LOGIN', '').lower() in ('1', 'true', 'yes')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}