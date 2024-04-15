import requests
import logging

from netatmo_home import NetatmoHome

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)


class InvalidHomeNameException(Exception):
    pass


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class NetatmoClient:
    def __init__(self, bearer_auth_token):
        self.api_endpoint = 'https://api.netatmo.com/api'
        self.bearer_auth_token = bearer_auth_token

    def get_homes_names(self):
        response = requests.get(self.api_endpoint + '/homesdata', auth=BearerAuth(self.bearer_auth_token))
        homes = response.json()['body']['homes']
        return list(map(lambda x: x['name'], homes))

    def get_home_by_name(self, home_name: str):
        response = requests.get(self.api_endpoint + '/homesdata', auth=BearerAuth(self.bearer_auth_token))
        response.raise_for_status()
        homes = response.json()['body']['homes']
        filtered_homes = list(filter(lambda x: x['name'] == home_name, homes))
        if len(filtered_homes) < 1:
            raise InvalidHomeNameException(home_name)
        home = filtered_homes[0]
        logging.info(home)
        rooms_ids = [r['id'] for r in home['rooms']]
        return NetatmoHome(id=home['id'], name=home['name'], rooms=rooms_ids)

    def get_sp_temp(self, home_id):
        response = requests.get(self.api_endpoint + '/homestatus?home_id=' + home_id,
                                auth=BearerAuth(self.bearer_auth_token))
        response.raise_for_status()
        sp_temp_by_rooms: dict = {}
        for r in response.json()['body']['home']['rooms']:
            sp_temp_by_rooms[r['id']] = r['therm_setpoint_temperature']
        return sp_temp_by_rooms

    def set_sp_temp(self, home_id, room_id, sp_temp):
        params = {
            'home_id': home_id,
            'room_id': room_id,
            'temp': sp_temp,
            'mode': 'manual'
        }
        response = requests.post(self.api_endpoint + '/setroomthermpoint', params=params,
                                 auth=BearerAuth(self.bearer_auth_token))
        response.raise_for_status()
        return
