import os
import re

from gi.repository import Gtk

from spielviz.ui.area import DotWidget
from spielviz.graphics.elements import Graph


class FindMenuToolAction(Gtk.Action):
    __gtype_name__ = "FindMenuToolAction"

    def do_create_tool_item(self) -> Gtk.ToolItem:
        return Gtk.ToolItem()


class DotWindow(Gtk.Window):
    ui = '''
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
    '''

    base_title = 'Dot Viewer'

    def __init__(self, widget=None, width=512, height=512):
        Gtk.Window.__init__(self)

        self.graph = Graph()

        window = self

        window.set_title(self.base_title)
        window.set_default_size(width, height)
        vbox = Gtk.VBox()
        window.add(vbox)

        self.dotwidget = widget or DotWidget()
        self.dotwidget.connect("error", lambda e, m: self.error_dialog(m))
        self.dotwidget.connect("history", self.on_history)

        # Create a UIManager instance
        uimanager = self.uimanager = Gtk.UIManager()

        # Add the accelerator group to the toplevel window
        accelgroup = uimanager.get_accel_group()
        window.add_accel_group(accelgroup)

        # Create an ActionGroup
        actiongroup = Gtk.ActionGroup('Actions')
        self.actiongroup = actiongroup

        # Create actions
        actiongroup.add_actions((
            ('Open', Gtk.STOCK_OPEN, None, None, None, self.on_open),
            ('Reload', Gtk.STOCK_REFRESH, None, None, None, self.on_reload),
            ('Print', Gtk.STOCK_PRINT, None, None,
             "Prints the currently visible part of the graph",
             self.dotwidget.on_print),
            (
                'ZoomIn', Gtk.STOCK_ZOOM_IN, None, None, None,
                self.dotwidget.on_zoom_in),
            ('ZoomOut', Gtk.STOCK_ZOOM_OUT, None, None, None,
             self.dotwidget.on_zoom_out),
            ('ZoomFit', Gtk.STOCK_ZOOM_FIT, None, None, None,
             self.dotwidget.on_zoom_fit),
            ('Zoom100', Gtk.STOCK_ZOOM_100, None, None, None,
             self.dotwidget.on_zoom_100),
        ))

        self.back_action = Gtk.Action('Back', None, None, Gtk.STOCK_GO_BACK)
        self.back_action.set_sensitive(False)
        self.back_action.connect("activate", self.dotwidget.on_go_back)
        actiongroup.add_action(self.back_action)

        self.forward_action = Gtk.Action('Forward', None, None,
                                         Gtk.STOCK_GO_FORWARD)
        self.forward_action.set_sensitive(False)
        self.forward_action.connect("activate", self.dotwidget.on_go_forward)
        actiongroup.add_action(self.forward_action)

        find_action = FindMenuToolAction("Find", None,
                                         "Find a node by name", None)
        actiongroup.add_action(find_action)

        # Add the actiongroup to the uimanager
        uimanager.insert_action_group(actiongroup, 0)

        # Add a UI descrption
        uimanager.add_ui_from_string(self.ui)

        # Create a Toolbar
        toolbar = uimanager.get_widget('/ToolBar')
        vbox.pack_start(toolbar, False, False, 0)

        vbox.pack_start(self.dotwidget, True, True, 0)

        self.last_open_dir = "."

        self.set_focus(self.dotwidget)

        # Add Find text search
        find_toolitem = uimanager.get_widget('/ToolBar/Find')
        self.textentry = Gtk.Entry(max_length=20)
        self.textentry.set_icon_from_stock(0, Gtk.STOCK_FIND)
        find_toolitem.add(self.textentry)

        self.textentry.set_activates_default(True)
        self.textentry.connect("activate", self.textentry_activate,
                               self.textentry);
        self.textentry.connect("changed", self.textentry_changed,
                               self.textentry);

        self.show_all()

    def find_text(self, entry_text):
        found_items = []
        dot_widget = self.dotwidget
        regexp = re.compile(entry_text)
        for element in dot_widget.graph.nodes + dot_widget.graph.edges:
            if element.search_text(regexp):
                found_items.append(element)
        return found_items

    def textentry_changed(self, widget, entry):
        entry_text = entry.get_text()
        dot_widget = self.dotwidget
        if not entry_text:
            dot_widget.set_highlight(None, search=True)
            return

        found_items = self.find_text(entry_text)
        dot_widget.set_highlight(found_items, search=True)

    def textentry_activate(self, widget, entry):
        entry_text = entry.get_text()
        dot_widget = self.dotwidget
        if not entry_text:
            dot_widget.set_highlight(None, search=True)
            return

        found_items = self.find_text(entry_text)
        dot_widget.set_highlight(found_items, search=True)
        if (len(found_items) == 1):
            dot_widget.animate_to(found_items[0].x, found_items[0].y)

    def set_filter(self, filter):
        self.dotwidget.set_filter(filter)

    def set_dotcode(self, dotcode, filename=None):
        if self.dotwidget.set_dotcode(dotcode, filename):
            self.update_title(filename)
            self.dotwidget.zoom_to_fit()

    def set_xdotcode(self, xdotcode, filename=None):
        if self.dotwidget.set_xdotcode(xdotcode):
            self.update_title(filename)
            self.dotwidget.zoom_to_fit()

    def update_title(self, filename=None):
        if filename is None:
            self.set_title(self.base_title)
        else:
            self.set_title(os.path.basename(filename) + ' - ' + self.base_title)

    def open_file(self, filename):
        try:
            fp = open(filename, 'rb')
            self.set_dotcode(fp.read(), filename)
            fp.close()
        except IOError as ex:
            self.error_dialog(str(ex))

    def on_open(self, action):
        chooser = Gtk.FileChooserDialog(parent=self,
                                        title="Open dot File",
                                        action=Gtk.FileChooserAction.OPEN,
                                        buttons=(Gtk.STOCK_CANCEL,
                                                 Gtk.ResponseType.CANCEL,
                                                 Gtk.STOCK_OPEN,
                                                 Gtk.ResponseType.OK))
        chooser.set_default_response(Gtk.ResponseType.OK)
        chooser.set_current_folder(self.last_open_dir)
        filter = Gtk.FileFilter()
        filter.set_name("Graphviz dot files")
        filter.add_pattern("*.dot")
        chooser.add_filter(filter)
        filter = Gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        chooser.add_filter(filter)
        if chooser.run() == Gtk.ResponseType.OK:
            filename = chooser.get_filename()
            self.last_open_dir = chooser.get_current_folder()
            chooser.destroy()
            self.open_file(filename)
        else:
            chooser.destroy()

    def on_reload(self, action):
        self.dotwidget.reload()

    def error_dialog(self, message):
        dlg = Gtk.MessageDialog(parent=self,
                                type=Gtk.MessageType.ERROR,
                                message_format=message,
                                buttons=Gtk.ButtonsType.OK)
        dlg.set_title(self.base_title)
        dlg.run()
        dlg.destroy()

    def on_history(self, action, has_back, has_forward):
        self.back_action.set_sensitive(has_back)
        self.forward_action.set_sensitive(has_forward)
