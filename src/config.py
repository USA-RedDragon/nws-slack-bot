import json

_default_config = {
    'server': {
        'base_url': '',
        'port': 3000,
    },
    'slack': {
        'client_id': '',
        'client_secret': '',
        'signing_secret': '',
    },
    'nws': {
        'user_agent': '',
    },
    's3': {
        'bucket': '',
    }
}


# Config interfaces with a json file to store configuration data
class Config():
    def __init__(self):
        self.config = _default_config
        self.config_file = 'config.json'
        self.load()

    def load(self):
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.save()
        # Check for any missing sections
        for section in _default_config:
            if section not in self.config:
                self.config[section] = {}
            # Check for any missing keys
            for key in _default_config[section]:
                if key not in self.config[section]:
                    self.config[section][key] = _default_config[section][key]
        self.save()

    def save(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get(self, section, key):
        return self.config[section][key]

    def set(self, section, key, value):
        self.config[section][key] = value
        self.save()


_config = Config()


def get_config():
    return _config
