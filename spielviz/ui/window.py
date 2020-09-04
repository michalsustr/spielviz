import os
import re
import logging

import pyspiel
from gi.repository import Gtk, Gdk, Gio

import spielviz.config as cfg
from spielviz.logic.game_selector import game_parameter_populator, list_games
from spielviz.resources import get_resource_path
from spielviz.ui.games import is_custom_view_registed, create_custom_state_view
from spielviz.ui.plot_area import PlotArea
from spielviz.ui.primitives.completing_combo_box import CompletingComboBoxText
from spielviz.ui.history_view import HistoryView
from spielviz.ui.state_view import StateView, StringStateView

BASE_TITLE = 'SpielViz'
UI_FILE = get_resource_path("definition.xml")
CSS_FILE = get_resource_path("style.css")
ICON_FILE = get_resource_path("game_512x512.png")


def create_state_view(game: pyspiel.Game,
    container: Gtk.ScrolledWindow) -> StateView:
  if is_custom_view_registed(game):
    return create_custom_state_view(game, container)
  else:
    return StringStateView(game, container)


def create_history_view(container: Gtk.ScrolledWindow) -> HistoryView:
  tv = Gtk.TextView()
  tv.set_wrap_mode(Gtk.WrapMode.WORD)
  tv.set_left_margin(5)
  tv.set_right_margin(5)
  tv.set_top_margin(5)
  tv.set_bottom_margin(5)
  tv.set_cursor_visible(False)
  tv.set_accepts_tab(False)
  tv.set_editable(False)
  tv.set_monospace(True)
  container.add(tv)
  return HistoryView(tv)


def create_game_selector(item: Gtk.ToolItem):
  game_combo = CompletingComboBoxText(
      list_games(), lambda x: "(" in x, game_parameter_populator)
  item.add(game_combo)
  return game_combo


def HistoryEntry(item: Gtk.ToolItem) -> Gtk.Entry:
  entry = Gtk.Entry()
  item.add(entry)
  return entry


def Spinner(item: Gtk.ToolItem, **kwargs) -> Gtk.SpinButton:
  spinbutton = Gtk.SpinButton()

  defaults = dict(
      value=0, lower=1, upper=5, step_increment=1,
      page_increment=10, page_size=0
  )
  defaults.update(kwargs)
  adjustment = Gtk.Adjustment(**defaults)
  spinbutton.set_adjustment(adjustment)
  item.add(spinbutton)
  return spinbutton


class MainWindow:
  def __init__(self, ui_file=UI_FILE, css_file=CSS_FILE):
    builder = Gtk.Builder()
    builder.add_from_file(ui_file)
    builder.connect_signals(self)

    self.window = builder.get_object("window")
    self.window.connect('delete-event', Gtk.main_quit)
    self.window.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
    self.window.set_icon_from_file(ICON_FILE)

    self.plot_area = PlotArea(builder.get_object("plot_area"), self)
    self.state_view_container = builder.get_object("state_view")
    self.state_history_container = builder.get_object("state_history")
    self.state_history = create_history_view(self.state_history_container)

    self.select_game = create_game_selector(builder.get_object("select_game"))
    # todo: create custom signal for completing combo box
    self.select_game.get_child().connect("activate", self.update_game)
    self.select_history = HistoryEntry(builder.get_object("select_history"))
    self.lookahead_spinner = Spinner(builder.get_object("lookahead"),
                                     value=1, lower=1, upper=5)
    self.lookbehind_spinner = Spinner(builder.get_object("lookbehind"),
                                      lower=0, upper=20)

    # Apply styles.
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(css_file)
    Gtk.StyleContext().add_provider_for_screen(
        Gdk.Screen.get_default(), css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_USER)

    self.window.show_all()

  def update_game(self, entry):
    game_name = entry.get_text()
    self.set_game_from_name(game_name)

  def set_game_from_name(self, game_name):
    try:
      game = pyspiel.load_game(game_name)
      self.set_game(game)
    except pyspiel.SpielException:
      self.error_dialog(f"Could not load '{game_name}'")

  def set_game(self, game: pyspiel.Game):
    logging.debug(f"Setting game '{str(game)}'")
    self.game = game
    self.state_view = create_state_view(self.game, self.state_view_container)
    self.set_state(self.game.new_initial_state())

  def set_state(self, state: pyspiel.State):
    logging.debug(f"Setting state '{str(state)}'")
    self.state = state
    self.state_history.update(state)
    self.state_view.update(state)
    self.plot_area.update(state)
    self.render()

  def render(self):
    self.state_history_container.show_all()
    self.state_view_container.show_all()
    self.plot_area.show_all()

  def find_text(self, entry_text):
    found_items = []
    dot_widget = self.plot_area
    regexp = re.compile(entry_text)
    for element in dot_widget.graph.nodes + dot_widget.graph.edges:
      if element.search_text(regexp):
        found_items.append(element)
    return found_items

  def textentry_changed(self, widget, entry):
    entry_text = entry.get_text()
    dot_widget = self.plot_area
    if not entry_text:
      dot_widget.set_highlight(None, search=True)
      return

    found_items = self.find_text(entry_text)
    dot_widget.set_highlight(found_items, search=True)

  def textentry_activate(self, widget, entry):
    entry_text = entry.get_text()
    dot_widget = self.plot_area
    if not entry_text:
      dot_widget.set_highlight(None, search=True)
      return

    found_items = self.find_text(entry_text)
    dot_widget.set_highlight(found_items, search=True)
    if (len(found_items) == 1):
      dot_widget.animate_to(found_items[0].x, found_items[0].y)

  def set_filter(self, filter):
    self.plot_area.set_filter(filter)

  def set_dotcode(self, dotcode, filename=None):
    if self.plot_area.set_dotcode(dotcode, filename):
      self.update_title(filename)
      self.plot_area.zoom_to_fit()

  def set_xdotcode(self, xdotcode, filename=None):
    if self.plot_area.set_xdotcode(xdotcode):
      self.update_title(filename)
      self.plot_area.zoom_to_fit()

  def update_title(self, filename=None):
    if filename is None:
      self.window.set_title(BASE_TITLE)
    else:
      self.window.set_title(
          os.path.basename(filename) + ' - ' + BASE_TITLE)

  def open_file(self, filename):
    try:
      fp = open(filename, 'rb')
      self.set_dotcode(fp.read(), filename)
      fp.close()
    except IOError as ex:
      self.error_dialog(str(ex))

  def on_open(self, action):
    pass

  def on_reload(self, action):
    self.plot_area.reload()

  def on_history(self, action, has_back, has_forward):
    pass
    # self.action_back.set_sensitive(has_back)
    # self.action_forward.set_sensitive(has_forward)

  def error_dialog(self, message: str):
    """
    Show an error dialog.
    """
    logging.error(message)
    dialog = Gtk.MessageDialog(
        transient_for=self.window,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.OK,
        text="An error occurred:"
    )
    dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()

  def warning_dialog(self, message: str) -> bool:
    """
    Show a warning dialog and ask whether to continue.
    :return: Did user press OK?
    """
    logging.warning(message)
    dialog = Gtk.MessageDialog(
        transient_for=self.window,
        message_type=Gtk.MessageType.WARNING,
        buttons=Gtk.ButtonsType.OK_CANCEL,
        text="WARNING",
    )
    dialog.format_secondary_text(message)
    response = dialog.run()
    dialog.destroy()
    return response == Gtk.ResponseType.OK

