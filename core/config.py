# core/config.py
import os
import json


class ConfigManager:
    def __init__(self, config_path, path_raiz):
        self.config_path = config_path
        self.path_raiz = path_raiz
        self.config = {}
        self.cargar_config()

    def cargar_config(self):
        if not os.path.exists(self.path_raiz):
            os.makedirs(self.path_raiz, exist_ok=True)
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {"semestres": {}, "ultimo_semestre": "", "ultima_materia": ""}
            self.guardar_config()

    def guardar_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.guardar_config()