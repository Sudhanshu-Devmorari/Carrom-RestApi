from channels.generic.websocket import AsyncWebsocketConsumer
from core.utils import total_match, get_match_data, create_match_user, is_match_exists_with_code, create_match, update_match_user_status
import random
import json

class MyConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        if not self.scope['user'].is_authenticated:
            return
        
        response = {}
        self.secure_code = str(self.scope['query_string'], 'UTF-8').split("/")[-1].split("=")[-1]

        # Join Room
        if self.secure_code:
            self.room_group_name = "chat_%s" % self.secure_code

            match_obj = await get_match_data(self.secure_code)
            if match_obj:

                await self.channel_layer.group_add(self.room_group_name, self.channel_name)
                is_created = await create_match_user(match_obj, self.scope['user'].id)
                response.update({'status': 'success', 
                                 'message': 'User added successfully.',
                                 'room': 'join'})

        # Create new room
        else:
            # Generate room code (room code should be unique for each active match)
            while True:
                code = await self.generate_random_code()
                match_exists_with_code = await is_match_exists_with_code(code)
                if not match_exists_with_code:
                    break
            
            # Generate group name
            self.secure_code = code
            self.room_group_name = "chat_%s" % self.secure_code

            # Create match 
            match_obj = await create_match(code, self.scope['user'].id)

            # Join room
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)

            # Create match user
            is_created = await create_match_user(match_obj, self.scope['user'].id)
            
            # Send room code in response
            response.update({'status': 'success',
                            'message': 'User added successfully.',
                            'room': 'create', 
                            'room_code': self.secure_code})

        if response:
            await self.accept()
            if is_created:
                await total_match(self.scope['user'])
            await self.send_data_to_client(response)


    async def disconnect(self, close_code):
        if not self.scope['user'].is_authenticated:
            return
        
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name) # Leave room
        match_obj = await get_match_data(self.secure_code)
        if match_obj:
            await update_match_user_status(match_obj, self.scope['user'].id)


    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await self.send(text_data=json.dumps({
            'message': message
        }))


    async def send_data_to_client(self, data):
        await self.send(text_data=json.dumps(data)) # Send data to the connected client


    async def generate_random_code(self): 
        code = random.randint(1000, 9999)  # Generate a random integer between 1000 and 9999
        return code