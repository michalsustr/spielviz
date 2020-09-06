"""
There are two levels of configuration:

1. Global -- defaults set in this file.
2. User -- overrides global defaults within user's ~/.spielviz_cfg.py file.
"""

import importlib.util
import logging
import os


class UserConfig:
  """
  Custom user config.
  """

  def __init__(self, module):
    self.module = module

  def __getattr__(self, item):
    if item in self.module.__dict__:
      return self.module.__dict__[item]
    else:
      return None


class NoneConfig:
  """
  Config where no fields are configured.
  """

  def __getattr__(self, item):
    return None


def load_config(path: str):
  expand_path = os.path.expanduser(path)
  if not os.path.exists(expand_path):
    return NoneConfig()

  spec = importlib.util.spec_from_file_location("spielviz.config", expand_path)
  cfg = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(cfg)
  return UserConfig(cfg)


# Load user configuration that can override the defaults.
user_cfg = load_config("~/.spielviz_cfg.py")

# ======================= Define all configurations. ===========================

DEFAULT_GAME = user_cfg.DEFAULT_GAME or "kuhn_poker"
LAYOUT = user_cfg.LAYOUT or "dot"
LOGGING_LEVEL = user_cfg.LOGGING_LEVEL or logging.DEBUG

# [Window]
WINDOW_MAXIMIZE = user_cfg.WINDOW_MAXIMIZE or False

# [Rendering]

# Available filters (same as in `man dot`):
# dot       - drawing directed graphs (default)
# neato     - drawing undirected graphs
# twopi     - radial layouts of graphs
# circo     - circular layout of graphs
# fdp       - drawing undirected graphs
# sfdp      - drawing large undirected graphs
# patchwork - squarified tree maps
# osage     - array-based layouts
GRAPHVIZ_FILTER = user_cfg.GRAPHVIZ_FILTER or "dot"

# [Players]
INVALID_PLAYER_COLOR = user_cfg.INVALID_PLAYER_COLOR or "#dddddd"  # gray
CHANCE_COLOR = user_cfg.CHANCE_COLOR or "#800080"  # purple
TERMINAL_COLOR = user_cfg.TERMINAL_COLOR or "#000000"  # black
SIMULTANEOUS_PLAYER_COLOR = user_cfg.SIMULTANEOUS_PLAYER_COLOR or "#F0FFFF"  # azure
PLAYER_COLORS = user_cfg.PLAYER_COLORS or {
  0: "#FF0000",  # red
  1: "#0000FF",  # blue
  2: "#008000",  # green
  3: "#800000",  # maroon
  4: "#FF00FF",  # fuchsia
  5: "#00FF00",  # lime
  6: "#FFFF00",  # yellow
  7: "#00FFFF",  # aqua
  8: "#808000",  # olive
  9: "#000080",  # navy
  10: "#008080",  # teal
  11: "#00008B",  # darkblue

  # If you need to support more players for your game,
  # just add more colors here.
}
PLAYER_SHAPES = user_cfg.PLAYER_COLORS or {
  0: "square",
  1: "square"
}

# [Show options]
SHOW_ACTIONS = user_cfg.SHOW_ACTIONS or True
SHOW_INFORMATION_STATE_STRING = user_cfg.SHOW_INFORMATION_STATE_STRING or True
SHOW_PUBLIC_OBSERVATION_HISTORY = user_cfg.SHOW_PUBLIC_OBSERVATION_HISTORY or True
SHOW_ACTION_OBSERVATION_HISTORY = user_cfg.SHOW_ACTION_OBSERVATION_HISTORY or True
