import pytest
from fastapi import status


class TestIntegration:
    """Интеграционные тесты"""
    
    def test_chat_lifecycle(self, client):
        """Полный жизненный цикл чата: создание, сообщения, удаление"""
        # Создаем чат
        chat_response = client.post("/chats/", json={"title": "Интеграционный чат"})
        assert chat_response.status_code == status.HTTP_200_OK
        chat_id = chat_response.json()["id"]
        
        # Добавляем несколько сообщений
        for i in range(3):
            msg_response = client.post(
                f"/chats/{chat_id}/messages/", 
                json={"text": f"Интеграционное сообщение {i+1}"}
            )
            assert msg_response.status_code == status.HTTP_200_OK
        
        # Получаем чат с сообщениями
        get_response = client.get(f"/chats/{chat_id}")
        assert get_response.status_code == status.HTTP_200_OK
        chat_data = get_response.json()
        
        assert chat_data["chat"]["title"] == "Интеграционный чат"
        assert len(chat_data["messages"]) == 3
        
        # Удаляем чат
        delete_response = client.delete(f"/chats/{chat_id}")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
        
        # Проверяем, что чат удален
        get_response = client.get(f"/chats/{chat_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_concurrent_messages(self, client):
        """Тест добавления множества сообщений"""
        # Создаем чат
        chat_response = client.post("/chats/", json={"title": "Чат для нагрузочного теста"})
        chat_id = chat_response.json()["id"]
        
        # Добавляем 50 сообщений
        for i in range(50):
            client.post(f"/chats/{chat_id}/messages/", json={"text": f"Сообщение {i+1}"})
        
        # Проверяем, что можем получить все сообщения с лимитом 100
        response = client.get(f"/chats/{chat_id}?limit=100")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["messages"]) == 50