import json
from pathlib import Path
import requests
import pandas as pd
from config import config, api_key
import ast
import time

def load_json(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data

def save_json(json_path, data):
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=4)

def update_stat(player, stats_df):
    placement = player["placement"]
    augments = player["augments"]
    augment_rounds = ast.literal_eval(config["game"]["augment_rounds"])
    for i in range(3):
        if augments[i] == "?":
            continue
        augment = f'{augments[i]} ({augment_rounds[i]})'
        if augment not in stats_df.index:
            stats_df.loc[augment] = [0.0, 0.0, 0.0, 0, 0, 0, 0]
        stats_df.at[augment, "Games"] += 1
        stats_df.at[augment, "Total Placement"] += placement
        if placement == 1:
            stats_df.at[augment, "Firsts"] += 1
        if placement <= 4:
            stats_df.at[augment, "Top 4s"] += 1
        stats_df.at[augment, "AVP"] = stats_df.at[augment, "Total Placement"]/stats_df.at[augment, "Games"]
        stats_df.at[augment, "First Rate"] = stats_df.at[augment, "Firsts"]/stats_df.at[augment, "Games"]
        stats_df.at[augment, "Top 4 Rate"] = stats_df.at[augment, "Top 4s"]/stats_df.at[augment, "Games"]

def collect_game_stats(game_dir, stats_df):
    data = load_json(game_dir)

    for player in data['info']['participants']:
        update_stat(player, stats_df)

def process_fresh_game(game_path):
    fresh_data = load_json(game_path)

    game_id = game_path.stem

    time.sleep(float(config["time"]["api_sleep_secs"]))
    url = config["api"]["match_url"].format(match_id=game_id, key=api_key)
    response = requests.get(url)
    if response.status_code != 200:
        print("API Error")
        return
    
    api_data = response.json()

    api_data["info"]["portal"] = fresh_data["portal"]

    for participant in api_data["info"]["participants"]:
        puuid = participant["puuid"]
        participant["augments"] = fresh_data[puuid]

    save_json(Path(config["dirs"]["data_dir"] + '\\' + config["dirs"]["processed_data_folder"] + "\\" + game_id + ".json"), api_data)

    game_path.unlink()

def process_fresh_games():
    fresh_data_dir = Path(config["dirs"]["data_dir"] + '\\' + config["dirs"]["fresh_data_folder"]) 

    for game in fresh_data_dir.iterdir():
        process_fresh_game(game)

def main():
    process_fresh_games()

    columns = ["Name", "AVP", "First Rate", "Top 4 Rate", "Games", "Total Placement", "Firsts", "Top 4s"]

    stats_df = pd.DataFrame(columns=columns)

    stats_df.set_index("Name", inplace=True)
    
    processed_directory = Path(config["dirs"]["data_dir"] + '\\' + config["dirs"]["processed_data_folder"]) 

    for game in processed_directory.iterdir():
        collect_game_stats(game, stats_df)

    stats_df.to_csv(config["dirs"]["stats_save_path"])

if __name__ == "__main__":
    main()