from channels.generic.websocket import AsyncWebsocketConsumer
import json
from core.utils import total_match

class MyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("------Consumer-------",self.scope)
        print("------User-------",self.scope['user'])
        user_obj = await total_match(self.scope['user'])
        # print("------Query_string-------",str(self.scope['query_string'], 'UTF-8').split("/"))
        self.secure_code=str(self.scope['query_string'], 'UTF-8').split("/")[-1].split("=")[-1]
        # print("------secure_code-------",self.secure_code)
        self.room_group_name = "chat_%s" % self.secure_code
        print("------room_group_name-------",self.room_group_name)

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))
