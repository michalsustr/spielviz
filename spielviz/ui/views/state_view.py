import pyspiel
from gi.repository import Gtk

from spielviz.ui.primitives.tagged_view import *


class StateView:
  """
  Render current pyspiel.State within scrolled window container.
  This allows for arbitrary rendering of UI based on the game.
  The list of game-specific UIs is in ui/games/
  """

  def __init__(self, game: pyspiel.Game, container: Gtk.ScrolledWindow):
    self.game = game
    self.container = container

  def update(self, state: pyspiel.State):
    raise NotImplementedError


class StringStateView(StateView):
  """
  Render current pyspiel.State within scrolled window container
  as a string representation of the State within a TextView.
  """

  def __init__(self, game: pyspiel.Game, container: Gtk.ScrolledWindow):
    StateView.__init__(self, game, container)
    text_view = Gtk.TextView()
    text_view.set_wrap_mode(Gtk.WrapMode.WORD)
    text_view.set_left_margin(5)
    text_view.set_right_margin(5)
    text_view.set_top_margin(5)
    text_view.set_bottom_margin(5)
    text_view.set_cursor_visible(False)
    text_view.set_accepts_tab(False)
    text_view.set_editable(False)
    text_view.set_monospace(True)

    maybe_child = container.get_child()
    if maybe_child:
      container.remove(maybe_child)
    container.add(text_view)
    self.ttv = TaggedTextView(text_view)
    container.show_all()

  def update(self, state: pyspiel.State):
    self.ttv.clear_text()
    state_str = str(state)
    if state_str:
      self.ttv.append(state_str)
    else:
      self.ttv.append(f"(empty state string)")
