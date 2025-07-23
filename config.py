import keyboard
import json

class ConfigHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self._load()
    
    def _load(self):
        try:
            with open(self.file_path, 'r') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            self._config = {}
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in {self.file_path}")
    
    def save(self, new_config=None):
        if new_config is not None:
            self._config = new_config
        with open(self.file_path, 'w') as f:
            json.dump(self._config, f, indent=4)
    
    def read_config(self):
        return self._config
    
    def assign_hotkey(self, field):
        event = keyboard.read_event(suppress=True)
        if event.event_type == keyboard.KEY_DOWN:
            scan_code = event.scan_code
            name = event.name
            if name == 'esc':
                return

            new_config = self._config

            if field == "start_key" or field == "stop_key":
                new_config["music"][field] = {
                    "name": name,
                    "scan_code": scan_code
                }
            else:
                new_config["music"]["key_mapping"][field] = name

            self.save(new_config)

            return name
    
    def set_always_on_top(self, value):
        self._config["app"]["always_on_top"] = value
        self.save()
