import spielviz.config as cfg
from spielviz.ui.primitives.tagged_view import TaggedTextView
import pyspiel
from gi.repository import Gtk, Pango


def player_to_str(player: int):
  if player >= 0:
    return f"PLAYER {player}"
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


class PlayerView:
  """
  Render information about the current player in pyspiel.State
  """

  def __init__(self, container: Gtk.TextView):
    self.ttv = TaggedTextView(container)

  def update(self, state: pyspiel.State):
    self.ttv.clear_text()
    current_player = state.current_player()
    self.ttv.append_pl(player_to_str(current_player), current_player)
