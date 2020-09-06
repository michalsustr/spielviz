import spielviz.config as cfg
import pyspiel
from gi.repository import Gtk, Pango
from typing import List

class TaggedTextView:
  """
  An object that allows to tag text in game-specific way within
  a TextView container.
  """

  def __init__(self, container: Gtk.TextView):
    self.container = container
    self.textbuffer = Gtk.TextBuffer()
    self.textbuffer.set_text("")
    self.container.set_buffer(self.textbuffer)

    self.TAG_NOTE = self.textbuffer.create_tag(
        "n", foreground="#999999")
    self.TAG_SECTION = self.textbuffer.create_tag(
        "b", weight=Pango.Weight.BOLD)
    self.TAG_PLAYER = [
      self.textbuffer.create_tag(f"p{p}", foreground=color)
      for p, color in cfg.PLAYER_COLORS.items()
    ]
    self.TAG_INVALID = self.textbuffer.create_tag(
        "inv", foreground=cfg.INVALID_PLAYER_COLOR)
    self.TAG_TERMINAL = self.textbuffer.create_tag(
        "ter", foreground=cfg.TERMINAL_COLOR)
    self.TAG_CHANCE = self.textbuffer.create_tag(
        "chn", foreground=cfg.CHANCE_COLOR)
    self.TAG_SIMULTANEOUS = self.textbuffer.create_tag(
        "sim", foreground=cfg.SIMULTANEOUS_PLAYER_COLOR)

  def append(self, text: str, *tags):
    if tags:
      self.textbuffer.insert_with_tags(
          self.textbuffer.get_end_iter(), text, *tags)
    else:
      self.textbuffer.insert(self.textbuffer.get_end_iter(), text)

  def appendln(self, text: str, *tags):
    self.append(text + "\n", *tags)

  def appendln_pl(self, text: str, player: int):
    self.appendln(text, self.player_tag(player))

  def append_pl(self, text: str, player: int):
    self.append(text, self.player_tag(player))

  def append_player_list(self, item_per_player: List[str], join_str=", "):
    for pl, item in enumerate(item_per_player):
      if pl > 0:
        self.append(join_str)
      self.append_pl(str(item), pl)

  def player_tag(self, player: int):
    if player >= 0:
      return self.TAG_PLAYER[player]
    elif player == pyspiel.PlayerId.INVALID:
      return self.TAG_INVALID
    elif player == pyspiel.PlayerId.TERMINAL:
      return self.TAG_TERMINAL
    elif player == pyspiel.PlayerId.CHANCE:
      return self.TAG_CHANCE
    elif player == pyspiel.PlayerId.SIMULTANEOUS:
      return self.TAG_SIMULTANEOUS
    else:
      raise AttributeError(f"Player not found: {player}")

  def clear_text(self):
    self.textbuffer.set_text("")
