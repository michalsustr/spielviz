import pyspiel
import re
from typing import List


def state_from_history_str(game: pyspiel.Game,
    history_str: str) -> pyspiel.State:
  history_str = history_str.strip()
  if history_str:
    return state_from_history(
        game, [int(action) for action in re.split("[\s,;]+", history_str)
               if action])
  else:
    return state_from_history(game, [])


def state_from_history(game: pyspiel.Game, history: List[int]) -> pyspiel.State:
  rollout = game.new_initial_state()
  for action in history:
    rollout.apply_action(int(action))
  return rollout
