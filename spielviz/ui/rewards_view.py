import spielviz.config as cfg
from spielviz.ui.primitives.tagged_view import TaggedTextView
import pyspiel
from gi.repository import Gtk, Pango

from spielviz.ui.utils import player_to_str

class RewardsView:
  """
  Render information about the current player in pyspiel.State
  """

  def __init__(self, container: Gtk.TextView):
    self.ttv = TaggedTextView(container)

  def update(self, state: pyspiel.State):
    self.ttv.clear_text()
    if not state.is_chance_node():
      self.ttv.append_player_list(state.rewards())
    else:
      self.ttv.append("(not available)", self.ttv.TAG_NOTE)
