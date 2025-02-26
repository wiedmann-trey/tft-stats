import gather_puuid
import os
import subprocess
import requests
import csv
import time
import get_augments
from datetime import datetime, timedelta
import psutil
from config import config, api_key

def update_puuids(puuid_list):
    if not os.path.exists(config["dirs"]['puuids_path']):
        return gather_puuid.gather()
    
    last_modified_time = os.path.getmtime(config["dirs"]['puuids_path'])
    last_modified_datetime = datetime.fromtimestamp(last_modified_time)
    current_time = datetime.now()

    if current_time - last_modified_datetime > timedelta(hours=int(config['time']['puuid_update_rate_hrs'])):
        print("Updating list of PUUIDs")
        return gather_puuid.gather()
    
    if not puuid_list:
        with open(config["dirs"]['puuids_path'], mode="r") as file:
            print("Reading PUUIDs from CSV")
            reader = csv.reader(file)
            for row in reader:
                puuid_list.append(row[0])
            print("PUUIDs read")

    return puuid_list

def spectate_player(puuid):
    url = config['api']['spectate_url'].format(puuid=puuid, key=api_key)

    time.sleep(float(config["time"]["api_sleep_secs"]))
    response = requests.get(url)

    if response.status_code != 200:
        #print(f"Player {puuid} not in game")
        return

    data = response.json()

    if 'gameQueueConfigId' not in data:
        print(f'Error reading JSON: {url}')
        return
        
    if data['gameQueueConfigId'] != int(config['api']['queue_id']):
        #print("Player in game, but not ranked TFT")
        return

    print(f"Match found! gameId: {data['gameId']}")

    if data['gameLength'] < int(config['time']['third_augment_time_secs']):
        print('Match not past third augment')
        return

    game_data_path = config['dirs']['data_dir'] + '\\' + config['dirs']['fresh_data_folder'] + '\\' + str(data['gameId']) + ".json"

    if os.path.exists(game_data_path):
        print("Data already collected for game")
        return

    subprocess.Popen(['spectate.bat', config['dirs']['lol_dir'], data['observers']['encryptionKey'], str(data['gameId'])])
    
    player_info = dict()
    for i in range(8):
        name = data["participants"][i]["riotId"].split("#")[0]
        p = data["participants"][i]["puuid"]
        player_info[name] = p

    if(not get_augments.main(player_info, game_data_path)):
        print(f"Failed to spectate game {data['gameId']}")

    for proc in psutil.process_iter():
        if proc.name() == config['dirs']['lol_process_name']:
            proc.kill()
            print("Closing League")

def main():
    i = 0
    puuid_list = []

    while True:
        puuid_list = update_puuids(puuid_list)
        if puuid_list is None:
            return

        if i >= len(puuid_list):
            i = 0

        spectate_player(puuid_list[i])
        i+=1

if __name__ == "__main__":
    os.system("net stop vgc")
    os.system("net stop vgk")
    main()

