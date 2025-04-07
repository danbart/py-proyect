from flask import request, jsonify
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
