import pytest
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
