import pyspiel
from gi.repository import Gtk

from spielviz.ui.primitives.tagged_view import TaggedTextView


class HistoryView:
  """
  Render information about the current pyspiel.State in a non-game-specific
  (general) way, like the current history, player(s) to move etc.
  """

  def __init__(self, container: Gtk.TextView):
    self.ttv = TaggedTextView(container)

  def update(self, state: pyspiel.State):
    self.ttv.clear_text()
    self.ttv.append("Move number: ", self.ttv.TAG_SECTION)
    self.ttv.append(str(state.move_number()))

    if state.is_initial_state():
      self.ttv.append("\nThis is the initial state.", self.ttv.TAG_NOTE)

    game = state.get_game()
    rollout = game.new_initial_state()
    for action in state.history():
      self.ttv.append_pl(f"\n{action}: {rollout.action_to_string(action)}",
                           rollout.current_player())
      rollout.apply_action(action)
