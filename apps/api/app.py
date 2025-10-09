from flask import Flask
from apps.api.blueprints.migrate import bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(bp)
    app.secret_key="AAAANASJKDHAIUFHIUBVSIJSDBIV SKJIVGSUIHFIASKJDBCIUOASHDIOQWJDKa iodcbasok"
    return app



