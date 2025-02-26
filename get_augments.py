import pyautogui
import pydirectinput
import easyocr
from fuzzywuzzy import fuzz
import cv2
import time
import numpy as np
import json
import re
import ast

from config import config

def clean_string(s):
    return re.sub(r'[^\w\s+]', '', s.strip().lower())

def upscale(screenshot, scale_factor=2):
    image = np.array(screenshot)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    image = cv2.resize(image, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    image = cv2.threshold(image, 130, 255, cv2.THRESH_BINARY_INV)[1]

    return image

def click(pos):
    pydirectinput.moveTo(pos[0], pos[1])
    pydirectinput.mouseDown()
    time.sleep(float(config["time"]["click_time_secs"]))
    pydirectinput.mouseUp()

def right_click(pos):
    pydirectinput.moveTo(pos[0], pos[1])
    pydirectinput.mouseDown(button="right")
    time.sleep(float(config["time"]["click_time_secs"]))
    pydirectinput.mouseUp(button="right")

def get_augment_list():
    with open(config['dirs']['game_data_json'], 'r') as file:
        data = json.load(file)
    
    augment_list = {}
    for augment in data['augments'].values():
        augment_list[clean_string(augment['name'])] = augment['name']

    return augment_list

def get_portal_list():
    with open(config['dirs']['portals_json'], 'r') as file:
        data = json.load(file)
    
    portal_list = {}
    for portal in data['data'].values():
        portal_list[clean_string(portal['name'])] = portal['name']

    return portal_list

def match_portal_name(name):
    name = clean_string(name)

    if name in portal_list:
        return portal_list[name]

    best_match = None
    best_score = 0

    for portal, full_name in portal_list.items():
        score = fuzz.ratio(name, portal)
        if score >= best_score:
            best_score = score
            best_match = full_name
    
    return best_match

def match_augment_name(name):
    name = clean_string(name)

    if name in augment_list:
        return augment_list[name]

    best_match = None
    best_score = 0

    for augment, full_name in augment_list.items():
        score = fuzz.ratio(name, augment)
        if score >= best_score:
            best_score = score
            best_match = full_name
    
    if best_score < int(config["misc"]["augment_match_thresh"]):
        return "?"

    return best_match

def wait_for_game_load():
    elapsed_time = 0

    while len(pyautogui.getWindowsWithTitle(config["dirs"]["lol_window_name"])) == 0:
        time.sleep(float(config["time"]["polling_interval_secs"]))
        elapsed_time += float(config["time"]["polling_interval_secs"])
        if(elapsed_time > float(config["time"]["game_load_timeout_secs"])):
            print("Game failed to launch")
            return False
        
    time.sleep(float(config["time"]["load_delay_secs"]))
    
    pyautogui.getWindowsWithTitle(config["dirs"]["lol_window_name"])[0].maximize()

    while elapsed_time < float(config["time"]["game_load_timeout_secs"]):
        fps_region = ast.literal_eval(config["game"]["fps_region"])
        screenshot = pyautogui.screenshot(region=fps_region)

        screenshot = np.array(screenshot)

        text_detections = reader.readtext(screenshot)

        for bbox, text, score in text_detections:
            if config["game"]["fps_text"].lower() in text.strip().lower():   
                print("Match loaded!")
                return True
        
        time.sleep(float(config["time"]["polling_interval_secs"]))
        elapsed_time += float(config["time"]["polling_interval_secs"])

    print("Timeout while waiting for match to load")
    return False

def wait_for_planning():
    elapsed_time = 0
    while elapsed_time < float(config["time"]["planning_phase_timeout_secs"]):
        planning_banner_region = ast.literal_eval(config["game"]["planning_banner_region"])
        screenshot = pyautogui.screenshot(region=planning_banner_region)

        screenshot = np.array(screenshot)

        text_detections = reader.readtext(screenshot)

        for bbox, text, score in text_detections:
            if text.strip().lower() == config["game"]["planning_text"].lower():   
                print("Planning phase found!")
                return True
        
        time.sleep(float(config["time"]["polling_interval_secs"]))
        elapsed_time += float(config["time"]["polling_interval_secs"])

    print("Timeout while waiting for planning phase")
    return False

def get_place_puuid(place, player_info):
    name_regions = ast.literal_eval(config["game"]["name_regions"])

    elapsed_time = 0
    while elapsed_time < float(config["time"]["read_name_timeout_secs"]):
        screenshot = pyautogui.screenshot(region=name_regions[place])
        
        image = upscale(screenshot)

        text_detections = reader.readtext(image)

        for bbox, text, score in text_detections:
            if score > float(config["misc"]["text_thresh"]):
                text = text.strip()
                for name in player_info.keys():
                    if fuzz.ratio(name, text) >= int(config["misc"]["player_name_match_thresh"]):
                        print(f"Player {name} found!")
                        return player_info[name]

        time.sleep(float(config["time"]["polling_interval_secs"]))
        elapsed_time += float(config["time"]["polling_interval_secs"])

    print(f"Timeout while scouting")
    return None

def get_augment_sword_pos(screenshot):
    img = np.array(screenshot)
    hsv_image = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    lower_black = np.array([0, 0, 0])         
    upper_black = np.array([255, 50, 30])      

    mask = cv2.inRange(hsv_image, lower_black, upper_black)

    kernel = np.ones((10, 10), np.uint8)
    closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    augment_icons_width = int(config["game"]["augment_icons_width"])
    augment_icons_height = int(config["game"]["augment_icons_height"])
    tolerance_augment_box_px = int(config["game"]["tolerance_augment_box_px"])
    augment_icons_approx_region = ast.literal_eval(config["game"]["augment_icons_approx_region"])
    augment_sword_offset_from_icons = ast.literal_eval(config["game"]["augment_sword_offset_from_icons"])

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if abs(w-augment_icons_width) <= tolerance_augment_box_px and abs(h-augment_icons_height) <= tolerance_augment_box_px:
            return (x+augment_icons_approx_region[0]+augment_sword_offset_from_icons[0], y+augment_icons_approx_region[1]+augment_sword_offset_from_icons[1])
    
    return None

def crop_augments(screenshot):
    image = np.array(screenshot)

    text_detections = reader.readtext(image)

    crop_region = None

    augments_offset_from_header = ast.literal_eval(config["game"]["augments_offset_from_header"])
    augments_size = ast.literal_eval(config["game"]["augments_size"])

    for bbox, text, score in text_detections:
            if text.strip().lower() == "augments":
                crop_region = (bbox[0][0]+augments_offset_from_header[0], bbox[0][1]+augments_offset_from_header[1], bbox[0][0]+augments_offset_from_header[0]+augments_size[0], bbox[0][1]+augments_offset_from_header[1]+augments_size[1])
                break
    
    if not crop_region:
        print("Unable to detect augments")
        return None
    
    return screenshot.crop(crop_region)

def process_portal_text(screenshot):
    screenshot = np.array(screenshot)

    text_detections = reader.readtext(screenshot)

    best_text = None
    best_score = 0

    for bbox, text, score in text_detections:  
        if score > best_score:
            best_text = text
            best_score = score
    
    if best_text is None:
        return "?"
    
    return match_portal_name(text)

def process_augment_text(screenshot):
    screenshot = np.array(screenshot)

    text_detections = reader.readtext(screenshot)

    best_text = None
    best_score = 0

    for bbox, text, score in text_detections:  
        if score > best_score:
            best_text = text
            best_score = score
    
    if best_text is None:
        return "?"
    
    return match_augment_name(text)

def process_augment_screenshot(screenshot):
    width, height = screenshot.size

    left = width // 5 + 15
    right = width
    cropped_image = screenshot.crop((left, 0, right, height))

    section_height = height // 4

    augments = []
    portal = None

    for i in range(4):
        top = i * section_height
        bottom = (i + 1) * section_height if i < 3 else height
        crop = cropped_image.crop((0, top, cropped_image.width, bottom))

        if i == 0:
            portal = process_portal_text(crop)
            continue

        augments.append(process_augment_text(crop))

    return augments, portal

def capture_augments(puuid, game_data_path):
    augment_icons_approx_region = ast.literal_eval(config["game"]["augment_icons_approx_region"])
    screenshot = pyautogui.screenshot(region=augment_icons_approx_region)
    augment_sword_position = get_augment_sword_pos(screenshot)
    if augment_sword_position is None:
        print('Could not find augment sword')
        return None, None 
    
    right_click(augment_sword_position)

    augments_approx_region = ast.literal_eval(config["game"]["augments_approx_region"])
    screenshot = pyautogui.screenshot(region=augments_approx_region)
    screenshot = crop_augments(screenshot)
    if screenshot is None:
        return None, None
    
    right_click(augment_sword_position)

    return process_augment_screenshot(screenshot)

def main(player_info, game_data_path):
    if not wait_for_game_load():
        return False

    if not wait_for_planning():
        return False
    
    game_info_dict = {}
    game_info_dict["portal"] = "?"
    for puuid in player_info.values():
        game_info_dict[puuid] = ["?", "?", "?"]

    portrait_locations = ast.literal_eval(config["game"]["portrait_locations"])

    print("Grabbing augment data")
    for i in range(8):
        click(portrait_locations[i])

        puuid = get_place_puuid(i, player_info)
        if not puuid:
            continue

        player_augments, portal = capture_augments(puuid, game_data_path)

        if portal is not None:
            game_info_dict["portal"] = portal

        if player_augments is not None:
            game_info_dict[puuid] = player_augments

    with open(game_data_path, 'w') as output_file:
        json.dump(game_info_dict, output_file, indent=4)

    return True

reader = easyocr.Reader(['en'], gpu=True)
augment_list = get_augment_list()
portal_list = get_portal_list()