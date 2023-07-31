from channels.generic.websocket import AsyncWebsocketConsumer
from core.utils import (total_match, get_match_data, create_match_user, is_match_exists_with_code, create_match,
                        update_match_user_status, get_match_city,user_has_enough_coin,get_pending_city_match,
                        update_match_user, get_match_id_list, get_total_score, charge_entry_fee,
                        update_player_score, assign_winning_prize, update_score_based_on_penlty,
                        get_current_player_data, get_next_player_data, get_game_over_status, update_match,is_skip_next_turn, update_skip_turn_of_player,
                        PlayWithFriendEntryFee)

from core.models import MatchUser, Match
from channels.db import database_sync_to_async

from datetime import datetime
import random
import json
import ast


class CarromPlayGame:
    
    foul_penlty_w = 200
    foul_penlty_b = 100
    cookie_win_coin = {'B':100, 'W':200, 'R':500}
    cookie_initial_position = [
        # Black cookie positions
        {'c':'B', 'x' : 0     , 'y':0.278 , 'z' :0 },
        {'c':'B', 'x' : 0.238 , 'y':0.14  , 'z' :0 },
        {'c':'B', 'x' : 0.239 , 'y':0.14  , 'z' :0 },
        {'c':'B', 'x' : 0.469 , 'y':0.283 , 'z' :0 },
        {'c':'B', 'x' : 0.476 , 'y':0.27  , 'z' :0 },
        {'c':'B', 'x' : 0.02  , 'y':0.55  , 'z' :0 },
        {'c':'B', 'x' : 0.496 , 'y':0.277 , 'z' :0 },
        {'c':'B', 'x' : 0.472 , 'y':0.277 , 'z' :0 },
        {'c':'B', 'x' : 0     , 'y':0.566 , 'z' :0 },

        # White cookie positions
        {'c':'W', 'x' : 0     , 'y':-0.283, 'z' :0 },
        {'c':'W', 'x' : 0.471 , 'y':0     , 'z' :0 },
        {'c':'W', 'x' : 0.241 , 'y':0.139 , 'z' :0 },
        {'c':'W', 'x' : 0.238 , 'y':0.139 , 'z' :0 },
        {'c':'W', 'x' : 0.245 , 'y':0.422 , 'z' :0 },
        {'c':'W', 'x' : 0.258 , 'y':0.414 , 'z' :0 },
        {'c':'W', 'x' : 0.232 , 'y':0.428 , 'z' :0 },
        {'c':'W', 'x' : 0.486 , 'y':0     , 'z' :0 },
        {'c':'W', 'x' : 0.245 , 'y':0.423 , 'z' :0 },

        # Red cookie positions
        {'c':'R', 'x' : 0 , 'y':0 , 'z' :0 },
    ]

    async def initialize(self, message):
        """ Initialize parameters when game is started """
        self.score = 0
        self.cookie_data = {'B':0, 'W':0, 'R':0} # dict of cookies to keep track how much cookie is pocked up (initially all zero as all cookie are present on board)

        self.cookie_data_list = message['cookie_data']
        self.striker_foul = ast.literal_eval(message.get('striker_foul', False)) 

        self.game_over_score = {'B': 9*self.cookie_win_coin['B'],
                           'W': 9*self.cookie_win_coin['W'],
                           'R': self.cookie_win_coin['R'],}

    async def get_game_data(self):
        """ Get current running player in game """
        if not self.match_obj:
            self.match_obj = await database_sync_to_async(Match.objects.filter(code=self.group_name).first)() 
        
        self.current_player_data = await get_current_player_data(self.match_obj.id) 
      
    async def calculate_how_much_cookie_pocked_up(self):
        """ Calculate how much cookie is pocked up by player """
        for data in self.cookie_data_list:
            if int(data['z']):
                self.cookie_data[data['c']] += 1
        
    async def calculate_score(self):
        """ Calculate score of player based on amount of cookies pocked up """
        for key, value in self.cookie_data.items():
            self.score += (value*self.cookie_win_coin[key])

    async def operation_if_previous_cookie_red(self):
        """ Operation perform if previous cookie is red 
            If previous cookie is red, then
            next cookie pocked up: Update score for red cookie
            next cookie not pocked up: Put red cookie again on board"""
        if self.is_red:
            if self.score != 0:
                self.score += self.cookie_win_coin['R']
            else:
                self.cookie_data_list.append({'c':'R', 'x': 0 , 'y':0 , 'z':0 })

    async def is_red_cookie_pocked_up(self):
        """ Check is player pocked up red cookie ? """
        self.is_red = True if self.cookie_data['R'] != 0 else False

    async def check_last_cookie_is_red(self):
        """ Check if last cookie pocked up is red cookie ? """
        if self.is_red:
            total_match_score = await get_total_score(self.match_obj.id)
            self.is_red_last = True if total_match_score >= (self.game_over_score['B'] + self.game_over_score['W']) else False

    async def change_player_turn(self):
        """ Update current player turn to False 
            Get next player
            Update next player turn to True"""
        await update_match_user(params_to_filter={'id': self.current_player_data['id']},
                                     params_to_update={'user_turn': False})
        self.next_player_data = await get_next_player_data(self.current_player_data['id'], self.match_obj.id)
        await update_match_user(params_to_filter={'id': self.next_player_data['id']},
                                    params_to_update={'user_turn': True})

    async def select_random_player(self, match_id):
        match_players = await get_match_id_list(match_id)
        player_to_play = random.choice(match_players)

        # Update user_turn for randomly selected player to True
        await update_match_user(params_to_filter={'id': player_to_play},
                                    params_to_update={'user_turn': True})
        
        # Get match user data for player who has turn
        match_data = await get_current_player_data(match_id)
        return match_data
    
    async def operation_on_striker_foul(self):
        if self.striker_foul == True:
            self.cookie_data_list = await update_score_based_on_penlty(self.current_player_data['id'],
                                                                        self.foul_penlty_w,
                                                                        self.foul_penlty_b,
                                                                        self.cookie_data_list)

    async def play_game(self, message):
        await self.initialize(message)
        await self.get_game_data()
        await self.calculate_how_much_cookie_pocked_up()
        await self.calculate_score()
        
        await self.operation_if_previous_cookie_red()
        await self.is_red_cookie_pocked_up()
        await self.check_last_cookie_is_red()
       
       
        # None of cookie is pocketing
        if self.score == 0:
            skip_player_turn = await is_skip_next_turn(self.current_player_data['id'], self.current_player_data['match_id'])
            if skip_player_turn == False:
                await self.change_player_turn()
            
                self.next_player_turn = {
                    'id': self.next_player_data['user_id'],
                    'user_id': self.next_player_data['user__user_id'],
                    'username': self.next_player_data['user__username']
                }
            else:
                # Update player skip turn to false
                await update_skip_turn_of_player(self.current_player_data['id'], self.current_player_data['match_id'])

                self.next_player_turn = {
                    'id': self.current_player_data['user_id'],
                    'user_id': self.current_player_data['user__user_id'],
                    'username': self.current_player_data['user__username']
                }
        
        # Since cookie is pocketing so still current player has chance
        else:
            if self.is_red == False or self.is_red_last == True:
                await update_player_score(self.current_player_data['id'], self.score) #  Update score of player
            
            self.next_player_turn = {
                'id': self.current_player_data['user_id'],
                'user_id': self.current_player_data['user__user_id'],
                'username': self.current_player_data['user__username']
            }

       
        # If foul than make penalty
        await self.operation_on_striker_foul()
       
        # Check if game is over
        total_match_score = await get_total_score(self.match_obj.id)
        if total_match_score < sum(self.game_over_score.values()):
            self.cookie_data_list = list(filter(lambda x:x['z'] == 0, self.cookie_data_list)) # Remove all pocketing cookies

            response = {'game': 'running',
                        'player': self.next_player_turn['user_id'],
                        'player_username': self.next_player_turn['username'],
                        'cookie_data': self.cookie_data_list}
        
        else:
            # Get winner
            game_over = await get_game_over_status(self.match_obj.id)

            if game_over['status'] == 'tie':
                await assign_winning_prize(game_over['user_ids'], int(game_over['winning_prize']/2))
                response = {'game': 'over', 'status': 'tie'}

            else:
                await assign_winning_prize([game_over['winner']['user_id']], game_over['winning_prize'])
                response = {'game': 'over', 'status': 'winner',
                            'winner': game_over['winner']['user__user_id'],
                            'winner_username': game_over['winner']['user__username'],
                            'winning_score': game_over['winner']['score']}
           
            # Update end_time of match
            await update_match(params_to_filter={'id': self.match_obj.id},
                               params_to_update={'end_time': datetime.now()})

        # Broadcast message
        await self.broadcast_message_to_client(self.room_group_name, response)

    async def send_data_to_client(self, data):
        await self.send(text_data=json.dumps(data)) # Send data to the connected client

    async def broadcast_message_to_client(self, group_name, data):
        await self.channel_layer.group_send(
            group_name,
            {
                'type': 'group.message',
                'message': data
            }
        )

    async def group_message(self, event):
        await self.send(text_data=json.dumps(event['message'])) # Send group message to the connected client

    async def disconnect_from_group(self, room_group_name, channel_name, group_code, match_type):
        await self.channel_layer.group_discard(room_group_name, channel_name) # Leave room
        match_obj = await get_match_data({'code': group_code, 'match_type': match_type, 'status':1})
        if match_obj:
            await update_match_user_status(match_obj, self.scope['user'].id)


