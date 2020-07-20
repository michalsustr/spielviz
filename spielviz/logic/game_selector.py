import pyspiel


def list_games():
  return [game.short_name for game in pyspiel.registered_games()]


def game_parameter_populator(text):
  options = [
    "kuhn_poker(players=1)",
    "kuhn_poker(players=2)",
    "kuhn_poker(players=3)",
  ]

  return [option for option in options if option.startswith(text)]
