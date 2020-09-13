import pyspiel
from gi.repository import Gtk
from spielviz.ui.views.state_view import StringStateView, StateView


class KuhnStateView(StringStateView):
  def __init__(self, game: pyspiel.Game, container: Gtk.ScrolledWindow):
    super().__init__(game, container)
    self.game = game
    assert game.get_type().short_name == "kuhn_poker"

  def update(self, state: pyspiel.State):
    self.ttv.clear_text()
    self.ttv.appendln(f"Player cards:", self.ttv.TAG_SECTION)
    for pl, card in enumerate([0, 1]):
      self.ttv.appendln(f"PL{pl}: {card}")  # todo: bug: cannot use colors here??
