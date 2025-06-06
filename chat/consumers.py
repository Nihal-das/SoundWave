import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatRoom, Message
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        sanitized_room_name = self.room_name.replace(" ", "_")
        self.room_group_name = f'chat_{sanitized_room_name}'

        # Deny connection for anonymous users
        user = self.scope.get("user")
        if user is None or isinstance(user, AnonymousUser) or user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except Exception:
            await self.send(json.dumps({'error': 'Invalid JSON.'}))
            return

        action = data.get("action", "send")
        user = self.scope.get("user")
        if user is None or user.is_anonymous:
            await self.send(json.dumps({'error': 'Authentication required.'}))
            return

        if action == "send":
            message = data.get("message", "").strip()
            if message:
                room = await self.get_room(self.room_name)
                msg = await self.create_message(room, user, message)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "action": "send",
                        "message": message,
                        "message_id": msg.id,
                        "user": user.name,
                        "user_id": user.id,
                    }
                )

        elif action == "edit":
            msg_id = data.get("message_id")
            new_content = data.get("new_content", "").strip()
            if msg_id and new_content:
                msg_user_id = await self.get_message_user_id(msg_id)
                if msg_user_id == user.id:
                    await self.update_message(msg_id, new_content)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "chat_message",
                            "action": "edit",
                            "message": new_content,
                            "message_id": msg_id,
                            "user": user.name,
                            "user_id": user.id,
                        }
                    )
                else:
                    await self.send(json.dumps({'error': 'Permission denied.'}))

        elif action == "delete":
            msg_id = data.get("message_id")
            if msg_id:
                msg_user_id = await self.get_message_user_id(msg_id)
                if msg_user_id == user.id:
                    await self.delete_message(msg_id)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "chat_message",
                            "action": "delete",
                            "message_id": msg_id,
                        }
                    )
                else:
                    await self.send(json.dumps({'error': 'Permission denied.'}))

        elif action == "music_control":
            # Accept only valid videoId/title for YouTube
            video_id = data.get("videoId", "")
            title = data.get("title", "")
            if video_id and title:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "music_control",
                        "action": "music_control",
                        "videoId": video_id,
                        "title": title,
                    }
                )
            else:
                await self.send(json.dumps({'error': 'Missing video info.'}))

        else:
            await self.send(json.dumps({'error': f'Unknown action: {action}'}))

    async def music_control(self, event):
        # Broadcasts music control command and track info to all clients
        await self.send(text_data=json.dumps({
            "action": "music_control",
            "videoId": event.get("videoId", ""),
            "title": event.get("title", ""),
        }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    # ORM accessors wrapped with async-safe decorators
    @database_sync_to_async
    def get_room(self, name):
        return ChatRoom.objects.get(name=name)

    @database_sync_to_async
    def create_message(self, room, user, content):
        return Message.objects.create(room=room, user=user, content=content)

    @database_sync_to_async
    def get_message_user_id(self, msg_id):
        try:
            return Message.objects.get(id=msg_id).user_id
        except Message.DoesNotExist:
            return None

    @database_sync_to_async
    def update_message(self, msg_id, new_content):
        try:
            msg = Message.objects.get(id=msg_id)
            msg.content = new_content
            msg.save()
        except Message.DoesNotExist:
            pass

    @database_sync_to_async
    def delete_message(self, msg_id):
        try:
            msg = Message.objects.get(id=msg_id)
            msg.delete()
        except Message.DoesNotExist:
            pass