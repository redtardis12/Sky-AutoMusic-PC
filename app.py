import os
import shutil
import multiprocessing
from music.automusic import mstart, assign_hotkey, assign_note_key
from config import ConfigHandler
import dearpygui.dearpygui as dpg
import threading
import json

music_proc = None
selected_song = None
config = ConfigHandler("config.json")


def stop_hotkeys():
    global music_proc
    if music_proc:
        music_proc.terminate()
        music_proc.join()
        music_proc = None
        print("Stopped music")

def copy_music(sender, app_data, user_data):
    if not app_data['selections']:
        return

    destination_folder = "music/songs/"
    os.makedirs(destination_folder, exist_ok=True)

    for file_path in app_data['selections']:
        file_name = os.path.basename(file_path)
        new_file_path = os.path.join(destination_folder, file_name)
        try:
            shutil.copy(file_path, new_file_path)
        except Exception as err:
            print(f"Error copying {file_path}: {err}")
        dpg.add_radio_button(items=[file_name], callback=restart_hotkeys, parent="music_list")

def music_hotkeys():
    global music_proc, selected_song, m, c, bar_thread
    if not selected_song:
        return
    if not music_proc:
        f = os.path.join("music/songs", selected_song)
        m = multiprocessing.Value('i', 1)
        c = multiprocessing.Value('i', 0)
        music_proc = multiprocessing.Process(target=mstart, args=(f,m,c))
        music_proc.start()
        dpg.set_item_label("play_btn", "Pause")
        print("Started music")
        bar_thread = threading.Thread(target=update_progress_bar, args=(), daemon=True)
        bar_thread.start()
    else:
        stop_hotkeys()
        dpg.set_item_label("play_btn", "Play")
        m = multiprocessing.Value('i', 1)
        c = multiprocessing.Value('i', 0)
        print("Stopped music")
        

def restart_hotkeys(sender, app_data, user_data):
    global music_proc, selected_song
    selected_song = app_data
    show_current_music_speed()
    print(f"Selected: {selected_song}")
    if music_proc:
        stop_hotkeys()
        music_hotkeys()
        print("Restarted music")

def update_progress_bar():
    while c.value < m.value and m.value > 0 and music_proc.is_alive():
        progress = c.value / m.value
        dpg.set_value("progress_bar", min(progress, 1.0))


def show_current_music_speed():
    if not selected_song:
        dpg.set_value("speed_slider", 0)
        return
    with open(os.path.join("music/songs", selected_song), 'r') as file:
        data = json.load(file)
        dpg.set_value("speed_slider", data[0]["bpm"])

def change_current_music_speed(sender, app_data, user_data):
    if not selected_song:
        return
    
    with open(os.path.join("music/songs", selected_song), 'r') as file:
        data = json.load(file)
        data[0]["bpm"] = dpg.get_value("speed_slider")
    with open(os.path.join("music/songs", selected_song), 'w') as file:
        json.dump(data, file)
    dpg.configure_item("modal_id", show=False)
    restart_hotkeys(sender, selected_song, user_data)

def update_hotkeys_binds(sender, app_data, user_data):
    if music_proc:
        stop_hotkeys()
    dpg.set_item_label(sender, config.assign_hotkey(user_data))
    
        
    

def main():
    dpg.create_context()
    dpg.create_viewport(title='Sky: Keys interactive', width=800, height=600)

    # Main window
    with dpg.window(label="Main", no_title_bar=True, no_resize=True, no_move=True, no_close=True, tag="main_window"):
        with dpg.menu_bar():
            dpg.add_menu_item(label="Add music", callback=lambda: dpg.show_item("file_picker"))
            dpg.add_menu_item(label="Settings", callback=lambda: dpg.show_item("advanced_settings"))
        with dpg.child_window(tag="content_area", autosize_x=True, height=-50, horizontal_scrollbar=False):
            dpg.add_text("Songs:")
            radio_list = []
            with dpg.group(horizontal=False, tag="music_list"):
                for midi_file in os.listdir("music/songs/"):
                    if midi_file.endswith(".txt") or midi_file.endswith(".json"):
                        radio_list.append(midi_file)
                dpg.add_radio_button(items=radio_list, callback=restart_hotkeys, default_value=False)

        # Docked bottom bar
        with dpg.group(horizontal=True):
            dpg.add_button(label="Play", tag="play_btn", width=60, callback=music_hotkeys)
            dpg.add_progress_bar(tag="progress_bar", default_value=0.0, width=640)
            dpg.add_button(label="⚙", width=30, tag="settings_btn")

            with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Left, modal=True, tag="modal_id"):
                dpg.add_text("Change current music speed (Press Ctrl + LMB to input manually)")
                dpg.add_slider_int(label="", min_value=1, max_value=800, default_value=1, tag="speed_slider", no_input=False)
                dpg.add_button(label="Save", callback=change_current_music_speed)
    
    # Collapsible Settings Window
    with dpg.window(label="Advanced Settings", tag="advanced_settings", show=False):
        dpg.add_text("Keybinds:")

        with dpg.group(horizontal=True):
            dpg.add_text("Start key: ")
            dpg.add_button(label=f"{config.get_json()['music']['start_key']['name']}", callback=update_hotkeys_binds, user_data="start_key")
        with dpg.group(horizontal=True):
            dpg.add_text(f"Stop key: ")
            dpg.add_button(label=f"{config.get_json()['music']['stop_key']['name']}", callback=update_hotkeys_binds, user_data="stop_key")
        
        dpg.add_text("Key mapping:")
        for key in config["music"]["key_mapping"].keys():
            with dpg.group(horizontal=True):
                dpg.add_text(f"Note {key}: ")
                dpg.add_button(label=f"{config.get_json()['music']['key_mapping'][key]}", callback=update_hotkeys_binds, user_data=f"{key}")




    # File picker
    with dpg.file_dialog(directory_selector=False, show=False, callback=copy_music, tag="file_picker", width=700, height=400):
        dpg.add_file_extension("*.txt")
        dpg.add_file_extension("*.json")

    # Resize the child window to leave 50px for the bottom bar
    def resize_content(sender, app_data):
        width = dpg.get_viewport_client_width()
        height = dpg.get_viewport_client_height()
        dpg.set_item_width("main_window", width)
        dpg.set_item_height("main_window", height)
        dpg.set_item_height("content_area", height - 70)

    dpg.set_viewport_resize_callback(resize_content)
    resize_content(None, None)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
    stop_hotkeys()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
