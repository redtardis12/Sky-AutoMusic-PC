import json
import time
import keyboard
import pydirectinput
import codecs
import pygetwindow as gw
import chardet
from multiprocessing import Value, Manager

def convert_to_utf8(input_file, output_file):
    """
    Convert a JSON file from any encoding to UTF-8.
    
    Args:
    input_file (str): Path to the input JSON file.
    output_file (str): Path to the output JSON file.
    """

    with open(input_file, 'rb') as file:
        raw_data = file.read()
    
    detected_encoding = chardet.detect(raw_data)['encoding']
    if detected_encoding == 'UTF-8':
        return

    decoded_data = raw_data.decode(detected_encoding)

    json_data = json.loads(decoded_data)

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)


class MusicHandler:
    exitProgram = False
    pauseProgram = False
    data = None
    config = None

    def __init__(self, file_path, max_notes, curr_note, config):
        self.file_path = file_path
        self.config = config
        self.data = self.read_json_file(file_path)

        notes = self.data[0]['songNotes']
        bpm = self.data[0]['bpm']
        self.start_key, self.stop_key = self.get_hotkeys()

        keyboard.add_hotkey(self.stop_key, lambda: self.pause())
        while not self.exitProgram:
                keyboard.wait(self.start_key)
                self.pauseProgram = False
                time.sleep(2)
                if gw.getActiveWindowTitle() == 'Sky':
                    self.simulate_keyboard_presses(notes, bpm, max_notes, curr_note)
    

    def get_hotkeys(self):
        keys = self.config.read_config()["music"]
        return keys["start_key"]["scan_code"], keys["stop_key"]["scan_code"]

    def read_json_file(self, file_path):
        convert_to_utf8(self.file_path, self.file_path)
        with codecs.open(file_path, 'r', 'utf-8', 'ignore') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON file: {file_path}. Probably wrong encoding, please make sure that your file is in UTF-8.")
    
    def quit(self):
        self.exitProgram=True
    
    def pause(self):
        self.pauseProgram = True
    
    def simulate_keyboard_presses(self, notes, bpm, max_notes, curr_note):

        hold_time = 0.05

        key_mapping = self.config.read_config()["music"]["key_mapping"]

        notes_dict = {}
        for note in notes:
            if note['time'] in notes_dict:
                notes_dict[note['time']].append(key_mapping.get(note['key'][4:]))
            else:
                notes_dict[note['time']] = [key_mapping.get(note['key'][4:])]
        notes = list(notes_dict.items())
    

        beat_interval = 60 / bpm  # Seconds per beat

        last_time_ms = 0
        pydirectinput.PAUSE=None

        max_notes.value = len(notes)
        curr_note.value = 0

        for note in notes:
            if self.pauseProgram: break
            current_time_ms = note[0]
            if last_time_ms != 0:
                time_delay = (current_time_ms - last_time_ms) / 1000.0
            else:
                time_delay = current_time_ms / 1000.0

            time.sleep(time_delay * beat_interval)

            key_to_press = note[1]
            if key_to_press:
                pydirectinput.hotkey(*key_to_press, wait=hold_time)
                # print(f"Pressed {key_to_press} at time {current_time_ms}, note {curr_note.value}")
                curr_note.value += 1

            last_time_ms = current_time_ms

def mstart(file, max_notes, curr_note, config):
    ms = MusicHandler(file, max_notes, curr_note, config)