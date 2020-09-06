import pyspiel
import re

def state_from_history(game: pyspiel.Game, history_str: str) -> pyspiel.State:
  rollout = game.new_initial_state()
  history_str = history_str.strip()
  if history_str:
    for action in re.split("[\s,;]+", history_str):
      if action:
        rollout.apply_action(int(action))
  return rollout
