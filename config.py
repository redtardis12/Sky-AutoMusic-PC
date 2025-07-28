import keyboard
import json


SCHEMA = {
    "music": {
        "start_key": {
            "name": "v",
            "scan_code": 47
        },
        "stop_key": {
            "name": "b",
            "scan_code": 48
        },
        "key_mapping": {
            "0": "y",
            "1": "u",
            "2": "i",
            "3": "o",
            "4": "p",
            "5": "h",
            "6": "j",
            "7": "k",
            "8": "l",
            "9": ";",
            "10": "n",
            "11": "m",
            "12": ",",
            "13": ".",
            "14": "/"
        }
    },
    "app": {
        "always_on_top": True,
        "music_dir": "music/songs"
    }
}

class ConfigHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self._load()
    
    def _load(self):
        try:
            with open(self.file_path, 'r') as f:
                self._config = json.load(f)
                self._config = {**SCHEMA, **self._config}
        except (FileNotFoundError, json.JSONDecodeError):
            self._config = SCHEMA
            self.save()
    
    def save(self):
        with open(self.file_path, 'w') as f:
            json.dump(self._config, f, indent=4)
    
    def read_config(self):
        return {**self._config}
    
    def assign_hotkey(self, field):
        event = keyboard.read_event(suppress=True)
        if event.event_type == keyboard.KEY_DOWN and event.name != 'esc':
            scan_code = event.scan_code
            name = event.name

            field_config = {"name": name, "scan_code": scan_code} if field in ["start_key", "stop_key"] else name
            if field in ["start_key", "stop_key"]:
                self._config["music"][field] = field_config
            else:
                self._config["music"]["key_mapping"][field] = field_config

            self.save()

            return name
    
    def set_always_on_top(self, value):
        self._config["app"]["always_on_top"] = value
        self.save()

    def set_music_dir(self, value):
        self._config["app"]["music_dir"] = value
        self.save()
