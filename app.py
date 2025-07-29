import os
import shutil
import multiprocessing
import time
from music.automusic import mstart
from config import ConfigHandler
import dearpygui.dearpygui as dpg
import threading
import json
import sys
import webbrowser

music_proc = None
selected_song = None
config = ConfigHandler("config.json")
music_folder = config.read_config()["app"]["music_dir"]
music_folder = music_folder if music_folder else "music/songs/"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_music_files():
    try:
        if not os.path.exists(music_folder):
            if os.path.relpath(music_folder).startswith(("music/songs", "music\songs")):
                os.makedirs(music_folder, exist_ok=True)
                return []
        radio_list = []
        for midi_file in os.listdir(music_folder):
            if midi_file.endswith(".txt") or midi_file.endswith(".json"):
                radio_list.append(midi_file)
        return radio_list
    except:
        return []

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

    destination_folder = music_folder
    os.makedirs(destination_folder, exist_ok=True)

    for file_name, file_path in app_data['selections'].items():
        new_file_path = os.path.join(destination_folder, file_name)
        try:
            shutil.copy(file_path, new_file_path)
        except Exception as err:
            raise Exception(f"Error copying {file_path} to {new_file_path}: {err}")
    dpg.configure_item("radio_btn", items=get_music_files())


# Manages the music playback process by starting or stopping it based on the current state
def music_hotkeys():
    global music_proc, selected_song, m, c, bar_thread
    if not selected_song:
        return
    if not music_proc:
        f = os.path.join(music_folder, selected_song)
        m = multiprocessing.Value('i', 1)
        c = multiprocessing.Value('i', 0)
        music_proc = multiprocessing.Process(target=mstart, args=(f,m,c, config))
        music_proc.start()
        dpg.set_item_label("play_btn", "Stop")
        print("Started music")
        bar_thread = threading.Thread(target=update_progress_bar, args=(), daemon=True)
        bar_thread.start()
    else:
        stop_hotkeys()
        dpg.set_item_label("play_btn", "Start")
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

def update_progress_bar():
    while c.value < m.value and m.value > 0 and music_proc.is_alive():
        progress = c.value / m.value
        dpg.set_value("progress_bar", min(progress, 1.0))
    dpg.set_value("progress_bar", 0)


def show_current_music_speed():
    if not selected_song:
        dpg.set_value("speed_slider", 0)
        return
    with open(os.path.join(music_folder, selected_song), 'r') as file:
        data = json.load(file)
        dpg.set_value("speed_slider", data[0]["bpm"])

def change_current_music_speed(sender, app_data, user_data):
    if not selected_song:
        return
    
    with open(os.path.join(music_folder, selected_song), 'r') as file:
        data = json.load(file)
        data[0]["bpm"] = dpg.get_value("speed_slider")
    with open(os.path.join(music_folder, selected_song), 'w') as file:
        json.dump(data, file)
    dpg.configure_item("modal_id", show=False)
    restart_hotkeys(sender, selected_song, user_data)

def update_hotkeys_binds(sender, app_data, user_data):
    if music_proc:
        stop_hotkeys()
    dpg.configure_item("advanced_settings", show=False)
    time.sleep(0.1)
    dpg.configure_item("hotkey_popup", show=True)
    dpg.set_item_label(sender, config.assign_hotkey(user_data))
    dpg.configure_item("hotkey_popup", show=False)
    time.sleep(0.1)
    dpg.configure_item("advanced_settings", show=True)

def update_music_dir(sender, app_data, user_data):
    global music_folder
    if music_proc:
        stop_hotkeys()
    music_dir = app_data["file_path_name"]
    if os.path.isdir(music_dir):
        music_folder = music_dir
        config.set_music_dir(music_folder)
        dpg.configure_item("radio_btn", items=get_music_files())
    dpg.configure_item("music_folder_input", default_value=f"{(music_folder[:20] + '...') if len(music_folder) > 40 else music_folder}")


def update_always_on_top(sender, app_data, user_data):
    dpg.configure_viewport(0, always_on_top=app_data)
    config.set_always_on_top(app_data)
    
        
    

