import re
import sys
from typing import List

import pyspiel


def state_from_history_str(game: pyspiel.Game,
    history_str: str) -> pyspiel.State:
  history_str = history_str.strip()
  if history_str:
    return state_from_history(
        game, [int(action) for action in re.split("[\s,;]+", history_str)
               if action])
  else:
    return state_from_history(game, [])


def state_from_history(game: pyspiel.Game, history: List[int],
    move_limit: int = sys.maxsize) -> pyspiel.State:
  rollout = game.new_initial_state()
  num_players = game.num_players()
  i = 0
  while i < len(history) and rollout.move_number() < move_limit:
    if rollout.is_simultaneous_node():
      rollout.apply_actions(history[i:i + num_players])
      i += num_players
    else:
      rollout.apply_action(history[i])
      i += 1
  return rollout


def state_undo_n_moves(state: pyspiel.State, n: int) -> pyspiel.State:
  return state_from_history(state.get_game(), state.history(),
                            move_limit=state.move_number() - n)
