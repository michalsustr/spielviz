import pyspiel
from gi.repository import Gtk

from spielviz.ui.primitives.tagged_view import *
from spielviz.ui.views.state_view import StringStateView


class KuhnStateView(StringStateView):
  def __init__(self, game: pyspiel.Game, container: Gtk.ScrolledWindow):
    super().__init__(game, container)
    self.game = game
    assert game.get_type().short_name == "kuhn_poker"

  def update(self, state: pyspiel.kuhn_poker.KuhnState):
    self.ttv.clear_text()
    self.ttv.appendln(f"Card dealing:", TAG_SECTION)
    for card, pl in enumerate(state.card_dealt()):
      self.ttv.append(f"Card {card}: ")
      if pl >= 0:
        self.ttv.append_pl(f"PL{pl}\n", pl)
      else:
        self.ttv.appendln("(no one)", TAG_NOTE)
