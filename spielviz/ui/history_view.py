import spielviz.config as cfg
import pyspiel
from gi.repository import Gtk, Pango


class HistoryView:

  def __init__(self, container: Gtk.TextView):
    self.container = container
    self.textbuffer = Gtk.TextBuffer()
    self.textbuffer.set_text("")
    self.container.set_buffer(self.textbuffer)

    self._tag_section = self.textbuffer.create_tag(
        "b", weight=Pango.Weight.BOLD)
    self._tag_player = [
      self.textbuffer.create_tag(f"p{p}", foreground=color)
      for p, color in enumerate(cfg.PLAYER_COLORS)
    ]
    self._tag_invalid = self.textbuffer.create_tag(
        "inv", foreground=cfg.INVALID_PLAYER_COLOR)
    self._tag_terminal = self.textbuffer.create_tag(
        "ter", foreground=cfg.TERMINAL_COLOR)
    self._tag_chance = self.textbuffer.create_tag(
        "chn", foreground=cfg.CHANCE_COLOR)
    self._tag_simultaneous = self.textbuffer.create_tag(
        "sim", foreground=cfg.SIMULTANEOUS_PLAYER_COLOR)

  def update(self, state: pyspiel.State):
    self._clear()

    self._append("Current player: ", self._tag_section)
    current_player = state.current_player()
    if current_player >= 0:
      self._appendln(str(state.current_player()),
                     self._tag_player[current_player])
    else:
      if current_player == pyspiel.PlayerId.INVALID:
        self._appendln("INVALID", self._tag_invalid)
      if current_player == pyspiel.PlayerId.TERMINAL:
        self._appendln("TERMINAL", self._tag_terminal)
      if current_player == pyspiel.PlayerId.CHANCE:
        self._appendln("CHANCE", self._tag_chance)
      if current_player == pyspiel.PlayerId.SIMULTANEOUS:
        self._appendln("SIMULTANEOUS", self._tag_simultaneous)

    self._appendln("Actions:", self._tag_section)
    for action in state.history():
      self._appendln(str(action))

  def _append(self, text: str, tag=None):
    if tag:
      self.textbuffer.insert_with_tags(
          self.textbuffer.get_end_iter(), text, tag)
    else:
      self.textbuffer.insert(self.textbuffer.get_end_iter(), text)

  def _appendln(self, text: str, tag=None):
    self._append(text + "\n", tag)

  def _clear(self):
    self.textbuffer.set_text("")
