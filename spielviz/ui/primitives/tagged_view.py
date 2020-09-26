import spielviz.config as cfg
import pyspiel
from gi.repository import Gtk, Pango
from typing import List


_TAG_TABLE = Gtk.TextTagTable()

TAG_SECTION = Gtk.TextTag(name="section")
TAG_SECTION.set_property("weight", Pango.Weight.BOLD)
_TAG_TABLE.add(TAG_SECTION)

TAG_NOTE = Gtk.TextTag(name="note")
TAG_NOTE.set_property("foreground", "#999999")
_TAG_TABLE.add(TAG_NOTE)

TAG_PLAYER = dict()
for p, color in cfg.PLAYER_COLORS.items():
  TAG_PLAYER[p] = Gtk.TextTag(name=f"pl_{p}")
  TAG_PLAYER[p].set_property("foreground", color)
  _TAG_TABLE.add(TAG_PLAYER[p])

class TaggedTextView:
  """
  An object that allows to tag text in game-specific way within
  a TextView container.
  """

  def __init__(self, container: Gtk.TextView):
    self.container = container
    self.textbuffer = Gtk.TextBuffer.new(table=_TAG_TABLE)
    self.textbuffer.set_text("")
    self.container.set_buffer(self.textbuffer)

  def append(self, text: str, *tags):
    if tags:
      self.textbuffer.insert_with_tags(
          self.textbuffer.get_end_iter(), text, *tags)
    else:
      self.textbuffer.insert(self.textbuffer.get_end_iter(), text)

  def appendln(self, text: str, *tags):
    self.append(text + "\n", *tags)

  def appendln_pl(self, text: str, player: int):
    self.appendln(text, TAG_PLAYER[player])

  def append_pl(self, text: str, player: int):
    self.append(text, TAG_PLAYER[player])

  def append_player_list(self, item_per_player: List[str], join_str=", "):
    for pl, item in enumerate(item_per_player):
      if pl > 0:
        self.append(join_str)
      self.append_pl(str(item), pl)

  def clear_text(self):
    self.textbuffer.set_text("")


__all__ = ["TaggedTextView",
           "TAG_SECTION",
           "TAG_NOTE",
           "TAG_PLAYER"]
