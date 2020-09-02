import pyspiel
from gi.repository import Gtk
from spielviz.ui.primitives.tagged_view import TaggedView


class StateView:
  """
  Render current pyspiel.State within scrolled window container.
  This allows for arbitrary rendering of UI based on the game.
  The list of game-specific UIs is in ui/games/
  """

  def __init__(self, game: pyspiel.Game, container: Gtk.ScrolledWindow):
    self.game = game
    # self.container = container

  def update(self, state: pyspiel.State):
    raise NotImplementedError


class StringStateView(StateView, TaggedView):
  """
  Render current pyspiel.State within scrolled window container
  as a string representation of the State within a TextView.
  """

  def __init__(self, game: pyspiel.Game, container: Gtk.ScrolledWindow):
    StateView.__init__(self, game, container)

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

    TaggedView.__init__(self, tv)

  def update(self, state: pyspiel.State):
    self._clear()
    self._append(str(state))
