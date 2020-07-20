import pyspiel
from gi.repository import Gtk


class StateView:
  def __init__(self, container: Gtk.TextView):
    raise NotImplementedError

  def update(self, state: pyspiel.State):
    raise NotImplementedError


class StringStateView(StateView):

  def __init__(self, container: Gtk.TextView):
    self.container = container
    self.text_buffer = Gtk.TextBuffer()
    self.text_buffer.set_text("")
    self.container.set_buffer(self.text_buffer)

  def update(self, state: pyspiel.State):
    self.text_buffer.set_text(str(state))
