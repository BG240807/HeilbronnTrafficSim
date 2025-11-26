from pathlib import Path
import json


def save_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)

def load_json(path: Path):
    with open(path) as f:
        return json.load(f)