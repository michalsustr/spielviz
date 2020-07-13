import os
import re

from gi.repository import Gtk

from spielviz.ui.area import PlotArea
from spielviz.graphics.elements import Graph

BASE_TITLE = 'SpielViz'
DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 512


class FindMenuToolAction(Gtk.Action):
    __gtype_name__ = "FindMenuToolAction"

    def do_create_tool_item(self) -> Gtk.ToolItem:
        return Gtk.ToolItem()


class MainWindow(Gtk.Window):
    ui_string = """
    <ui>
        <toolbar name="ToolBar">
            <toolitem action="Open"/>
            <toolitem action="Reload"/>
            <toolitem action="Print"/>
            <separator/>
            <toolitem action="Back"/>
            <toolitem action="Forward"/>
            <separator/>
            <toolitem action="ZoomIn"/>
            <toolitem action="ZoomOut"/>
            <toolitem action="ZoomFit"/>
            <toolitem action="Zoom100"/>
            <separator/>
            <toolitem name="Find" action="Find"/>
        </toolbar>
    </ui>
    """

    def __init__(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        Gtk.Window.__init__(self)

        window = self
        window.set_title(BASE_TITLE)
        window.set_default_size(width, height)

        self.plot_area = self._create_plot_area()
        toolbar = self._create_toolbar()

        container = Gtk.VBox()
        window.add(container)
        container.pack_start(toolbar, expand=False, fill=False, padding=0)
        container.pack_start(self.plot_area, expand=True, fill=True, padding=0)

        window.set_focus(self.plot_area)
        window.show_all()

    def _create_plot_area(self):
        plot_area = PlotArea()
        plot_area.connect("error", lambda e, m: self.error_dialog(m))
        plot_area.connect("history", self.on_history)
        return plot_area

    def _create_toolbar(self):
        # Create a UIManager instance
        ui_manager = Gtk.UIManager()

        # Add the accelerator group to the toplevel window
        accelgroup = ui_manager.get_accel_group()
        self.add_accel_group(accelgroup)

        ui_manager.insert_action_group(
              self._create_actiongroup(),
              0  # position=
        )
        # Construct UI that uses previously defined action group
        ui_manager.add_ui_from_string(self.ui_string)

        # Add Find text search
        find_toolitem = ui_manager.get_widget('/ToolBar/Find')
        self.textentry = Gtk.Entry(max_length=20)
        self.textentry.set_icon_from_stock(0, Gtk.STOCK_FIND)
        find_toolitem.add(self.textentry)

        self.textentry.set_activates_default(True)
        self.textentry.connect(
              "activate", self.textentry_activate, self.textentry)
        self.textentry.connect(
              "changed", self.textentry_changed, self.textentry)

        return ui_manager.get_widget('/ToolBar')

    def _create_actiongroup(self):
        group = Gtk.ActionGroup('Actions')

        action_open = Gtk.Action(
              'Open', label=None, tooltip=None, stock_id=Gtk.STOCK_OPEN)
        action_open.connect("activate", self.on_open)
        group.add_action(action_open)

        action_reload = Gtk.Action(
              'Reload', label=None, tooltip=None, stock_id=Gtk.STOCK_REFRESH)
        action_reload.connect("activate", self.on_reload)
        group.add_action(action_reload)

        action_print = Gtk.Action(
              'Print', label=None, tooltip=None, stock_id=Gtk.STOCK_PRINT)
        action_print.connect("activate", self.plot_area.on_print)
        group.add_action(action_print)

        action_zoomin = Gtk.Action(
              'ZoomIn', label=None, tooltip=None, stock_id=Gtk.STOCK_ZOOM_IN)
        action_zoomin.connect("activate", self.plot_area.on_zoom_in)
        group.add_action(action_zoomin)

        action_zoomout = Gtk.Action(
              'ZoomOut', label=None, tooltip=None, stock_id=Gtk.STOCK_ZOOM_OUT)
        action_zoomout.connect("activate", self.plot_area.on_zoom_out)
        group.add_action(action_zoomout)

        action_zoomfit = Gtk.Action(
              'ZoomFit', label=None, tooltip=None, stock_id=Gtk.STOCK_ZOOM_FIT)
        action_zoomfit.connect("activate", self.plot_area.on_zoom_fit)
        group.add_action(action_zoomfit)

        action_zoom100 = Gtk.Action(
              'Zoom100', label=None, tooltip=None, stock_id=Gtk.STOCK_ZOOM_100)
        action_zoom100.connect("activate", self.plot_area.on_zoom_100)
        group.add_action(action_zoom100)

        self.action_back = Gtk.Action(
              'Back', label=None, tooltip=None, stock_id=Gtk.STOCK_GO_BACK)
        self.action_back.set_sensitive(False)
        self.action_back.connect("activate", self.plot_area.on_go_back)
        group.add_action(self.action_back)

        self.action_forward = Gtk.Action(
              'Forward', label=None, tooltip=None,
              stock_id=Gtk.STOCK_GO_FORWARD)
        self.action_forward.set_sensitive(False)
        self.action_forward.connect("activate", self.plot_area.on_go_forward)
        group.add_action(self.action_forward)

        action_find = FindMenuToolAction(
              "Find", label=None,
              tooltip="Find a node by name", stock_id=None)
        group.add_action(action_find)
        return group

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
            self.set_title(BASE_TITLE)
        else:
            self.set_title(os.path.basename(filename) + ' - ' + BASE_TITLE)

    def open_file(self, filename):
        try:
            fp = open(filename, 'rb')
            self.set_dotcode(fp.read(), filename)
            fp.close()
        except IOError as ex:
            self.error_dialog(str(ex))

    def on_open(self, action):
        pass
        # chooser = Gtk.FileChooserDialog(parent=self,
        #                                 title="Open dot File",
        #                                 action=Gtk.FileChooserAction.OPEN,
        #                                 buttons=(Gtk.STOCK_CANCEL,
        #                                          Gtk.ResponseType.CANCEL,
        #                                          Gtk.STOCK_OPEN,
        #                                          Gtk.ResponseType.OK))
        # chooser.set_default_response(Gtk.ResponseType.OK)
        # chooser.set_current_folder(self.last_open_dir)
        # filter = Gtk.FileFilter()
        # filter.set_name("Graphviz dot files")
        # filter.add_pattern("*.dot")
        # chooser.add_filter(filter)
        # filter = Gtk.FileFilter()
        # filter.set_name("All files")
        # filter.add_pattern("*")
        # chooser.add_filter(filter)
        # if chooser.run() == Gtk.ResponseType.OK:
        #     filename = chooser.get_filename()
        #     self.last_open_dir = chooser.get_current_folder()
        #     chooser.destroy()
        #     self.open_file(filename)
        # else:
        #     chooser.destroy()

    def on_reload(self, action):
        self.plot_area.reload()

    def error_dialog(self, message):
        dlg = Gtk.MessageDialog(parent=self,
                                type=Gtk.MessageType.ERROR,
                                message_format=message,
                                buttons=Gtk.ButtonsType.OK)
        dlg.set_title(self.base_title)
        dlg.run()
        dlg.destroy()

    def on_history(self, action, has_back, has_forward):
        self.action_back.set_sensitive(has_back)
        self.action_forward.set_sensitive(has_forward)
