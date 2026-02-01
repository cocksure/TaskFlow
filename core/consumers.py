import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Message, Task


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer для чата в задаче.

    Как это работает:
    1. connect() - пользователь открыл чат, подключаемся к группе задачи
    2. disconnect() - пользователь закрыл чат, отключаемся от группы
    3. receive() - получили сообщение от пользователя, сохраняем и рассылаем всем
    4. chat_message() - отправляем сообщение конкретному пользователю
    """

    async def connect(self):
        """Подключение к WebSocket"""
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.room_group_name = f'chat_task_{self.task_id}'
        self.user = self.scope['user']

        # Проверяем аутентификацию
        if not self.user.is_authenticated:
            await self.close()
            return

        # Проверяем существование задачи
        task_exists = await self.check_task_exists()
        if not task_exists:
            await self.close()
            return

        # Присоединяемся к группе чата задачи
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Отправляем историю сообщений при подключении
        messages = await self.get_message_history()
        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': messages
        }))

    async def disconnect(self, close_code):
        """Отключение от WebSocket"""
        # Покидаем группу
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Получение сообщения от клиента"""
        try:
            data = json.loads(text_data)
            message_text = data.get('message', '').strip()

            if not message_text:
                return

            # Сохраняем сообщение в БД
            message_data = await self.save_message(message_text)

            # Отправляем сообщение всем в группе
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_data
                }
            )
        except json.JSONDecodeError:
            pass

    async def chat_message(self, event):
        """Отправка сообщения клиенту (вызывается group_send)"""
        message = event['message']

        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message
        }))

    @sync_to_async
    def check_task_exists(self):
        """Проверяем существование задачи"""
        return Task.objects.filter(id=self.task_id).exists()

    @sync_to_async
    def get_message_history(self):
        """Получаем историю сообщений"""
        messages = Message.objects.filter(
            task_id=self.task_id
        ).select_related('user').order_by('created_at')[:100]

        return [
            {
                'id': msg.id,
                'user': msg.user.username,
                'user_id': msg.user.id,
                'text': msg.text,
                'created_at': msg.created_at.strftime('%d.%m %H:%M'),
                'is_own': msg.user_id == self.user.id
            }
            for msg in messages
        ]

    @sync_to_async
    def save_message(self, text):
        """Сохраняем сообщение в БД"""
        message = Message.objects.create(
            task_id=self.task_id,
            user=self.user,
            text=text
        )
        return {
            'id': message.id,
            'user': self.user.username,
            'user_id': self.user.id,
            'text': message.text,
            'created_at': message.created_at.strftime('%d.%m %H:%M'),
        }