class PlaywithFriendsConsumer(AsyncWebsocketConsumer, CarromPlayGame):

    match_type = 1

    async def check_validation(self):
        # 1. user has enough coin to join match ?
        has_enough_coin = await user_has_enough_coin(self.scope['user'].id, PlayWithFriendEntryFee)
        if not has_enough_coin:
            return False

        return True
    
    async def join_player_to_match(self):
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
                
        self.is_created = await create_match_user({'match':self.match_obj,
                                                   'user_id':self.scope['user'].id,
                                                   'status':0})

    async def connect(self):
        if not self.scope['user'].is_authenticated:
            return
        
        is_validate = await self.check_validation()
        if not is_validate:
            return 
        
        response = {}
        self.is_red = False
        self.is_red_last = False

        group_name = None
        query_string = self.scope["query_string"].decode("utf-8")
        for param in query_string.split("&"):
            key, value = param.split("=")
            if key == "secure_code":
                group_name = value
                break
        self.group_name = group_name

        # Join Room
        if self.group_name:
            self.room_group_name = "chat_%s" % self.group_name

            self.match_obj = await get_match_data({'code': self.group_name, 'match_type': self.match_type, 'status':1})
            if self.match_obj:
                # Check any pending matches
                pending_match_user = await database_sync_to_async(MatchUser.objects.filter(match=self.match_obj, status=0).first)()
                if not pending_match_user:
                    return 

                # Join player to match
                await self.join_player_to_match()

                # Now all players status changes to running
                await update_match_user(params_to_filter={'match_id':self.match_obj.id},
                              params_to_update={'status':1})
                
                # charge entry fee to players
                player_coin_data = await charge_entry_fee(pending_match_user)

                # Take random player to send
                match_data = await self.select_random_player(self.match_obj.id)
            
                # Update start_time of match
                await update_match(params_to_filter={'id': self.match_obj.id},
                               params_to_update={'start_time': datetime.now()})
            
                response.update({'status': 'success', 
                                 'room': 'join',
                                 'player': match_data['user__user_id'],
                                 'player_user_name': match_data['user__username'],
                                 'cookie_data': self.cookie_initial_position,
                                 'player_coin_data': player_coin_data
                                })

        # Create new room
        else:
            # Generate room code (room code should be unique for each active match)
            while True:
                code = await self.generate_random_code()
                match_exists_with_code = await is_match_exists_with_code(code, self.match_type)
                if not match_exists_with_code:
                    break
            
            # Generate group name
            self.group_name = code
            self.room_group_name = "chat_%s" % self.group_name

            # Create match 
            self.match_obj = await create_match({'code':code, 'created_by_id':self.scope['user'].id, 'match_type':self.match_type})

            # Join room
            await self.join_player_to_match()
            
            # Send room code in response
            response.update({'status': 'success', 'room': 'create', 
                             'room_code': self.group_name})

        if response:
            await self.accept()
            if self.is_created:
                await total_match(self.scope['user'])
            await self.broadcast_message_to_client(self.room_group_name, response)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        await self.play_game(message)

    async def disconnect(self, close_code):
        if not self.scope['user'].is_authenticated:
            return
        
        await self.disconnect_from_group(self.room_group_name, self.channel_name, self.group_name, self.match_type)

    async def generate_random_code(self): 
        code = random.randint(1000, 9999)  # Generate a random integer between 1000 and 9999
        return code
    

