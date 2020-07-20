import pyspiel
from gi.repository import Gtk
from spielviz.ui.state_view import StringStateView, StateView


class KuhnStateView(StringStateView):

  def __init__(self, game: pyspiel.Game, container: Gtk.ScrolledWindow):
    super().__init__(game, container)
    self.text_buffer.set_text("kuhn!")

  def update(self, state: pyspiel.State):
    self.text_buffer.set_text(str(state))
