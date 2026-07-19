import json
import os

CONFIG_DIR = os.path.expanduser("~/.config/arkhas")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# hotkey se guarda como {"keysym": str, "modifiers": [str]}. El keysym usa
# la nomenclatura de Gdk.keyval_name() (la misma que devuelve la captura de
# teclado en ui.py), y los modifiers son nombres ("Control", "Alt", "Super",
# "Shift") que hotkey.py traduce a mascaras de X11 al armar el grab. Guardar
# nombres en vez de codigos crudos hace que el archivo sea legible/editable
# a mano y no dependa de que las constantes numericas de X11 no cambien.
DEFAULTS = {
    "hotkey": {"keysym": "s", "modifiers": ["Control", "Alt"]},
    "split_percent": 50,
}

# Estas teclas, apretadas SOLAS (sin ningun modificador), son controles
# locales del picker (X = cerrar ventana, Espacio = maximizar, Escape =
# cancelar). Guardarlas como atajo global generaria un conflicto cada vez
# que el picker esta abierto: ui.py ya evita que se puedan capturar asi
# desde la interfaz, pero se valida aca tambien por si el archivo termina
# con un valor invalido de otra forma (edicion manual, o una version
# anterior con el bug que permitia guardar Escape).
RESERVED_BARE_KEYNAMES = ("x", "X", "space", "Escape")


def is_valid_hotkey(hotkey):
    if not hotkey or not hotkey.get("keysym"):
        return False
    if hotkey["keysym"] in RESERVED_BARE_KEYNAMES and not hotkey.get("modifiers"):
        return False
    return True


def load_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULTS)
        return dict(DEFAULTS)
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
    # Se mergea sobre DEFAULTS en vez de usar data directo: si en una
    # version futura se agrega una clave nueva, un config.json viejo que no
    # la tiene sigue cargando con el valor por defecto en vez de romper.
    merged = dict(DEFAULTS)
    merged.update(data)

    if not is_valid_hotkey(merged.get("hotkey")):
        print(
            f"Arkhas: atajo guardado invalido ({merged.get('hotkey')!r}), "
            f"volviendo al de fabrica.",
            flush=True,
        )
        merged["hotkey"] = dict(DEFAULTS["hotkey"])
        save_config(merged)

    return merged


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
