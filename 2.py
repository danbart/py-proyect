#!/usr/bin/env python3
import os
import sys

def crear_estructura_flask_jwt_swagger():
    estructura = {
        # Estructura principal del proyecto
        "app": {
            "__init__.py": """from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flasgger import Swagger

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
""",
            "config.py": """import os
from datetime import timedelta

class Config:
    # Configuración general
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-por-defecto')
    
    # Configuración de base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/postgres')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-por-defecto')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=3)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=5)
""",
            "models.py": """from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
""",
            "api": {
                "__init__.py": """from flask import Blueprint

api_bp = Blueprint('api', __name__)

from app.api import routes
""",
                "routes.py": """from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api import api_bp
from app.models import User
from app import db
from flasgger import swag_from

# GET todos los usuarios
@api_bp.route('/users', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Users'],
    'summary': 'Obtener todos los usuarios',
    'description': 'Retorna una lista de todos los usuarios registrados',
    'responses': {
        200: {
            'description': 'Lista de usuarios',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'username': {'type': 'string'},
                                'email': {'type': 'string'},
                                'created_at': {'type': 'string', 'format': 'date-time'}
                            }
                        }
                    }
                }
            }
        },
        401: {
            'description': 'No autorizado'
        }
    }
})
def get_users():
    users = User.query.all()
    return jsonify([user.serialize() for user in users]), 200

# GET un usuario por ID
@api_bp.route('/users/<int:id>', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Users'],
    'summary': 'Obtener un usuario por ID',
    'description': 'Retorna un usuario basado en su ID',
    'parameters': [
        {
            'name': 'id',
            'in': 'path',
            'required': True,
            'description': 'ID del usuario',
            'schema': {'type': 'integer'}
        }
    ],
    'responses': {
        200: {
            'description': 'Usuario encontrado',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'username': {'type': 'string'},
                            'email': {'type': 'string'},
                            'created_at': {'type': 'string', 'format': 'date-time'}
                        }
                    }
                }
            }
        },
        404: {'description': 'Usuario no encontrado'},
        401: {'description': 'No autorizado'}
    }
})
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify(user.serialize()), 200

# POST crear un nuevo usuario
@api_bp.route('/users', methods=['POST'])
@jwt_required()
@swag_from({
    'tags': ['Users'],
    'summary': 'Crear un nuevo usuario',
    'description': 'Crea un nuevo usuario con los datos proporcionados',
    'requestBody': {
        'description': 'Datos del usuario',
        'required': True,
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'required': ['username', 'email', 'password'],
                    'properties': {
                        'username': {'type': 'string'},
                        'email': {'type': 'string'},
                        'password': {'type': 'string'}
                    }
                }
            }
        }
    },
    'responses': {
        201: {
            'description': 'Usuario creado exitosamente',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'username': {'type': 'string'},
                            'email': {'type': 'string'},
                            'created_at': {'type': 'string', 'format': 'date-time'}
                        }
                    }
                }
            }
        },
        400: {'description': 'Datos incompletos'},
        409: {'description': 'Usuario o email ya en uso'},
        401: {'description': 'No autorizado'}
    }
})
def create_user():
    data = request.get_json()
    
    if not data or 'username' not in data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Datos incompletos'}), 400
    
    # Verificar si el usuario o email ya existen
    existing_user = User.query.filter(
        (User.username == data['username']) | 
        (User.email == data['email'])
    ).first()
    
    if existing_user:
        return jsonify({'error': 'Username o email ya en uso'}), 409
    
    # Crear nuevo usuario
    user = User(
        username=data['username'], 
        email=data['email'], 
        password=data['password']
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.serialize()), 201

# PUT actualizar un usuario existente
@api_bp.route('/users/<int:id>', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Users'],
    'summary': 'Actualizar un usuario existente',
    'description': 'Actualiza los datos de un usuario existente',
    'parameters': [
        {
            'name': 'id',
            'in': 'path',
            'required': True,
            'description': 'ID del usuario',
            'schema': {'type': 'integer'}
        }
    ],
    'requestBody': {
        'description': 'Datos para actualizar',
        'required': True,
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'username': {'type': 'string'},
                        'email': {'type': 'string'},
                        'password': {'type': 'string'}
                    }
                }
            }
        }
    },
    'responses': {
        200: {
            'description': 'Usuario actualizado exitosamente',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'username': {'type': 'string'},
                            'email': {'type': 'string'},
                            'created_at': {'type': 'string', 'format': 'date-time'}
                        }
                    }
                }
            }
        },
        400: {'description': 'Datos incompletos'},
        404: {'description': 'Usuario no encontrado'},
        409: {'description': 'Username o email ya en uso'},
        401: {'description': 'No autorizado'}
    }
})
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Datos incompletos'}), 400
    
    # Actualizar campos si están presentes
    if 'username' in data:
        # Verificar si el nuevo username ya existe (y no es el usuario actual)
        existing_user = User.query.filter(User.username == data['username']).first()
        if existing_user and existing_user.id != id:
            return jsonify({'error': 'Username ya en uso'}), 409
        user.username = data['username']
    
    if 'email' in data:
        # Verificar si el nuevo email ya existe (y no es el usuario actual)
        existing_user = User.query.filter(User.email == data['email']).first()
        if existing_user and existing_user.id != id:
            return jsonify({'error': 'Email ya en uso'}), 409
        user.email = data['email']
    
    if 'password' in data:
        user.set_password(data['password'])
    
    db.session.commit()
    
    return jsonify(user.serialize()), 200

# DELETE eliminar un usuario
@api_bp.route('/users/<int:id>', methods=['DELETE'])
@jwt_required()
@swag_from({
    'tags': ['Users'],
    'summary': 'Eliminar un usuario',
    'description': 'Elimina un usuario existente',
    'parameters': [
        {
            'name': 'id',
            'in': 'path',
            'required': True,
            'description': 'ID del usuario',
            'schema': {'type': 'integer'}
        }
    ],
    'responses': {
        200: {
            'description': 'Usuario eliminado exitosamente',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'message': {'type': 'string'}
                        }
                    }
                }
            }
        },
        404: {'description': 'Usuario no encontrado'},
        401: {'description': 'No autorizado'}
    }
})
def delete_user(id):
    user = User.query.get_or_404(id)
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': f'Usuario {id} eliminado correctamente'}), 200
"""
            },
            "auth": {
                "__init__.py": """from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from app.auth import routes
""",
                "routes.py": """from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.auth import auth_bp
from app.models import User
from app import db
from flasgger import swag_from

# Registro de usuario
@auth_bp.route('/register', methods=['POST'])
@swag_from({
    'tags': ['Authentication'],
    'summary': 'Registrar un nuevo usuario',
    'description': 'Crea un nuevo usuario con los datos proporcionados',
    'requestBody': {
        'description': 'Datos del usuario',
        'required': True,
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'required': ['username', 'email', 'password'],
                    'properties': {
                        'username': {'type': 'string'},
                        'email': {'type': 'string'},
                        'password': {'type': 'string'}
                    }
                }
            }
        }
    },
    'responses': {
        201: {
            'description': 'Usuario registrado exitosamente',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'username': {'type': 'string'},
                            'email': {'type': 'string'},
                            'created_at': {'type': 'string', 'format': 'date-time'}
                        }
                    }
                }
            }
        },
        400: {'description': 'Datos incompletos'},
        409: {'description': 'Username o email ya en uso'}
    }
})
def register():
    data = request.get_json()
    
    if not data or 'username' not in data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Datos incompletos'}), 400
    
    # Verificar si el usuario o email ya existen
    existing_user = User.query.filter(
        (User.username == data['username']) | 
        (User.email == data['email'])
    ).first()
    
    if existing_user:
        return jsonify({'error': 'Username o email ya en uso'}), 409
    
    # Crear nuevo usuario
    user = User(
        username=data['username'], 
        email=data['email'], 
        password=data['password']
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.serialize()), 201

# Login de usuario
@auth_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Authentication'],
    'summary': 'Iniciar sesión',
    'description': 'Inicia sesión con username/email y password',
    'requestBody': {
        'description': 'Credenciales',
        'required': True,
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'required': ['login', 'password'],
                    'properties': {
                        'login': {'type': 'string', 'description': 'Username o email'},
                        'password': {'type': 'string'}
                    }
                }
            }
        }
    },
    'responses': {
        200: {
            'description': 'Login exitoso',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'access_token': {'type': 'string'},
                            'refresh_token': {'type': 'string'},
                            'user': {
                                'type': 'object',
                                'properties': {
                                    'id': {'type': 'integer'},
                                    'username': {'type': 'string'},
                                    'email': {'type': 'string'}
                                }
                            }
                        }
                    }
                }
            }
        },
        400: {'description': 'Datos incompletos'},
        401: {'description': 'Credenciales inválidas'}
    }
})
def login():
    data = request.get_json()
    
    if not data or 'login' not in data or 'password' not in data:
        return jsonify({'error': 'Datos incompletos'}), 400
    
    # Buscar usuario por username o email
    user = User.query.filter(
        (User.username == data['login']) | 
        (User.email == data['login'])
    ).first()
    
    # Verificar usuario y contraseña
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Credenciales inválidas'}), 401
    
    # Crear tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 200

# Refrescar token
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@swag_from({
    'tags': ['Authentication'],
    'summary': 'Refrescar token de acceso',
    'description': 'Genera un nuevo token de acceso usando el token de refresco',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Token refrescado exitosamente',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'access_token': {'type': 'string'}
                        }
                    }
                }
            }
        },
        401: {'description': 'Token inválido o expirado'}
    }
})
def refresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    
    return jsonify({
        'access_token': access_token
    }), 200

# Obtener datos del usuario actual
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Authentication'],
    'summary': 'Obtener usuario actual',
    'description': 'Retorna información del usuario autenticado',
    'security': [{'Bearer': []}],
    'responses': {
        200: {
            'description': 'Datos del usuario',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'username': {'type': 'string'},
                            'email': {'type': 'string'},
                            'created_at': {'type': 'string', 'format': 'date-time'}
                        }
                    }
                }
            }
        },
        401: {'description': 'No autorizado o token expirado'}
    }
})
def me():
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    
    return jsonify(user.serialize()), 200
"""
            }
        },
        "tests": {
            "__init__.py": "",
            "conftest.py": """import pytest
from app import create_app, db
from app.models import User

@pytest.fixture
def app():
    app = create_app('app.config.TestConfig')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    # Crear un usuario de prueba
    response = client.post('/auth/register', json={
        'username': 'testuser',
        'email': 'test@test.com',
        'password': 'testpass'
    })
    
    # Iniciar sesión
    response = client.post('/auth/login', json={
        'login': 'testuser',
        'password': 'testpass'
    })
    
    data = response.get_json()
    access_token = data['access_token']
    
    return {'Authorization': f'Bearer {access_token}'}
""",
            "test_auth.py": """import json
import pytest

def test_register(client):
    # Test de registro exitoso
    response = client.post('/auth/register', json={
        'username': 'user1',
        'email': 'user1@test.com',
        'password': 'password1'
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert data['username'] == 'user1'
    assert data['email'] == 'user1@test.com'
    assert 'password_hash' not in data
    
    # Test de registro con username existente
    response = client.post('/auth/register', json={
        'username': 'user1',
        'email': 'different@test.com',
        'password': 'password2'
    })
    
    assert response.status_code == 409
    
    # Test de registro con email existente
    response = client.post('/auth/register', json={
        'username': 'user2',
        'email': 'user1@test.com',
        'password': 'password2'
    })
    
    assert response.status_code == 409

def test_login(client):
    # Crear un usuario para probar
    client.post('/auth/register', json={
        'username': 'logintest',
        'email': 'login@test.com',
        'password': 'loginpass'
    })
    
    # Test de login exitoso con username
    response = client.post('/auth/login', json={
        'login': 'logintest',
        'password': 'loginpass'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert 'refresh_token' in data
    assert 'user' in data
    assert data['user']['username'] == 'logintest'
    
    # Test de login exitoso con email
    response = client.post('/auth/login', json={
        'login': 'login@test.com',
        'password': 'loginpass'
    })
    
    assert response.status_code == 200
    
    # Test de login con credenciales incorrectas
    response = client.post('/auth/login', json={
        'login': 'logintest',
        'password': 'wrongpass'
    })
    
    assert response.status_code == 401

def test_refresh(client):
    # Crear un usuario y obtener tokens
    client.post('/auth/register', json={
        'username': 'refreshtest',
        'email': 'refresh@test.com',
        'password': 'refreshpass'
    })
    
    response = client.post('/auth/login', json={
        'login': 'refreshtest',
        'password': 'refreshpass'
    })
    
    data = response.get_json()
    refresh_token = data['refresh_token']
    
    # Test de refresh exitoso
    response = client.post(
        '/auth/refresh', 
        headers={'Authorization': f'Bearer {refresh_token}'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data

def test_me(client, auth_headers):
    # Test de obtención de datos del usuario autenticado
    response = client.get('/auth/me', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == 'testuser'
    assert data['email'] == 'test@test.com'
""",
            "test_users.py": """import json
import pytest

def test_get_users(client, auth_headers):
    # Test de obtención de usuarios (debe estar vacío al principio)
    response = client.get('/api/users', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 1  # Solo el usuario de prueba creado por auth_headers

def test_create_user(client, auth_headers):
    # Test de creación exitosa
    response = client.post('/api/users', 
        headers=auth_headers,
        json={
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'newpass'
        }
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['username'] == 'newuser'
    assert data['email'] == 'new@test.com'
    
    # Test de validación de datos
    response = client.post('/api/users', 
        headers=auth_headers,
        json={
            'username': 'incomplete'
            # Falta email y password
        }
    )
    
    assert response.status_code == 400
    
    # Test de unicidad
    response = client.post('/api/users', 
        headers=auth_headers,
        json={
            'username': 'newuser',  # Username ya existe
            'email': 'another@test.com',
            'password': 'anotherpass'
        }
    )
    
    assert response.status_code == 409

def test_get_user(client, auth_headers):
    # Crear un usuario para luego obtenerlo por ID
    response = client.post('/api/users', 
        headers=auth_headers,
        json={
            'username': 'getuser',
            'email': 'get@test.com',
            'password': 'getpass'
        }
    )
    
    user_id = response.get_json()['id']
    
    # Test de obtención exitosa
    response = client.get(f'/api/users/{user_id}', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == user_id
    assert data['username'] == 'getuser'
    
    # Test de obtención de usuario inexistente
    response = client.get('/api/users/9999', headers=auth_headers)
    
    assert response.status_code == 404

def test_update_user(client, auth_headers):
    # Crear un usuario para luego actualizarlo
    response = client.post('/api/users', 
        headers=auth_headers,
        json={
            'username': 'updateuser',
            'email': 'update@test.com',
            'password': 'updatepass'
        }
    )
    
    user_id = response.get_json()['id']
    
    # Test de actualización exitosa
    response = client.put(f'/api/users/{user_id}', 
        headers=auth_headers,
        json={
            'username': 'updateduser',
            'email': 'updated@test.com'
        }
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['username'] == 'updateduser'
    assert data['email'] == 'updated@test.com'
    
    # Test de actualización de usuario inexistente
    response = client.put('/api/users/9999', 
        headers=auth_headers,
        json={
            'username': 'nonexistent'
        }
    )
    
    assert response.status_code == 404

def test_delete_user(client, auth_headers):
    # Crear un usuario para luego eliminarlo
    response = client.post('/api/users', 
        headers=auth_headers,
        json={
            'username': 'deleteuser',
            'email': 'delete@test.com',
            'password': 'deletepass'
        }
    )
    
    user_id = response.get_json()['id']
    
    # Test de eliminación exitosa
    response = client.delete(f'/api/users/{user_id}', headers=auth_headers)
    
    assert response.status_code == 200
    
    # Verificar que el usuario ya no existe
    response = client.get(f'/api/users/{user_id}', headers=auth_headers)
    assert response.status_code == 404
    
    # Test de eliminación de usuario inexistente
    response = client.delete('/api/users/9999', headers=auth_headers)
    assert response.status_code == 404
"""
        },
        "migrations": {
            # Este directorio se creará vacío
        },
        # Archivos de Docker
        "Dockerfile": """FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar la aplicación
COPY . .

# Exponer el puerto que utilizará la aplicación
EXPOSE 5000

# Comando para ejecutar las migraciones y la aplicación
CMD ["./entrypoint.sh"]
""",
        "docker-compose.yml": """version: '3.8'

services:
  web:
    build: .
    restart: always
    ports:
      - "5000:5000"
    environment:
      - FLASK_APP=wsgi.py
      - FLASK_DEBUG=1
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
      - SECRET_KEY=dev-secret-key-change-in-production
      - JWT_SECRET_KEY=dev-jwt-secret-key-change-in-production
    depends_on:
      - db
    volumes:
      - .:/app
    networks:
      - app-network

  db:
    image: postgres:13
    restart: always
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - app-network

networks:
  app-network:

volumes:
  postgres-data:
""",
        "entrypoint.sh": """#!/bin/sh

# Esperar a que la base de datos esté lista
echo "Esperando a que la base de datos esté disponible..."
python -c "
import time
import psycopg2

db_up = False
while not db_up:
    try:
        conn = psycopg2.connect('postgresql://postgres:postgres@db:5432/postgres')
        conn.close()
        db_up = True
    except psycopg2.OperationalError:
        print('La base de datos aún no está disponible. Esperando...')
        time.sleep(1)
"

# Ejecutar migraciones
echo "Ejecutando migraciones..."
flask db init || true
flask db migrate -m "Initial migration"
flask db upgrade

# Iniciar la aplicación
echo "Iniciando la aplicación..."
gunicorn --bind 0.0.0.0:5000 wsgi:app
""",
        # Archivo de configuración de Python
        "requirements.txt": """flask==2.2.3
flask-sqlalchemy==3.0.3
flask-migrate==4.0.4
flask-jwt-extended==4.4.4
flasgger==0.9.5
psycopg2-binary==2.9.5
gunicorn==20.1.0
pytest==7.3.1
pytest-flask==1.2.0
werkzeug==2.2.3
""",
        # Punto de entrada de la aplicación
        "wsgi.py": """from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
""",
        # Archivo para correr los tests
        "run_tests.sh": """#!/bin/sh
python -m pytest -v
""",
        # README con instrucciones
        "README.md": """# API CRUD de Usuarios con Flask, JWT, Swagger y Tests

Una API RESTful para gestionar usuarios, con autenticación JWT, documentación Swagger y tests automatizados.

## Estructura del Proyecto

```
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   └── auth/
│       ├── __init__.py
│       └── routes.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_users.py
├── migrations/
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── requirements.txt
├── run_tests.sh
├── wsgi.py
└── README.md
```

## Puntos Finales (Endpoints)

### Autenticación

- `POST /auth/register`: Registrar un nuevo usuario
- `POST /auth/login`: Iniciar sesión y obtener tokens
- `POST /auth/refresh`: Refrescar el token de acceso
- `GET /auth/me`: Obtener datos del usuario autenticado

### Usuarios

- `GET /api/users`: Obtener todos los usuarios
- `GET /api/users/<id>`: Obtener un usuario por ID
- `POST /api/users`: Crear un nuevo usuario
- `PUT /api/users/<id>`: Actualizar un usuario existente
- `DELETE /api/users/<id>`: Eliminar un usuario

## Documentación

La documentación completa de la API está disponible en Swagger:
- URL: `http://localhost:5000/docs/`

## Inicio Rápido

1. Clona el repositorio
2. Navega al directorio del proyecto
3. Ejecuta `docker-compose up --build`
4. La API estará disponible en `http://localhost:5000`
5. La documentación estará disponible en `http://localhost:5000/docs/`

## Tests

Para ejecutar los tests automáticamente:

```bash
docker-compose exec web ./run_tests.sh
```

## Ejemplos de Uso

### Registrar un usuario

```bash
curl -X POST http://localhost:5000/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"username": "example", "email": "example@example.com", "password": "securepassword"}'
```

### Iniciar sesión

```bash
curl -X POST http://localhost:5000/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"login": "example", "password": "securepassword"}'
```

### Obtener todos los usuarios (con autenticación)

```bash
curl -X GET http://localhost:5000/api/users \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Crear un usuario (con autenticación)

```bash
curl -X POST http://localhost:5000/api/users \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -d '{"username": "newuser", "email": "new@example.com", "password": "password"}'
```
"""
    }
    
    # Crear la estructura de directorios y archivos
    base_path = "flask_jwt_swagger"
    os.makedirs(base_path, exist_ok=True)
    
    for ruta, contenido in estructura.items():
        ruta_completa = os.path.join(base_path, ruta)
        
        if isinstance(contenido, dict):
            # Es un directorio
            os.makedirs(ruta_completa, exist_ok=True)
            
            # Crear los archivos dentro del directorio
            for nombre_archivo, contenido_archivo in contenido.items():
                if isinstance(contenido_archivo, dict):
                    # Es un subdirectorio
                    crear_subdirectorio(os.path.join(ruta_completa, nombre_archivo), contenido_archivo)
                else:
                    # Es un archivo
                    with open(os.path.join(ruta_completa, nombre_archivo), 'w') as f:
                        f.write(contenido_archivo)
        else:
            # Es un archivo en la raíz
            with open(ruta_completa, 'w') as f:
                f.write(contenido)
    
    # Hacer ejecutables los archivos de scripts
    os.chmod(os.path.join(base_path, "entrypoint.sh"), 0o755)
    os.chmod(os.path.join(base_path, "run_tests.sh"), 0o755)
    
    print(f"\n✅ Proyecto Flask + JWT + Swagger + Tests creado en: {os.path.abspath(base_path)}")
    print("\nPara ejecutar el proyecto:")
    print(f"  cd {base_path}")
    print("  docker-compose up --build")
    print("\nLa API estará disponible en: http://localhost:5000")
    print("La documentación Swagger estará en: http://localhost:5000/docs/")
    print("\nPara ejecutar los tests:")
    print("  docker-compose exec web ./run_tests.sh")

def crear_subdirectorio(ruta, estructura):
    os.makedirs(ruta, exist_ok=True)
    
    for nombre_archivo, contenido in estructura.items():
        if isinstance(contenido, dict):
            # Es un subdirectorio
            crear_subdirectorio(os.path.join(ruta, nombre_archivo), contenido)
        else:
            # Es un archivo
            with open(os.path.join(ruta, nombre_archivo), 'w') as f:
                f.write(contenido)

if __name__ == "__main__":
    crear_estructura_flask_jwt_swagger()