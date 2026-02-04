import pytest
from fastapi import status


class TestMessagesAPI:
    """Тесты для API сообщений"""
    
    @pytest.fixture
    def created_chat(self, client, sample_chat_data):
        """Фикстура для создания чата перед тестами"""
        response = client.post("/chats/", json=sample_chat_data)
        return response.json()
    
    def test_create_message_success(self, client, created_chat, sample_message_data):
        """Тест успешного создания сообщения"""
        chat_id = created_chat["id"]
        response = client.post(f"/chats/{chat_id}/messages/", json=sample_message_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["text"] == sample_message_data["text"]
        assert data["chat_id"] == chat_id
        assert "id" in data
        assert "created_at" in data
        assert len(data["text"]) <= 5000
    
    def test_create_message_empty_text(self, client, created_chat):
        """Тест создания сообщения с пустым текстом"""
        chat_id = created_chat["id"]
        response = client.post(f"/chats/{chat_id}/messages/", json={"text": ""})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_message_too_long(self, client, created_chat):
        """Тест создания сообщения с слишком длинным текстом"""
        chat_id = created_chat["id"]
        long_text = "a" * 5001
        response = client.post(f"/chats/{chat_id}/messages/", json={"text": long_text})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_message_text_trimming(self, client, created_chat):
        """Тест обрезки пробелов в тексте сообщения"""
        chat_id = created_chat["id"]
        response = client.post(
            f"/chats/{chat_id}/messages/", 
            json={"text": "  Сообщение с пробелами  "}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["text"] == "Сообщение с пробелами"
    
    def test_create_message_in_nonexistent_chat(self, client, sample_message_data):
        """Тест создания сообщения в несуществующем чате"""
        response = client.post("/chats/999/messages/", json=sample_message_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_messages_ordering(self, client, created_chat):
        """Тест правильной сортировки сообщений по времени создания"""
        chat_id = created_chat["id"]
        
        # Создаем сообщения с разным текстом
        messages = ["Первое", "Второе", "Третье"]
        for text in messages:
            client.post(f"/chats/{chat_id}/messages/", json={"text": text})
        
        # Получаем чат с сообщениями
        response = client.get(f"/chats/{chat_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Проверяем, что сообщения отсортированы по времени создания (новые последние)
        # и содержат правильные тексты в правильном порядке
        received_texts = [msg["text"] for msg in data["messages"]]
        assert received_texts == messages
    
    def test_create_message_with_min_length_text(self, client, created_chat):
        """Тест создания сообщения с текстом минимальной длины"""
        chat_id = created_chat["id"]
        response = client.post(f"/chats/{chat_id}/messages/", json={"text": "a"})
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["text"] == "a"
    
    def test_message_limit_default(self, client, created_chat):
        """Тест лимита сообщений по умолчанию"""
        chat_id = created_chat["id"]
        
        # Создаем больше сообщений, чем лимит по умолчанию
        for i in range(25):
            client.post(f"/chats/{chat_id}/messages/", json={"text": f"Сообщение {i+1}"})
        
        # Получаем чат (должны получить только 20 последних сообщений)
        response = client.get(f"/chats/{chat_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["messages"]) == 20
        
        # Проверяем, что получили последние 20 сообщений
        received_texts = [msg["text"] for msg in data["messages"]]
        expected_texts = [f"Сообщение {i}" for i in range(6, 26)]
        assert received_texts == expected_texts