from flasgger import Swagger
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Inicialización de las extensiones
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
swagger = Swagger()

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Cargar configuración
    if config_class is None:
        app.config.from_object('app.config.Config')
    else:
        app.config.from_object(config_class)
    
    # Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Configuración de Swagger
    app.config['SWAGGER'] = {
        'title': 'API de Usuarios',
        'version': '1.0.0',
        'description': 'API RESTful para gestionar usuarios',
        'uiversion': 3,
        'termsOfService': '',
        'specs': [
            {
                'endpoint': 'apispec',
                'route': '/apispec.json',
                'rule_filter': lambda rule: True,  # all rules
                'model_filter': lambda tag: True,  # all models
            }
        ],
        'specs_route': '/docs/'
    }
    swagger.init_app(app)
    
    # Registro de blueprints
    from app.api import api_bp
    from app.auth import auth_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    @app.route('/')
    def index():
        return {"message": "API en funcionamiento. Accede a /docs para ver la documentación."}
    
    return app
