import spielviz.config as cfg
from spielviz.ui.primitives.tagged_view import TaggedTextView
import pyspiel
from gi.repository import Gtk, Pango

from spielviz.ui.utils import player_to_str



class HistoryView:
  """
  Render information about the current pyspiel.State in a non-game-specific
  (general) way, like the current history, player(s) to move etc.
  """

  def __init__(self, container: Gtk.TextView):
    self.ttv = TaggedTextView(container)

  def update(self, state: pyspiel.State):
    self.ttv.clear_text()
    game = state.get_game()

    rollout = game.new_initial_state()
    for action in state.history():
      self.ttv.appendln_pl(f"{action}: {rollout.action_to_string(action)}",
                           rollout.current_player())
      rollout.apply_action(action)
