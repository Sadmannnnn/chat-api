import pytest
from fastapi import status


class TestChatsAPI:
    """Тесты для API чатов"""
    
    def test_create_chat_success(self, client, sample_chat_data):
        """Тест успешного создания чата"""
        response = client.post("/chats/", json=sample_chat_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["title"] == sample_chat_data["title"]
        assert "id" in data
        assert "created_at" in data
        assert len(data["title"]) <= 200
    
    def test_create_chat_empty_title(self, client):
        """Тест создания чата с пустым названием"""
        response = client.post("/chats/", json={"title": ""})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_chat_title_too_long(self, client):
        """Тест создания чата с слишком длинным названием"""
        long_title = "a" * 201
        response = client.post("/chats/", json={"title": long_title})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_chat_title_trimming(self, client):
        """Тест обрезки пробелов в названии"""
        response = client.post("/chats/", json={"title": "  Чат с пробелами  "})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Чат с пробелами"
    
    def test_get_chat_with_messages(self, client, sample_chat_data):
        """Тест получения чата с сообщениями"""
        # Создаем чат
        chat_response = client.post("/chats/", json=sample_chat_data)
        chat_id = chat_response.json()["id"]
        
        # Добавляем несколько сообщений
        for i in range(3):
            client.post(f"/chats/{chat_id}/messages/", json={"text": f"Сообщение {i+1}"})
        
        # Получаем чат с сообщениями
        response = client.get(f"/chats/{chat_id}?limit=10")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["chat"]["id"] == chat_id
        assert data["chat"]["title"] == sample_chat_data["title"]
        assert len(data["messages"]) == 3
        assert all("text" in msg for msg in data["messages"])
    
    def test_get_chat_with_limit(self, client, sample_chat_data):
        """Тест получения чата с ограничением количества сообщений"""
        # Создаем чат
        chat_response = client.post("/chats/", json=sample_chat_data)
        chat_id = chat_response.json()["id"]
        
        # Добавляем больше сообщений, чем лимит
        for i in range(25):
            client.post(f"/chats/{chat_id}/messages/", json={"text": f"Сообщение {i+1}"})
        
        # Получаем с лимитом по умолчанию (20)
        response = client.get(f"/chats/{chat_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["messages"]) == 20
        
        # Получаем с кастомным лимитом
        response = client.get(f"/chats/{chat_id}?limit=5")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["messages"]) == 5
    
    def test_get_chat_max_limit(self, client, sample_chat_data):
        """Тест получения чата с максимальным лимитом"""
        # Создаем чат
        chat_response = client.post("/chats/", json=sample_chat_data)
        chat_id = chat_response.json()["id"]
        
        # Добавляем сообщения
        for i in range(150):
            client.post(f"/chats/{chat_id}/messages/", json={"text": f"Сообщение {i+1}"})
        
        # Пытаемся получить с лимитом больше максимума
        response = client.get(f"/chats/{chat_id}?limit=150")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_nonexistent_chat(self, client):
        """Тест получения несуществующего чата"""
        response = client.get("/chats/999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_chat_success(self, client, sample_chat_data):
        """Тест успешного удаления чата"""
        # Создаем чат
        chat_response = client.post("/chats/", json=sample_chat_data)
        chat_id = chat_response.json()["id"]
        
        # Добавляем сообщение
        client.post(f"/chats/{chat_id}/messages/", json={"text": "Сообщение для удаления"})
        
        # Удаляем чат
        response = client.delete(f"/chats/{chat_id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Проверяем, что чат удален
        response = client.get(f"/chats/{chat_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_nonexistent_chat(self, client):
        """Тест удаления несуществующего чата"""
        response = client.delete("/chats/999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_cascade_delete_messages(self, client, sample_chat_data):
        """Тест каскадного удаления сообщений при удалении чата"""
        # Создаем чат
        chat_response = client.post("/chats/", json=sample_chat_data)
        chat_id = chat_response.json()["id"]
        
        # Добавляем несколько сообщений
        for i in range(5):
            client.post(f"/chats/{chat_id}/messages/", json={"text": f"Сообщение {i+1}"})
        
        # Получаем чат с сообщениями
        get_response = client.get(f"/chats/{chat_id}")
        assert len(get_response.json()["messages"]) == 5
        
        # Удаляем чат
        client.delete(f"/chats/{chat_id}")
        
        # Пробуем отправить сообщение в удаленный чат
        response = client.post(f"/chats/{chat_id}/messages/", json={"text": "Новое сообщение"})
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_chat_with_min_length_title(self, client):
        """Тест создания чата с названием минимальной длины"""
        response = client.post("/chats/", json={"title": "a"})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "a"