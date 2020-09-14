import logging
import re

import pyspiel
from gi.repository import Gtk, Gdk, GObject

import spielviz.config as cfg
from spielviz.dot.parser import make_graph, make_xdotcode
from spielviz.logic.dotcode_tree import GameTreeViz
from spielviz.logic.game_selector import game_parameter_populator, list_games
from spielviz.logic.state_history import state_from_history_str
from spielviz.resources import get_resource_path
from spielviz.ui.games import is_custom_view_registed, create_custom_state_view
from spielviz.ui.history_entry import HistoryEntry
from spielviz.ui.plot_area import PlotArea
from spielviz.ui.primitives.completing_combo_box import CompletingComboBoxText
from spielviz.ui.views.game_information_view import GameInformationView
from spielviz.ui.views.history_view import HistoryView
from spielviz.ui.views.observations_view import ObservationsView
from spielviz.ui.views.player_view import PlayerView
from spielviz.ui.views.rewards_view import RewardsView
from spielviz.ui.views.state_view import StateView, StringStateView
from spielviz.ui.views.observing_player_view import ObservingPlayerView

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


def make_text_view():
  tv = Gtk.TextView()
  tv.set_wrap_mode(Gtk.WrapMode.WORD)
  # tv.set_left_margin(15)
  # tv.set_border_width(2)
  tv.set_cursor_visible(False)
  tv.set_accepts_tab(False)
  tv.set_editable(False)
  tv.set_monospace(True)
  # tv.set_fill(True)
  return tv


def create_history_view(container: Gtk.ScrolledWindow) -> HistoryView:
  tv = make_text_view()
  container.add(tv)
  return HistoryView(tv)


def create_game_information_view(
    container: Gtk.ScrolledWindow) -> GameInformationView:
  tv = make_text_view()
  container.add(tv)
  return GameInformationView(tv)


def create_player_view(container: Gtk.ScrolledWindow) -> PlayerView:
  tv = make_text_view()
  container.add(tv)
  return PlayerView(tv)


def create_rewards_view(container: Gtk.ScrolledWindow) -> RewardsView:
  tv = make_text_view()
  container.add(tv)
  return RewardsView(tv)


def create_observations_view(container: Gtk.ScrolledWindow) -> ObservationsView:
  tv = make_text_view()
  container.add(tv)
  return ObservationsView(tv)


def create_game_selector(item: Gtk.ToolItem):
  game_combo = CompletingComboBoxText(
      list_games(), lambda x: "(" in x, game_parameter_populator)
  item.add(game_combo)
  return game_combo


def create_history_entry(item: Gtk.ToolItem) -> HistoryEntry:
  history_entry = HistoryEntry()
  item.add(history_entry)
  return history_entry


