import pyspiel
from gi.repository import Gtk

from spielviz.ui.primitives.tagged_view import *


class StateStrView:

  def __init__(self, container: Gtk.TextView):
    self.ttv = TaggedTextView(container)

  def update(self, state: pyspiel.State):
    self.ttv.clear_text()
    self.ttv.appendln("State to string:", TAG_SECTION)
    self.ttv.appendln(str(state))
