import pyautogui
from pynput import keyboard

def get_mouse_position():
    position = pyautogui.position()
    print(f"Mouse position: {position}")

def on_press(key):
    try:              
        if key == keyboard.Key.space:
            get_mouse_position()
        elif key == keyboard.Key.esc:
            print("Exiting")
            return False
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Press the space bar to get the mouse position. Press ESC to exit.")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    main()
