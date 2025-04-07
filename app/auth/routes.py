from flask import request, jsonify
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
