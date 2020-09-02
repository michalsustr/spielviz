import spielviz.config as cfg
import pyspiel
from gi.repository import Gtk, Pango


class TaggedView:
  """
  An object that allows to tag text in game-specific way within
  a TextView container.
  """

  def __init__(self, container: Gtk.TextView):
    self.container = container
    self.textbuffer = Gtk.TextBuffer()
    self.textbuffer.set_text("")
    self.container.set_buffer(self.textbuffer)

    self._tag_note = self.textbuffer.create_tag(
        "n", foreground="#999999")
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

  def _append(self, text: str, *tags):
    if tags:
      self.textbuffer.insert_with_tags(
          self.textbuffer.get_end_iter(), text, *tags)
    else:
      self.textbuffer.insert(self.textbuffer.get_end_iter(), text)

  def _appendln(self, text: str, *tags):
    self._append(text + "\n", *tags)

  def _appendln_pl(self, text: str, player: int):
    self._appendln(text, self._player_tag(player))

  def _append_pl(self, text: str, player: int):
    self._append(text, self._player_tag(player))

  def _player_tag(self, player: int):
    if player >= 0:
      return self._tag_player[player]
    elif player == pyspiel.PlayerId.INVALID:
      return self._tag_invalid
    elif player == pyspiel.PlayerId.TERMINAL:
      return self._tag_terminal
    elif player == pyspiel.PlayerId.CHANCE:
      return self._tag_chance
    elif player == pyspiel.PlayerId.SIMULTANEOUS:
      return self._tag_simultaneous
    else:
      raise AttributeError(f"Player not found: {player}")

  def _clear(self):
    self.textbuffer.set_text("")
