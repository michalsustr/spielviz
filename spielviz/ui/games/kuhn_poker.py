import pyspiel
from gi.repository import Gtk
from spielviz.ui.state_view import StringStateView, StateView


class KuhnStateView(StringStateView):
  def __init__(self, game: pyspiel.Game, container: Gtk.ScrolledWindow):
    super().__init__(game, container)
    self.game = game
    assert game.get_type().short_name == "kuhn_poker"

  def update(self, state: pyspiel.State):
    self.tv._clear()
    self.tv._appendln(f"Player cards:", self.tv._tag_section)
    for pl, card in enumerate([0, 1]):
      self.tv._appendln(f"PL{pl}: {card}")  # todo: bug: cannot use colors here??
