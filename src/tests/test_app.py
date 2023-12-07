import pytest
from fastapi.testclient import TestClient
from app.app import app, get_db

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def test_db():
    db = get_db()
    try:
        yield db
    finally:
        db.close()

def test_create_user(test_client, test_db):
    # Testa a criação de um novo usuário
    username = "testuser"
    password = "testpassword"
    data = {
        "username": username,
        "password": password,
        "email": "test@example.com",
        "full_name": "Test User",
    }
    response = test_client.post("/user", json=data)
    assert response.status_code == 200
    assert response.json()["username"] == username

def test_login(test_client, test_db):
    # Testa o login com um usuário criado anteriormente
    username = "testuser"
    password = "testpassword"
    data = {
        "username": username,
        "password": password,
    }
    response = test_client.post("/login", data=data)
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_create_historia(test_client, test_db):
    # Testa a criação de uma nova história
    titulo = "Test Title"
    historia = "Test Story Content"
    categoria = "Test Category"
    data = {
        "titulo": titulo,
        "historia": historia,
        "categoria": categoria,
    }
    response = test_client.post("/historia", json=data)
    assert response.status_code == 200
    assert "content" in response.json()

def test_update_historia(test_client, test_db):
    # Testa a atualização de uma história existente
    titulo = "Test Title"
    categoria = "Test Category"
    historia = "Updated Story Content"
    data = {
        "titulo": titulo,
        "categoria": categoria,
        "historia": historia,
    }
    response = test_client.patch("/atualizarhistoria", json=data)
    assert response.status_code == 200
    assert response.json() == historia

def test_delete_historia(test_client, test_db):
    # Testa a exclusão de uma história
    titulo = "Test Title"
    categoria = "Test Category"
    response = test_client.delete("/historia", params={"titulo": titulo, "categoria": categoria})
    assert response.status_code == 200
    assert response.json()["message"] == "Historia deleted successfully"

# Execute os testes usando o comando pytest
