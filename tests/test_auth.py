import json
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