class OnlineMatchConsumer(AsyncWebsocketConsumer, CarromPlayGame):

    match_type = 0
    
    async def check_validation(self):
        # 1. city to join with is really exist
        self.match_city_obj = await get_match_city(self.city_index)
        if not self.match_city_obj:
            return False
        
        # 2. user has enough coin to join with city match
        has_enough_coin = await user_has_enough_coin(self.scope['user'].id, self.match_city_obj.entry_fee)
        if not has_enough_coin:
            return False

        return True
    
    async def join_player_to_match(self, match_id):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await create_match_user({'match_id': match_id, 'user_id':self.scope['user'].id,
                                'status':0, 'city':self.match_city_obj})


    async def connect(self):
        if not self.scope['user'].is_authenticated:
            return
        
        # Get city index
        self.city_index = str(self.scope['query_string'], 'UTF-8').split("/")[-1].split("=")[-1]

        is_validate = await self.check_validation()
        if not is_validate:
            return 
        
        # -------- Join or create match --------
        self.is_red = False
        self.is_red_last = False

        # Is any pending match for city ?
        pending_city_match = await get_pending_city_match(self.match_city_obj.id)
        
        # Join to play with
        if pending_city_match:
            # Get match object
            self.match_obj = await get_match_data({'id': pending_city_match.match_id})
            
            # Group name
            self.group_name = self.match_obj.code

            # Join channel to play 
            await self.join_player_to_match(pending_city_match.match_id)
            
            # Now all players status changes to running
            await update_match_user(params_to_filter={'match_id':pending_city_match.match_id},
                              params_to_update={'status':1})
            
            # charge entry fee to players
            player_coin_data = await charge_entry_fee(pending_city_match)
            
            # Update start_time of match
            await update_match(params_to_filter={'id': self.match_obj.id},
                               params_to_update={'start_time': datetime.now()})

            # Take random player to send
            match_data = await self.select_random_player(pending_city_match.match_id)

            # Data to send
            response = {'game_data': True, 'status': 'success', 'room': 'join',
                        'player': match_data['user__user_id'],
                        'player_user_name': match_data['user__username'],
                        'cookie_data': self.cookie_initial_position,
                        'player_coin_data': player_coin_data,
                        }

        # Create a new match
        else:
            # Make group to play
            total_group = await database_sync_to_async(Match.objects.filter(match_type=self.match_type).count)()
            self.group_name = f'Group_{total_group}'

            # make entry in match and match_user
            self.match_obj = await create_match({'code':self.group_name,'match_type':self.match_type,
                                                'status':1,'created_by_id':self.scope['user'].id})
            # Join room
            await self.join_player_to_match(self.match_obj.id)
           
            response = {'status': 'success', 'room': 'create'}
        
        self.room_group_name = self.group_name
        
        # Connect to socket
        await self.accept()
            
        # Broadcast message
        await self.broadcast_message_to_client(self.group_name, response)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        await self.play_game(message)

    async def disconnect(self, close_code):
        if not self.scope['user'].is_authenticated:
            return

        await self.disconnect_from_group(self.group_name, self.channel_name, self.group_name, self.match_type)