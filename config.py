import keyboard
import json

class ConfigHandler:
    config = None
    def __init__(self, path):
        self.config = open(path, "r+")
    
    def __del__(self):
        
        if self.config == '': return
        self.config.close()
    
    def get_json(self):
        return json.load(self.config)
    
    def assign_hotkey(self, field):
        event = keyboard.read_event(suppress=True)
        if event.event_type == keyboard.KEY_DOWN:
            scan_code = event.scan_code
            name = event.name
            if name == 'esc':
                return

            new_config = json.load(self.config)

            if field == "start_key" or field == "stop_key":
                new_config["music"][field] = {
                    "name": name,
                    "scan_code": scan_code
                }
            else:
                new_config["music"]["key_mapping"][field] = name

            json.dump(new_config, self.config, indent=4)

            return name
