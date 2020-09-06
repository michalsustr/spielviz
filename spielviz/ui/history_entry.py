import logging

import pyspiel
from spielviz.logic.state_history import state_from_history_str
from gi.repository import Gtk


class HistoryEntry(Gtk.Entry):
  def __init__(self, *args):
    super(HistoryEntry, self).__init__(*args)
    self.liststore = Gtk.ListStore(str)
    completion = Gtk.EntryCompletion()
    completion.set_model(self.liststore)
    completion.set_text_column(0)
    self.set_completion(completion)

  def update(self, state: pyspiel.State):
    self.state = state
    self.set_text(state.history_str())

  def do_changed(self, *args):
    # Avoid calling this function before init?
    if not hasattr(self, "liststore"):
      return

    self.liststore.clear()
    base = self.state.history_str()
    self.liststore.append((base,))

    if base:
      base += " "
    for action in self.state.legal_actions():
      self.liststore.append((base + str(action),))

    # Add possibly more options based on current expansion:
    try:
      history_str = self.get_text().rstrip()
      rollout = state_from_history_str(self.state.get_game(), history_str)
      for action in rollout.legal_actions():
        self.liststore.append((history_str + " " + str(action),))
    except RuntimeError as e:
      logging.debug(f"Expanding history failed with {e}")
