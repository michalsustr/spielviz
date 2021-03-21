from typing import Dict

import pyspiel
from gi.repository import Gdk, Gtk, GObject

from spielviz.ui import spielviz_events


def make_label(entry_label) -> Gtk.Label:
  label = Gtk.Label(halign=Gtk.Align.START, valign=Gtk.Align.START,
                    margin=1, margin_right=10)
  label.set_markup(f"<b>{entry_label}</b>")
  return label


def make_textview(**kwargs) -> Gtk.TextView:
  return Gtk.TextView(monospace=True,
                      halign=Gtk.Align.START,
                      valign=Gtk.Align.CENTER, **kwargs)


def make_row_entry(grid: Gtk.Grid, entry_label: str,
                   label_cell_factory=make_label,
                   value_cell_factory=make_textview) -> GObject:
  label = make_label(entry_label)
  cell = value_cell_factory()
  grid.add(label)
  grid.attach_next_to(cell, label, side=Gtk.PositionType.RIGHT,
                      width=1, height=1)
  return cell


def num_grid_rows(grid: Gtk.Grid) -> int:
  grid_children = grid.get_children()
  assert len(grid_children) % 2 == 0
  return int(len(grid_children) / 2)


class GameInformationView(GObject.GObject):
  """
  Render information about the current pyspiel.Game
  Allow to change the game parameters.
  """

  __gsignals__ = {
    spielviz_events.CHANGE_GAME: (GObject.SIGNAL_RUN_LAST, None, (str,))
  }

  def __init__(self, container: Gtk.Grid):
    GObject.GObject.__init__(self)
    self.game: Optional[pyspiel.Game] = None
    self.grid = container

    def add_entry(label):
      return make_row_entry(self.grid, label,
                            value_cell_factory=lambda: Gtk.TextView(
                                monospace=True, editable=False,
                                cursor_visible=False,
                                halign=Gtk.Align.START,
                                valign=Gtk.Align.CENTER))

    self.short_name = add_entry("Short name")
    self.game_param_grid = make_row_entry(self.grid, "Params",
                                          value_cell_factory=lambda: Gtk.Grid(
                                              orientation="vertical",
                                              margin_bottom=6,
                                              column_spacing=2, row_spacing=2))
    self.long_name = add_entry("Long name")
    self.dynamics = add_entry("Dynamics")
    self.chance_mode = add_entry("Chance mode")
    self.information = add_entry("Information")
    self.utility = add_entry("Utility")
    self.reward_model = add_entry("Reward model")
    self.max_players = add_entry("Max players")
    self.min_players = add_entry("Min players")
    self.max_chance_outcomes = add_entry("Max chance\noutcomes")
    self.num_distinct_actions = add_entry("Num distinct\nactions")
    self.max_game_length = add_entry("Max game\nlength")
    self.min_utility = add_entry("Min utility")
    self.max_utility = add_entry("Max utility")

  def update(self, game: pyspiel.Game):
    self.game = game
    type = self.game.get_type()
    params_values = self.game.get_parameters()
    params_spec = type.parameter_specification

    self.short_name.get_buffer().set_text(str(type.short_name))

    self._update_param_grid_rows(self.game_param_grid, params_spec)
    for i, (name, default_param) in enumerate(params_spec.items()):
      label = self.game_param_grid.get_child_at(left=0, top=i)
      tv = self.game_param_grid.get_child_at(left=1, top=i)
      label.set_text(f"{name}*" if default_param.is_mandatory() else name)
      tv.get_buffer().set_text(str(params_values[name]))
    self.game_param_grid.show_all()

    self.long_name.get_buffer().set_text(str(type.long_name))
    self.dynamics.get_buffer().set_text(str(type.dynamics))
    self.chance_mode.get_buffer().set_text(str(type.chance_mode))
    self.information.get_buffer().set_text(str(type.information))
    self.utility.get_buffer().set_text(str(type.utility))
    self.reward_model.get_buffer().set_text(str(type.reward_model))
    self.max_players.get_buffer().set_text(str(type.max_num_players))
    self.min_players.get_buffer().set_text(str(type.min_num_players))

    def update_optional(field, callback):
      try:
        field.get_buffer().set_text(str(callback()))
      except RuntimeError:
        field.get_buffer().set_text("(not available)")

    update_optional(self.max_chance_outcomes, game.max_chance_outcomes)
    update_optional(self.num_distinct_actions, game.num_distinct_actions)
    update_optional(self.max_game_length, game.max_game_length)
    update_optional(self.min_utility, game.min_utility)
    update_optional(self.max_utility, game.max_utility)

  def _update_param_grid_rows(self, grid: Gtk.Grid,
                              params: Dict[str, pyspiel.GameParameter]):
    actual_grid_rows = num_grid_rows(grid)
    expected_num_rows = len(params)
    if expected_num_rows == actual_grid_rows:
      pass
    elif expected_num_rows < actual_grid_rows:
      # Remove
      for i in range(expected_num_rows, actual_grid_rows):
        label = grid.get_child_at(left=0, top=i)
        tv = grid.get_child_at(left=1, top=i)
        grid.remove(label)
        grid.remove(tv)
    else:
      # Add
      num_row_additions = expected_num_rows - actual_grid_rows
      for _ in range(num_row_additions):
        tv = make_row_entry(grid, "", lambda: Gtk.TextView(monospace=True))
        tv.connect("key-press-event", self._on_param_change)

  def _get_grid_params(self) -> Dict[str, str]:
    actual_grid_rows = num_grid_rows(self.game_param_grid)
    params = dict()
    for i in range(actual_grid_rows):
      label = self.game_param_grid.get_child_at(left=0, top=i)
      tv = self.game_param_grid.get_child_at(left=1, top=i)
      param = label.get_text()
      buf = tv.get_buffer()
      value = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
      params[param.strip()] = value.strip()
    return params

  def _on_param_change(self, widget, event):
    if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
      params = self._get_grid_params()
      params_str = ",".join(f"{key}={val}" for key, val in params.items())
      game_spec = f"{self.game.get_type().short_name}({params_str})"
      self.emit(spielviz_events.CHANGE_GAME, game_spec)
      return True
    return False
