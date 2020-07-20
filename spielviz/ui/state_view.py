import pyspiel
from gi.repository import Gtk


class StateView:
  def __init__(self, game: pyspiel.Game, container: Gtk.ScrolledWindow):
    self.game = game
    self.container = container

  def update(self, state: pyspiel.State):
    raise NotImplementedError


class StringStateView(StateView):

  def __init__(self, game: pyspiel.Game, container: Gtk.ScrolledWindow):
    super().__init__(game, container)

    tv = Gtk.TextView()
    tv.set_wrap_mode(Gtk.WrapMode.WORD)
    tv.set_left_margin(5)
    tv.set_right_margin(5)
    tv.set_top_margin(5)
    tv.set_bottom_margin(5)
    tv.set_cursor_visible(False)
    tv.set_accepts_tab(False)
    tv.set_editable(False)
    tv.set_monospace(True)
    container.add(tv)

    self.text_buffer = Gtk.TextBuffer()
    self.text_buffer.set_text(game.get_type().short_name)
    tv.set_buffer(self.text_buffer)

  def update(self, state: pyspiel.State):
    self.text_buffer.set_text(str(state))
