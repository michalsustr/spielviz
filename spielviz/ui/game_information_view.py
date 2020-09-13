import spielviz.config as cfg
from spielviz.ui.primitives.tagged_view import TaggedTextView
import pyspiel
from gi.repository import Gtk, Pango


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
      self.ttv.append(label + ": ", self.ttv.TAG_SECTION)
      self.ttv.appendln(val)

    self.ttv.append("Short name: ", self.ttv.TAG_SECTION)
    self.ttv.appendln(str(type.short_name))
    self.ttv.append("Long name: ", self.ttv.TAG_SECTION)
    self.ttv.appendln(str(type.long_name))
    append_type("Dynamics", str(type.dynamics))
    append_type("Chance mode", str(type.chance_mode))
    append_type("Information", str(type.information))
    append_type("Utility", str(type.utility))
    append_type("Reward model", str(type.reward_model))

    self.ttv.append("Max players: ", self.ttv.TAG_SECTION)
    self.ttv.appendln(str(type.max_num_players))
    self.ttv.append("Min players: ", self.ttv.TAG_SECTION)
    self.ttv.appendln(str(type.min_num_players))
    self.ttv.append("Game parameters: ", self.ttv.TAG_SECTION)
    for name, param in type.parameter_specification.items():
      self.ttv.append(f"\n - {name}: {param}")
      if param.is_mandatory():
        self.ttv.append(f"(mandatory)", self.ttv.TAG_NOTE)
