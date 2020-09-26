import pyspiel
from gi.repository import Gtk

from spielviz.ui.primitives.tagged_view import *


class HistoryView:
  """
  Render information about the current pyspiel.State in a non-game-specific
  (general) way, like the current history, player(s) to move etc.
  """

  def __init__(self, container: Gtk.TextView):
    self.ttv = TaggedTextView(container)

  def update(self, state: pyspiel.State):
    self.ttv.clear_text()
    if state.is_initial_state():
      self.ttv.append("This is the initial state.", TAG_NOTE)
      return

    game = state.get_game()
    rollout = game.new_initial_state()
    num_players = game.num_players()
    history = state.history()
    i = 0
    move_num = 0
    while i < len(history):
      if rollout.is_simultaneous_node():
        move_str = f"move={move_num}  "
        for p in range(num_players):
          action = history[i+p]
          action_descr = rollout.action_to_string(p, action)
          self.ttv.append(move_str if p == 0 else " " * len(move_str),
                          TAG_PLAYER[pyspiel.PlayerId.SIMULTANEOUS])
          self.ttv.append_pl(f"action={action}  "
                             f"str={action_descr}\n", p)
        rollout.apply_actions(history[i:i+num_players])
        i += num_players
        move_num += 1
      else:
        action = history[i]
        action_descr = rollout.action_to_string(action)
        self.ttv.append_pl(f"move={move_num}  "
                           f"action={action}  "
                           f"str={action_descr}  ",
                           rollout.current_player())
        if rollout.is_chance_node():
          prob = [p for a, p in rollout.chance_outcomes() if a == action][0]
          self.ttv.append_pl(f"prob={prob:.4f}", rollout.current_player())
        self.ttv.append("\n")
        rollout.apply_action(history[i])
        i += 1
        move_num += 1
