import pyspiel
from gi.repository import Gtk

from spielviz.ui.primitives.tagged_view import *
from spielviz.ui.utils import player_to_str


class PlayerView:
  """
  Render information about the current player in pyspiel.State
  """

  def __init__(self, container: Gtk.TextView):
    self.ttv = TaggedTextView(container)

  def update(self, state: pyspiel.State):
    self.ttv.clear_text()
    current_player = state.current_player()
    self.ttv.append_pl(player_to_str(current_player), current_player)
