import pyspiel

def player_to_str(player: int):
  if player >= 0:
    return f"PL{player}"
  elif player == pyspiel.PlayerId.INVALID:
    return "INVALID"
  elif player == pyspiel.PlayerId.TERMINAL:
    return "TERMINAL"
  elif player == pyspiel.PlayerId.CHANCE:
    return "CHANCE"
  elif player == pyspiel.PlayerId.SIMULTANEOUS:
    return "SIMULTANEOUS"
  else:
    raise AttributeError(f"Player not found: {player}")
