import pyspiel
from gi.repository import Gtk

from spielviz.ui.primitives.tagged_view import TaggedTextView


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
