from datetime import datetime, timedelta
import requests
import logging

from netatmo_home import NetatmoHome

MINUTES_BEFORE_REFRESHING = 1


class InvalidHomeNameException(Exception):
    pass


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


def refresh_token_decorator(func):
    """
    Decorator to refresh token before `func` calls the api
    """
    def wrapper(*args, **kwargs):
        self = args[0]
        self.get_refresh_token()
        args = args[1:]
        return func(self, *args, **kwargs)

    return wrapper


class NetatmoClient:
    """
    Netatmo API client
    """
    def __init__(self, client_id, client_secret, access_token, refresh_token):
        self.api_endpoint = 'https://api.netatmo.com/api'
        self.authentication_api_endpoint = 'https://api.netatmo.com'
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiration = datetime.now()
        self.client_id = client_id
        self.client_secret = client_secret

    @refresh_token_decorator
    def get_homes_names(self):
        response = requests.get(self.api_endpoint + '/homesdata', auth=BearerAuth(self.access_token))
        homes = response.json()['body']['homes']
        return list(map(lambda x: x['name'], homes))

    @refresh_token_decorator
    def get_home_by_name(self, home_name: str):
        response = requests.get(self.api_endpoint + '/homesdata', auth=BearerAuth(self.access_token))
        response.raise_for_status()
        homes = response.json()['body']['homes']
        filtered_homes = list(filter(lambda x: x['name'] == home_name, homes))
        if len(filtered_homes) < 1:
            raise InvalidHomeNameException(home_name)
        home = filtered_homes[0]
        logging.info(home)
        rooms_ids = [r['id'] for r in home['rooms']]
        return NetatmoHome(id=home['id'], name=home['name'], rooms=rooms_ids)

    @refresh_token_decorator
    def get_sp_temp(self, home_id):
        response = requests.get(self.api_endpoint + '/homestatus?home_id=' + home_id,
                                auth=BearerAuth(self.access_token))
        response.raise_for_status()
        sp_temp_by_rooms: dict = {}
        for r in response.json()['body']['home']['rooms']:
            sp_temp_by_rooms[r['id']] = r['therm_setpoint_temperature']
        return sp_temp_by_rooms

    @refresh_token_decorator
    def set_sp_temp(self, home_id, room_id, sp_temp):
        params = {
            'home_id': home_id,
            'room_id': room_id,
            'temp': sp_temp,
            'mode': 'manual'
        }
        response = requests.post(self.api_endpoint + '/setroomthermpoint', params=params,
                                 auth=BearerAuth(self.access_token))
        response.raise_for_status()
        return

    def get_refresh_token(self):
        # if token_expiration is soon (< 1 minute), refresh token
        token_expires_in = self.token_expiration - datetime.now()
        if token_expires_in > timedelta(minutes=MINUTES_BEFORE_REFRESHING):
            logging.info('No need to refresh token')
            return

        logging.debug('Refreshing token...')
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        response = requests.post(self.authentication_api_endpoint + '/oauth2/token', data=data)
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens['access_token']
            self.refresh_token = tokens['refresh_token']
            self.token_expiration = datetime.now() + timedelta(seconds=tokens['expires_in'])
            logging.info('Token refreshed successfully')
        else:
            logging.error('Failed to refresh token:', response.content)
            raise Exception('Failed to refresh token')
