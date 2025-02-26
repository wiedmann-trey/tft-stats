import configparser
import os

config = configparser.ConfigParser()
config.read("config.ini")

api_key = os.getenv('API_KEY')