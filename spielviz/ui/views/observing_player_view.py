import pyspiel
from gi.repository import Gtk


class ObservingPlayerView:

  def __init__(self, container: Gtk.ComboBox):
    self.container = container
    self.store = Gtk.ListStore(int)
    self.container.set_model(self.store)

  def update(self, game: pyspiel.Game):
    previosly_active = self.container.get_active()
    self.container.set_model(None)  # Avoid signal propagation.
    self.store.clear()
    for i in range(game.num_players()):
      self.store.append([i])
    self.container.set_model(self.store)

    if previosly_active and 0 <= previosly_active < game.num_players():
      self.container.set_active(previosly_active)
    else:
      self.container.set_active(0)
