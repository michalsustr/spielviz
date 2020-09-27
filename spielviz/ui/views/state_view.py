import pyspiel
from gi.repository import Gtk

from spielviz.ui.primitives.tagged_view import *


class StateView:
  """
  Render current pyspiel.State within scrolled window container.
  This allows for arbitrary rendering of UI based on the game.
  The list of game-specific UIs is in ui/games/
  """

  def __init__(self, game: pyspiel.Game, container: Gtk.Frame):
    self.game = game
    self.container = container

  def update(self, state: pyspiel.State):
    raise NotImplementedError

  def _add_single_child(self, child):
    maybe_child = self.container.get_child()
    if maybe_child:
      self.container.remove(maybe_child)
    self.container.add(child)


class TextStateView(StateView):
  """
  Render current pyspiel.State within scrolled window container
  as a string representation of the State within a TextView.
  """

  def __init__(self, game: pyspiel.Game, container: Gtk.Frame):
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
    self.ttv = TaggedTextView(text_view)
    self._add_single_child(text_view)
    container.show_all()

  def update(self, state: pyspiel.State):
    self.ttv.clear_text()
    state_str = str(state)
    if state_str:
      self.ttv.append(state_str)
    else:
      self.ttv.append(f"(empty state string)")


class NoStateViewImplemented(TextStateView):
  def __init__(self, game: pyspiel.Game, container: Gtk.Frame):
    TextStateView.__init__(self, game, container)
    self.ttv.append(f"(no special view available)")

  def update(self, state: pyspiel.State):
    pass


class ImageStateView(StateView):

  def __init__(self, game: pyspiel.Game, container: Gtk.Frame):
    StateView.__init__(self, game, container)
    self.game = game
    self.image = Gtk.Image()
    self.image.set_halign(Gtk.Align.START)
    self._add_single_child(self.image)
    container.show_all()
