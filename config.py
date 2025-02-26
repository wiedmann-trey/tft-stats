import configparser
import os

config = configparser.ConfigParser()
config.read("config.ini")

api_key = os.getenv('API_KEY')

p = config["dirs"]["data_dir"]
if not os.path.exists(p):
    os.makedirs(p)

p = config["dirs"]["data_dir"]+"\\"+config["dirs"]["fresh_data_folder"]
if not os.path.exists(p):
    os.makedirs(p)

p = config["dirs"]["data_dir"]+"\\"+config["dirs"]["processed_data_folder"]
if not os.path.exists(p):
    os.makedirs(p)