def main():
    dpg.create_context()
    apply_dark_purple_theme()
    dpg.create_viewport(title='Sky AutoMusic PC', width=800, height=600, always_on_top=config.read_config()["app"]["always_on_top"])
    icon = resource_path("icon.ico")
    dpg.set_viewport_small_icon(icon)
    dpg.set_viewport_large_icon(icon)

    # Main window
    with dpg.window(label="Main", no_title_bar=True, no_resize=True, no_move=True, no_close=True, tag="main_window"):
        with dpg.menu_bar():
            dpg.add_menu_item(label="Add music", callback=lambda: dpg.show_item("file_picker"))
            dpg.add_menu_item(label="Settings", callback=lambda: dpg.show_item("advanced_settings"))
            with dpg.menu(label="Help"):
                dpg.add_menu_item(label="How to use?", callback=lambda: dpg.show_item("howto_window"))
                dpg.add_menu_item(label="About", callback=lambda: dpg.show_item("about_window"))

        with dpg.child_window(tag="content_area", autosize_x=True, height=-50, horizontal_scrollbar=False):
            dpg.add_text("Songs:")
            radio_list = get_music_files()
            with dpg.group(horizontal=False, tag="music_list"):
                dpg.add_radio_button(items=radio_list, callback=restart_hotkeys, default_value=False, tag="radio_btn")

        # Docked bottom bar
        with dpg.group(horizontal=True):
            dpg.add_button(label="Start", tag="play_btn", width=60, callback=music_hotkeys)
            dpg.add_progress_bar(tag="progress_bar", default_value=0.0, width=600)
            dpg.add_button(label="Edit..", width=70, tag="settings_btn")

            with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Left, modal=True, tag="modal_id"):
                dpg.add_text("Change current music speed (Press Ctrl + LMB to input manually)")
                dpg.add_slider_int(label="", min_value=1, max_value=800, default_value=1, tag="speed_slider", no_input=False)
                dpg.add_button(label="Save", callback=change_current_music_speed)
    
    with dpg.window(label="How to use?", tag="howto_window", show=False, modal=True, width=750, height=400):
        dpg.add_text("How to use:", color=(0, 255, 0))
        dpg.add_text("1. Download the music sheet file from anywhere in .txt or .json format.")
        dpg.add_text("2. Press the 'Add music' button and select the music sheet file (you can add multiple songs" \
        "\nYou can also just put files in the 'app_location/music/songs' folder (it can be changed in settings).")
        dpg.add_separator()
        dpg.add_text("3. Choose the music from the list and press 'Start'. " \
        "\nAfter that the app will wait for you to press a Start keybind while in the game.")
        dpg.add_text("You can press pause keybind to stop the music while it is playing")
        dpg.add_text("Buttons are V and B by default. You can change both keybinds in the settings.", color=(0, 255, 0))
        dpg.add_separator()
        dpg.add_text("4. Press the 'Edit' button and change the music speed.")
        dpg.add_text("5. Press the 'Stop' button again to stop the app detecting your keybinds.")
    
    with dpg.window(label="About", tag="about_window", show=False, modal=True, width=400, height=200):
        dpg.add_text("Sky AutoMusic PC", color=(0, 255, 0))
        dpg.add_text("Version 1.0.0")
        dpg.add_text("Author: killey_")
        dpg.add_button(label="Report Issues on Github", callback=lambda:webbrowser.open("https://github.com/redtardis12/Sky-AutoMusic-PC"))
    
    # Settings Window
    with dpg.window(label="Settings", tag="advanced_settings", show=False, modal=True, width=400):
        dpg.add_text("Keybinds:")

        with dpg.group(horizontal=True):
            dpg.add_text("Play key: ")
            dpg.add_button(label=f"{config.read_config()['music']['start_key']['name']}", callback=update_hotkeys_binds, user_data="start_key", width=100, indent=100)
        with dpg.group(horizontal=True):
            dpg.add_text(f"Pause key: ")
            dpg.add_button(label=f"{config.read_config()['music']['stop_key']['name']}", callback=update_hotkeys_binds, user_data="stop_key", width=100, indent=100)
        
        with dpg.collapsing_header(label="Note keybinds"):
            for key in config.read_config()["music"]["key_mapping"].keys():
                with dpg.group(horizontal=True):
                    dpg.add_text(f"Note {key}: ")
                    dpg.add_button(label=f"{config.read_config()['music']['key_mapping'][key]}",
                                    callback=update_hotkeys_binds,
                                    user_data=f"{key}",
                                    indent=100,
                                    width=100)
        
        dpg.add_separator()

        dpg.add_text("App settings:")
        with dpg.group(horizontal=True):
            dpg.add_text("Always on top: ")
            dpg.add_checkbox(default_value=config.read_config()["app"]["always_on_top"], callback=update_always_on_top)
        
        with dpg.group(horizontal=True):
            dpg.add_text("Music folder: ")
            dpg.add_input_text(default_value=f"{(music_folder[:20] + '..') if len(music_folder) > 40 else music_folder}", tag="music_folder_input", readonly=True, width=200)
            dpg.add_button(label=f"..", callback=lambda: dpg.show_item("folder_picker"), width=40)
        
        with dpg.window(modal=True, tag="hotkey_popup", no_title_bar=True, no_resize=True, no_move=True, no_close=True, width=400, height=100, show=False):
            dpg.add_text("Press a key to assign a hotkey")
            dpg.add_text("(Press Esc to cancel)")
        
        dpg.add_file_dialog(label="Select music folder", modal=True, directory_selector=True, show=False, callback=update_music_dir, tag="folder_picker", width=700, height=400)


    with dpg.file_dialog(directory_selector=False, show=False, callback=copy_music, tag="file_picker", width=700, height=400):
        dpg.add_file_extension(".txt")
        dpg.add_file_extension(".json")
    

    # Resize the child window to leave 90px for the bottom bar
    def resize_content(sender, app_data):
        width = dpg.get_viewport_client_width()
        height = dpg.get_viewport_client_height()
        dpg.set_item_width("main_window", width)
        dpg.set_item_height("main_window", height)
        dpg.set_item_height("content_area", height - 90)

    dpg.set_viewport_resize_callback(resize_content)
    resize_content(None, None)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
    stop_hotkeys()

def apply_dark_purple_theme():
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            # Background & Frames
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (25, 25, 35), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive , (50, 50, 60), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (20, 20, 30), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (40, 40, 60), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (100, 60, 150), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (130, 70, 200), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (150, 90, 240), category=dpg.mvThemeCat_Core)

            # Buttons
            dpg.add_theme_color(dpg.mvThemeCol_Button, (90, 50, 160), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (120, 70, 200), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (150, 90, 240), category=dpg.mvThemeCat_Core)

            # Radio buttons
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (150, 90, 240), category=dpg.mvThemeCat_Core)

            # Progress bars
            dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, (140, 80, 240), category=dpg.mvThemeCat_Core)

            # Text
            dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 255), category=dpg.mvThemeCat_Core)

            # Sliders and progress bars
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (140, 80, 240), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (180, 110, 255), category=dpg.mvThemeCat_Core)

            # Rounding and spacing
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)

            # Padding and spacing
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 10)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 15, 15)

            dpg.add_theme_style(dpg.mvStyleVar_IndentSpacing, 20)

    dpg.bind_theme(global_theme)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
