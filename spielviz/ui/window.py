import os
import re

import pyspiel
from gi.repository import Gtk
from open_spiel.python.visualizations import treeviz

import spielviz.config as cfg
from spielviz.logic.game_selector import game_parameter_populator, list_games
from spielviz.resources import get_resource_path
from spielviz.ui.area import PlotArea
from spielviz.ui.completing_combo_box import CompletingComboBoxText

BASE_TITLE = 'SpielViz'
UI_FILE = get_resource_path("definition.xml")
ICON_FILE = get_resource_path("game_512x512.png")


def StateView(container: Gtk.ScrolledWindow):
    text = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam tristique quis tortor at fermentum. Donec orci diam, ornare efficitur orci quis, efficitur rhoncus metus. Donec eget ultricies nisi. Donec efficitur purus et nunc placerat, ut suscipit ante dictum. Aenean quis mi nec magna blandit tristique. Nulla laoreet vulputate fringilla. Integer alLorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam tristique quis tortor at fermentum. Donec orci diam, ornare efficitur orci quis, efficitur rhoncus metus. Donec eget ultricies nisi. Donec efficitur purus et nunc placerat, ut suscipit ante dictum. Aenean quis mi nec magna blandit tristique. Nulla laoreet vulputate fringilla. Integer alLorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam tristique quis tortor at fermentum. Donec orci diam, ornare efficitur orci quis, efficitur rhoncus metus. Donec eget ultricies nisi. Donec efficitur purus et nunc placerat, ut suscipit ante dictum. Aenean quis mi nec magna blandit tristique. Nulla laoreet vulputate fringilla. Integer alLorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam tristique quis tortor at fermentum. Donec orci diam, ornare efficitur orci quis, efficitur rhoncus metus. Donec eget ultricies nisi. Donec efficitur purus et nunc placerat, ut suscipit ante dictum. Aenean quis mi nec magna blandit tristique. Nulla laoreet vulputate fringilla. Integer al"""
    buf = Gtk.TextBuffer()
    buf.set_text(text)

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
    tv.set_buffer(buf)
    container.add(tv)
    return tv


def GameSelector(item: Gtk.ToolItem):
    game_combo = CompletingComboBoxText(
          list_games(), lambda x: "(" in x, game_parameter_populator)
    item.add(game_combo)
    return game_combo


def HistoryEntry(item: Gtk.ToolItem):
    entry = Gtk.Entry()
    item.add(entry)
    return entry


def Spinner(item: Gtk.ToolItem, **kwargs):
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


def export_tree(state):
    gametree = treeviz.GameTree(state.get_game(), depth_limit=1)
    return gametree.to_string().encode()


class MainWindow:
    def __init__(self, ui_file=UI_FILE):
        builder = Gtk.Builder()
        builder.add_from_file(ui_file)
        builder.connect_signals(self)

        self.world_tree = PlotArea(builder.get_object("world_tree"))
        self.state_view = StateView(builder.get_object("state_view"))

        self.select_game = GameSelector(builder.get_object("select_game"))
        self.select_history = HistoryEntry(builder.get_object("select_history"))
        self.lookahead_spin = Spinner(builder.get_object("lookahead"),
                                      value=1, lower=1, upper=5)
        self.lookbehind_spin = Spinner(builder.get_object("lookbehind"),
                                       lower=0, upper=20)

        self.window = builder.get_object("window")
        self.window.connect('delete-event', Gtk.main_quit)
        self.window.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.window.set_icon_from_file(ICON_FILE)
        self.window.show_all()

    def set_game(self, game: str):
        self.game = pyspiel.load_game(game)
        self.state = self.game.new_initial_state()
        self.render()

    def render(self):
        code = export_tree(self.state)
        self.set_dotcode(code)

    def find_text(self, entry_text):
        found_items = []
        dot_widget = self.world_tree
        regexp = re.compile(entry_text)
        for element in dot_widget.graph.nodes + dot_widget.graph.edges:
            if element.search_text(regexp):
                found_items.append(element)
        return found_items

    def textentry_changed(self, widget, entry):
        entry_text = entry.get_text()
        dot_widget = self.world_tree
        if not entry_text:
            dot_widget.set_highlight(None, search=True)
            return

        found_items = self.find_text(entry_text)
        dot_widget.set_highlight(found_items, search=True)

    def textentry_activate(self, widget, entry):
        entry_text = entry.get_text()
        dot_widget = self.world_tree
        if not entry_text:
            dot_widget.set_highlight(None, search=True)
            return

        found_items = self.find_text(entry_text)
        dot_widget.set_highlight(found_items, search=True)
        if (len(found_items) == 1):
            dot_widget.animate_to(found_items[0].x, found_items[0].y)

    def set_filter(self, filter):
        self.world_tree.set_filter(filter)

    def set_dotcode(self, dotcode, filename=None):
        if self.world_tree.set_dotcode(dotcode, filename):
            self.update_title(filename)
            self.world_tree.zoom_to_fit()

    def set_xdotcode(self, xdotcode, filename=None):
        if self.world_tree.set_xdotcode(xdotcode):
            self.update_title(filename)
            self.world_tree.zoom_to_fit()

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
        self.world_tree.reload()

    def error_dialog(self, message):
        dlg = Gtk.MessageDialog(parent=self,
                                type=Gtk.MessageType.ERROR,
                                message_format=message,
                                buttons=Gtk.ButtonsType.OK)
        dlg.set_title(BASE_TITLE)
        dlg.run()
        dlg.destroy()

    def on_history(self, action, has_back, has_forward):
        pass
        # self.action_back.set_sensitive(has_back)
        # self.action_forward.set_sensitive(has_forward)
