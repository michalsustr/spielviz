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
LOGGING_LEVEL = user_cfg.LOGGING_LEVEL or logging.INFO

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
PLOT_FONTSIZE = user_cfg.PLOT_FONTSIZE or 8
PLOT_WIDTH = user_cfg.PLOT_WIDTH or 0.25
PLOT_HEIGHT = user_cfg.PLOT_HEIGHT or 0.25
PLOT_ARROWSIZE = user_cfg.PLOT_ARROWSIZE or .25
PLOT_MARGIN = user_cfg.PLOT_MARGIN or 0.01
PLOT_HIGHLIGHT_PENWIDTH = user_cfg.PLOT_HIGHLIGHT_PENWIDTH or 4
HIGHLIGHT_COLOR = user_cfg.HIGHLIGHT_COLOR or (.8, .8, .1, 1)

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
TREE_MAX_NODES = user_cfg.TREE_MAX_NODES or 1000
LOOKAHEAD = user_cfg.LOOKAHEAD or 1
LOOKBEHIND = user_cfg.LOOKAHEAD or 1
FULL_TREE = user_cfg.FULL_TREE or False
# Use None for the player at current state, or 0 ... N-1
OBSERVING_PLAYER = user_cfg.OBSERVING_PLAYER or None
