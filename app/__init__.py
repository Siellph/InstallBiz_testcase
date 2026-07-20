from flask import Flask

from app import storage
from app.config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    storage.init_db(app.config['DATABASE_PATH'])

    from .routes.download import download_bp
    from .routes.files import files_bp

    app.register_blueprint(download_bp)
    app.register_blueprint(files_bp)

    return app
