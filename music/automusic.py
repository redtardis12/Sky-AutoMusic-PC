import codecs
import json
import time
from multiprocessing import Manager, Value

import chardet
import keyboard
import pydirectinput
import pygetwindow as gw


def convert_to_utf8(input_file, output_file):
    """
    Convert a JSON file from any encoding to UTF-8.

    Args:
    input_file (str): Path to the input JSON file.
    output_file (str): Path to the output JSON file.
    """

    with open(input_file, "rb") as file:
        raw_data = file.read()

    detected_encoding = chardet.detect(raw_data)["encoding"]
    if detected_encoding == "UTF-8":
        return

    decoded_data = raw_data.decode(detected_encoding)

    json_data = json.loads(decoded_data)

    with open(output_file, "w", encoding="utf-8") as file:
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

        notes = self.data[0]["songNotes"]
        bpm = self.data[0]["bpm"]
        self.start_key, self.stop_key = self.get_hotkeys()

        keyboard.add_hotkey(self.stop_key, lambda: self.pause())
        while not self.exitProgram:
            keyboard.wait(self.start_key)
            self.pauseProgram = False
            time.sleep(2)
            if gw.getActiveWindowTitle() == "Sky":
                self.simulate_keyboard_presses(notes, bpm, max_notes, curr_note)

    def get_hotkeys(self):
        keys = self.config.read_config()["music"]
        return keys["start_key"]["scan_code"], keys["stop_key"]["scan_code"]

    def read_json_file(self, file_path):
        convert_to_utf8(self.file_path, self.file_path)
        with codecs.open(file_path, "r", "utf-8", "ignore") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                raise ValueError(
                    f"Invalid JSON file: {file_path}. Probably wrong encoding, please make sure that your file is in UTF-8."
                )

    def quit(self):
        self.exitProgram = True

    def pause(self):
        self.pauseProgram = True

    def simulate_keyboard_presses(self, notes, bpm, max_notes, curr_note):

        hold_time = 0.05

        key_mapping = self.config.read_config()["music"]["key_mapping"]

        notes_dict = {}
        for note in notes:
            if note["time"] in notes_dict:
                notes_dict[note["time"]].append(key_mapping.get(note["key"][4:]))
            else:
                notes_dict[note["time"]] = [key_mapping.get(note["key"][4:])]
        notes = list(notes_dict.items())

        last_time_ms = 0
        pydirectinput.PAUSE = None

        max_notes.value = len(notes)
        curr_note.value = 0

        start_time = time.perf_counter()
        paused_time = 0.0
        pause_start = None

        for note in notes:
            target_time = note[0] / 1000.0

            while True:
                # Handle pausing
                if self.pauseProgram:
                    if pause_start is None:
                        pause_start = time.perf_counter()

                    time.sleep(0.01)
                    continue

                # Resume
                if pause_start is not None:
                    paused_time += time.perf_counter() - pause_start
                    pause_start = None

                elapsed = time.perf_counter() - start_time
                remaining = target_time - elapsed

                if remaining <= 0:
                    break

                time.sleep(min(remaining, 0.001))

            if self.pauseProgram:
                    continue

            pydirectinput.hotkey(*note[1], wait=hold_time)


def mstart(file, max_notes, curr_note, config):
    ms = MusicHandler(file, max_notes, curr_note, config)
