import json
import logging
import time
from typing import Dict

from netatmo_client import NetatmoClient

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

if __name__ == '__main__':
    # Init
    with open('config.json', 'r') as f:
        config = json.load(f)

    bearer_auth_token = config['authToken']
    home_name = config['homeName']
    cap_sp_temp = config['maxTemperature']
    seconds_between_checks = config['secondsBetweenChecks']

    client = NetatmoClient(bearer_auth_token)

    home = client.get_home_by_name(home_name)
    home_id = home.id

    while True:
        sp_temp_by_rooms: Dict[str, str] = client.get_sp_temp(home_id)

        for room in home.rooms:
            sp_temp = sp_temp_by_rooms[room]
            logging.info('room_id: %s,current sp_temp = %.1f', room, sp_temp)

            if sp_temp <= cap_sp_temp:
                logging.info('Nothing to do')
                continue

            client.set_sp_temp(home_id, room_id=room, sp_temp=cap_sp_temp)
            logging.info('Turned back to %s', cap_sp_temp)
        time.sleep(seconds_between_checks)
