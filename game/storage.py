"""Atomic local saves; invalid files never crash the title screen."""
from __future__ import annotations

import json
import math
from pathlib import Path

from .state import GameState

DEFAULT_SETTINGS = {
    "muted": False, "large_text": False, "reduced_motion": False, "high_contrast": False, "slow_walk": False,
    # A gentle marker over the next suggested place; on for new players.
    "show_way": True,
    # First-time prompts, each shown once.
    "tip_move": False, "tip_talk": False, "tip_journal": False,
}


def write_json(path, data):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+".tmp")
    temporary.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
    temporary.replace(path)


def save_game(path,state,position):
    write_json(path,{"format":1,"state":state.to_dict(),"position":[round(float(v),3) for v in position]})


def load_game(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data,dict) or data.get("format")!=1:
        raise ValueError("Unrecognized save format")
    state=GameState.from_dict(data["state"])
    position=data["position"]
    if not isinstance(position,list) or len(position)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in position):
        raise ValueError("Invalid player position")
    if not (32<=position[0]<=1088 and 56<=position[1]<=800):
        raise ValueError("Player position outside village")
    return state,position


def load_settings(path):
    settings=DEFAULT_SETTINGS.copy()
    try:
        data=json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data,dict):
            settings.update({key:value for key,value in data.items() if key in settings and type(value) is bool})
    except (OSError,ValueError):
        pass
    return settings
