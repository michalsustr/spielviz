from typing import Optional
import pyspiel
from gi.repository import Gtk


class ObservingPlayerView:

  def __init__(self, container: Gtk.ComboBox):
    self.container = container
    self.store = Gtk.ListStore(str)
    self.container.set_model(self.store)

  def update(self, game: pyspiel.Game, observing_player: Optional[int]):
    self.container.set_model(None)  # Avoid signal propagation.
    self.store.clear()
    self.store.append(["Current at state"])
    for i in range(game.num_players()):
      self.store.append([str(i)])
    self.container.set_model(self.store)

    if observing_player is None:
      self.container.set_active(0)
    else:
      self.container.set_active(observing_player + 1)

