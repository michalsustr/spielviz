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

# Define all configurations.
DEFAULT_GAME = user_cfg.DEFAULT_GAME or "kuhn_poker"
DEFAULT_LAYOUT = user_cfg.DEFAULT_LAYOUT or "dot"
DEFAULT_LOGGING = user_cfg.DEFAULT_LOGGING or logging.INFO
