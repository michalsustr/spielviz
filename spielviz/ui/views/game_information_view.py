import pyspiel
from gi.repository import Gtk

from spielviz.ui.primitives.tagged_view import *

class GameInformationView:
  """
  Render information about the current pyspiel.Game
  """

  def __init__(self, container: Gtk.TextView):
    self.ttv = TaggedTextView(container)

  def update(self, game: pyspiel.Game):
    self.ttv.clear_text()
    type = game.get_type()

    def append_type(label, s):
      key, val = s.split(".")
      self.ttv.append(label + ": ", TAG_SECTION)
      self.ttv.appendln(val)

    self.ttv.append("Short name: ", TAG_SECTION)
    self.ttv.appendln(str(type.short_name))
    self.ttv.append("Long name: ", TAG_SECTION)
    self.ttv.appendln(str(type.long_name))
    append_type("Dynamics", str(type.dynamics))
    append_type("Chance mode", str(type.chance_mode))
    append_type("Information", str(type.information))
    append_type("Utility", str(type.utility))
    append_type("Reward model", str(type.reward_model))

    self.ttv.append("Max players: ", TAG_SECTION)
    self.ttv.appendln(str(type.max_num_players))
    self.ttv.append("Min players: ", TAG_SECTION)
    self.ttv.appendln(str(type.min_num_players))
    self.ttv.append("Game parameters: ", TAG_SECTION)
    params = game.get_parameters()
    for name, default_param in type.parameter_specification.items():
      self.ttv.append(f"\n - {name}: {params[name]} ")
      self.ttv.append(f"(default {default_param}) ", TAG_NOTE)
      if default_param.is_mandatory():
        self.ttv.append(f"(mandatory)", TAG_NOTE)

    self.ttv.append("\n\n")
    self.ttv.append("")

    def append_optional(label, callback):
      self.ttv.append(label, TAG_SECTION)
      try:
        self.ttv.appendln(str(callback()))
      except RuntimeError:
        self.ttv.appendln("(not available)", TAG_NOTE)

    append_optional("Max chance outcomes: ", game.max_chance_outcomes)
    append_optional("Num distinct actions: ", game.num_distinct_actions)
    append_optional("Max game length: ", game.max_game_length)
    append_optional("Min utility: ", game.min_utility)
    append_optional("Max utility: ", game.max_utility)
