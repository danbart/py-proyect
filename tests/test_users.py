import json
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
