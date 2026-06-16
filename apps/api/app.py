from flask import Flask
from apps.api.blueprints.migrate import bp
import os

def create_app():
    app = Flask(__name__)
    app.register_blueprint(bp)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    return app



