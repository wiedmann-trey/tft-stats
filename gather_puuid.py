import requests
import time
import csv
from config import config, api_key

'''
We want to be able to spectate all the players in Challenger. 
The API gives an endpoint to get these players, from which we can get their summonerId's. 
However, to spectate a player, we need their PUUID, which comes from a different endpoint.
'''

def get_challenger_league():
    url = config['api']['challenger_league_url'].format(key=api_key)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [entry["summonerId"] for entry in data["entries"]]
    else:
        print(f"Error fetching Challenger league data: {response.status_code}")
        return []

def get_puuid(summoner_id):
    time.sleep(float(config["time"]["api_sleep_secs"]))
    url = config['api']['summoners_url'].format(summoner_id=summoner_id, key=api_key)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data[0]["puuid"]
    else:
        print(f"Error fetching data for summoner ID {summoner_id}: {response.status_code}")
        return None

def gather():
    print("Fetching Challenger league summoner IDs")
    summoner_ids = get_challenger_league()

    if not summoner_ids:
        print("No summoner IDs found. Exiting")
        return

    print("Fetching PUUIDs for each summoner")
    puuid_list = []
    for summoner_id in summoner_ids:
        puuid = get_puuid(summoner_id)
        if puuid:
            puuid_list.append(puuid) 

    print(f"Saving {len(puuid_list)} PUUIDs to puuids.csv")
    with open(config['dirs']['puuids_path'], "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for puuid in puuid_list:
            writer.writerow([puuid])

    print("PUUIDs successfully saved to puuids.csv")

    return puuid_list

if __name__ == "__main__":
    gather()
