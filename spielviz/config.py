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

# Colors
INVALID_PLAYER_COLOR = user_cfg.INVALID_PLAYER_COLOR or "#dddddd"  # gray
CHANCE_COLOR = user_cfg.CHANCE_COLOR or "#800080"  # purple
TERMINAL_COLOR = user_cfg.TERMINAL_COLOR or "#000000"  # black
SIMULTANEOUS_PLAYER_COLOR = user_cfg.SIMULTANEOUS_PLAYER_COLOR or "#F0FFFF"  # azure
PLAYER_COLORS = user_cfg.PLAYER_COLORS or [
  "#FF0000",  # red
  "#0000FF",  # blue
  "#008000",  # green
  "#800000",  # maroon
  "#FF00FF",  # fuchsia
  "#00FF00",  # lime
  "#FFFF00",  # yellow
  "#00FFFF",  # aqua
  "#808000",  # olive
  "#000080",  # navy
  "#008080",  # teal
  "#00008B",  # darkblue

  # If you need to support more players for your game,
  # just add more colors here.
]