def create_spin_button(item: Gtk.ToolItem, **kwargs) -> Gtk.SpinButton:
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
    self.plot_area.connect("change_history", self.change_history)
    self.state_view_container = builder.get_object("state_view")

    self.history_view = HistoryView(builder.get_object("history"))

    self.game_information_view = GameInformationView(
        builder.get_object("game_information"))

    self.player_view = PlayerView(builder.get_object("player"))

    self.rewards_view = RewardsView(builder.get_object("rewards"))

    self.observation_private_info = pyspiel.PrivateInfoType.NONE
    self.observations_view = ObservationsView(builder.get_object("observations"))
    self.observing_player_combo = builder.get_object("observing_player")
    self.observing_player_combo.connect("changed", self.change_observing_player)
    self.observing_player_view = ObservingPlayerView(self.observing_player_combo)
    self.observing_player = 0

    self.show_public_info = True
    self.public_info = builder.get_object("public_info")
    self.public_info.set_active(self.show_public_info)
    self.public_info.connect("toggled", self.toggle_public_info)

    self.show_perfect_recall = False
    self.perfect_recall = builder.get_object("perfect_recall")
    self.perfect_recall.set_active(self.show_perfect_recall)
    self.perfect_recall.connect("toggled", self.toggle_perfect_recall)

    self.show_private_info = pyspiel.PrivateInfoType.SINGLE_PLAYER
    self.private_info_none = builder.get_object("private_info_none")
    self.private_info_single = builder.get_object("private_info_single")
    self.private_info_all = builder.get_object("private_info_all")
    self.private_info_single.set_active(True)
    self.private_info_none.connect("toggled", self.toggle_private_info)
    self.private_info_single.connect("toggled", self.toggle_private_info)
    self.private_info_all.connect("toggled", self.toggle_private_info)

    self.select_game = create_game_selector(builder.get_object("select_game"))
    self.select_game.connect("activate", self.update_game)
    self.select_history = create_history_entry(
        builder.get_object("select_history"))
    self.select_history.connect(
        "activate", lambda entry: self.change_history(entry, entry.get_text()))

    self.lookahead = cfg.LOOKAHEAD
    self.lookahead_spinner = create_spin_button(
        builder.get_object("lookahead"), value=self.lookahead, lower=1, upper=5)
    self.lookahead_spinner.connect("value-changed", self.update_lookahead)

    self.lookbehind = cfg.LOOKBEHIND
    self.lookbehind_spinner = create_spin_button(
        builder.get_object("lookbehind"), lower=self.lookbehind, upper=100)
    self.lookbehind_spinner.connect("value-changed", self.update_lookbehind)

    self.show_full_tree = cfg.FULL_TREE
    self.full_tree = builder.get_object("full_tree")
    self.full_tree.connect("toggled", self.toggle_full_tree)
    self.full_tree.set_active(self.show_full_tree)

    # Apply styles.
    css_provider = Gtk.CssProvider()
    css_provider.load_from_path(css_file)
    Gtk.StyleContext().add_provider_for_screen(
        Gdk.Screen.get_default(), css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_USER)

    if cfg.WINDOW_MAXIMIZE:
      self.window.maximize()
    self.window.set_title(BASE_TITLE)
    self.window.show_all()

  def change_observing_player(self, combo: Gtk.ComboBox):
    self.observing_player = combo.get_active()
    self.update_observer()
    self.set_state(self.state)

  def toggle_full_tree(self, button: Gtk.CheckButton):
    do_show = button.get_active()
    if do_show:
      self.show_full_tree = True
      self.lookbehind_spinner.set_sensitive(False)
      self.lookahead_spinner.set_sensitive(False)
    else:
      self.show_full_tree = False
      self.lookbehind_spinner.set_sensitive(True)
      self.lookahead_spinner.set_sensitive(True)
    self.set_state(self.state)

  def toggle_public_info(self, button: Gtk.CheckButton):
    do_show = button.get_active()
    self.show_public_info = do_show
    self.update_observer()
    self.set_state(self.state)

  def toggle_perfect_recall(self, button: Gtk.CheckButton):
    do_show = button.get_active()
    self.show_perfect_recall = do_show
    self.update_observer()
    self.set_state(self.state)

  def toggle_private_info(self, button: Gtk.RadioButton):
    active_radio = \
      [r for r in self.private_info_none.get_group() if r.get_active()][0]
    if active_radio == self.private_info_none:
      self.show_private_info = pyspiel.PrivateInfoType.NONE
    if active_radio == self.private_info_single:
      self.show_private_info = pyspiel.PrivateInfoType.SINGLE_PLAYER
    if active_radio == self.private_info_all:
      self.show_private_info = pyspiel.PrivateInfoType.ALL_PLAYERS
    self.update_observer()
    self.set_state(self.state)

  def update_lookahead(self, button: Gtk.SpinButton):
    self.lookahead = button.get_value_as_int()
    self.set_state(self.state)

  def update_lookbehind(self, button: Gtk.SpinButton):
    self.lookbehind = button.get_value_as_int()
    self.set_state(self.state)

  def change_history(self, origin_object: GObject, history_str: str):
    try:
      state = state_from_history_str(self.game, history_str)
      self.set_state(state)
    except ValueError as e:
      self.error_dialog(f"Could not parse history string '{history_str}': {e}")
    except pyspiel.SpielError as e:
      self.error_dialog(f"Could not seek to history '{history_str}': {e}")

  def update_game(self, combo_box: CompletingComboBoxText, game_name: str):
    self.set_game_from_name(game_name)

  def set_game_from_name(self, game_name):
    try:
      game = pyspiel.load_game(game_name)
      self.set_game(game)
    except pyspiel.SpielError:
      self.error_dialog(f"Could not load '{game_name}'")

  def set_game(self, game: pyspiel.Game):
    logging.debug(f"Setting game '{game}'")
    self.window.set_title(f"{BASE_TITLE}: {game}")
    self.game = game
    self.state_view = create_state_view(self.game, self.state_view_container)
    self.game_information_view.update(game)
    self.observing_player_view.update(game)
    self.update_observer()
    self.set_state(self.game.new_initial_state())

  def update_observer(self):
    self.observations_view.change_observation(
        self.game, self.observing_player, self.show_public_info,
        self.show_perfect_recall, self.show_private_info)

  def set_state(self, state: pyspiel.State):
    logging.debug(f"Setting state '{str(state)}'")
    try:
      gametree = GameTreeViz(state=state,
                             full_tree=self.show_full_tree,
                             lookbehind=self.lookbehind,
                             lookahead=self.lookahead)
      count = 0
      for _ in gametree.build_tree():
        if count >= cfg.TREE_MAX_NODES:
          self.error_dialog("There are too many nodes in the tree.\n"
                            f"Showing only {count} of them.")
          break
        count += 1

      dotcode = gametree.to_string().encode()
      xdotcode = make_xdotcode(dotcode)
      graph = make_graph(xdotcode)
      self.plot_area.set_graph(graph)

      self.history_view.update(state)
      self.state_view.update(state)
      self.player_view.update(state)
      self.rewards_view.update(state)
      self.observations_view.update(state)
      self.select_history.update(state)
      self.state = state
      self.render()
    except pyspiel.SpielError as ex:
      self.error_dialog(str(ex))
      return False

  def render(self):
    self.state_view_container.show_all()
    self.plot_area.show_all()
    pass

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
