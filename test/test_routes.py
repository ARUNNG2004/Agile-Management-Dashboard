from flask import url_for, get_flashed_messages
from datetime import datetime
from app.models import User,Admin
def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
def test_adminIndex(client):
    response=client.get('/admin/')
    assert response.status_code==200
def test_register(client):
    response = client.get('/signup')
    assert b"<title>Sign-up</title>" in response.data
def test_signup(client,app):
    """
    Test successful user registration.
    """
    data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'dob': '2000-01-01',
        'gender': 'Male',
        'address': '123 Test St',
        'phone': '9876543210',
        'password': 'password123',
        'confirm-password': 'password123',
        'role': 'user',
        'enable_2fa': 'false'
    }
    with app.app_context():
        response = client.post('/signup', data=data, follow_redirects=True)

        # Check if the user was redirected to the login page
        assert response.status_code == 200
        assert b"<title>Login</title>" in response.data
        
        # Check if the success message was flashed
        messages = get_flashed_messages()
        assert 'Registration successful! Wait for admin approval.' in messages
        
        # Verify that the user was added to the database
        user = User.query.filter_by(email='test@example.com').first()
        assert user is not None
        assert user.name == 'Test User'
        assert user.phone == '9876543210'
        assert user.address == '123 Test St'
        assert user.role == 'user'
