import math
import os
import subprocess
import sys
import time
from typing import Optional, Set, Tuple, Type

from cairo import Context
from gi.overrides.Gdk import EventButton, EventMotion
from gi.repository import GLib, GObject, Gdk, Gtk
from gi.repository.Gdk import Rectangle

from spielviz.dot.lexer import ParseError
from spielviz.dot.parser import XDotParser
from spielviz.ui import actions, animation
from spielviz.ui.actions import PanAction
from spielviz.ui.elements import Graph
from spielviz.ui.elements import Node, Url


# See http://www.graphviz.org/pub/scm/graphviz-cairo/plugin/cairo/gvrender_cairo.c

# For pygtk inspiration and guidance see:
# - http://mirageiv.berlios.de/
# - http://comix.sourceforge.net/

class DotWidget(Gtk.DrawingArea):
    """GTK widget that draws dot graphs."""

    # TODO GTK3: Second argument has to be of type Gdk.EventButton instead of object.
    __gsignals__ = {
        'clicked': (GObject.SIGNAL_RUN_LAST, None, (str, object)),
        'error': (GObject.SIGNAL_RUN_LAST, None, (str,)),
        'history': (GObject.SIGNAL_RUN_LAST, None, (bool, bool))
    }

    filter = 'dot'

    def __init__(self) -> None:
        Gtk.DrawingArea.__init__(self)

        self.graph = Graph()
        self.openfilename = None

        self.set_can_focus(True)

        self.connect("draw", self.on_draw)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect("button-press-event", self.on_area_button_press)
        self.connect("button-release-event", self.on_area_button_release)
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.POINTER_MOTION_HINT_MASK |
                        Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.SCROLL_MASK)
        self.connect("motion-notify-event", self.on_area_motion_notify)
        self.connect("scroll-event", self.on_area_scroll_event)
        self.connect("size-allocate", self.on_area_size_allocate)

        self.connect('key-press-event', self.on_key_press_event)
        self.last_mtime = None

        GLib.timeout_add(1000, self.update)

        self.x, self.y = 0.0, 0.0
        self.zoom_ratio = 1.0
        self.zoom_to_fit_on_resize = False
        self.animation = animation.NoAnimation(self)
        self.drag_action = actions.NullAction(self)
        self.presstime = None
        self.highlight = None
        self.highlight_search = False
        self.history_back = []
        self.history_forward = []

    def error_dialog(self, message):
        self.emit('error', message)

    def set_filter(self, filter):
        self.filter = filter

    def run_filter(self, dotcode: bytes) -> bytes:
        if not self.filter:
            return dotcode
        try:
            p = subprocess.Popen(
                  [self.filter, '-Txdot'],
                  stdin=subprocess.PIPE,
                  stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE,
                  shell=False,
                  universal_newlines=False
            )
        except OSError as exc:
            error = '%s: %s' % (self.filter, exc.strerror)
            p = subprocess.CalledProcessError(exc.errno, self.filter,
                                              exc.strerror)
        else:
            xdotcode, error = p.communicate(dotcode)
            error = error.decode()
        error = error.rstrip()
        if error:
            sys.stderr.write(error + '\n')
        if p.returncode != 0:
            self.error_dialog(error)
            return None
        return xdotcode

    def _set_dotcode(self, dotcode: bytes, filename: None = None,
          center: bool = True) -> bool:
        # By default DOT language is UTF-8, but it accepts other encodings
        assert isinstance(dotcode, bytes)
        xdotcode = self.run_filter(dotcode)
        if xdotcode is None:
            return False
        try:
            self.set_xdotcode(xdotcode, center=center)
        except ParseError as ex:
            self.error_dialog(str(ex))
            return False
        else:
            return True

    def set_dotcode(self, dotcode: bytes, filename: str = None,
          center: bool = True) -> bool:
        self.openfilename = None
        if self._set_dotcode(dotcode, filename, center=center):
            if filename is None:
                self.last_mtime = None
            else:
                self.last_mtime = os.stat(filename).st_mtime
            self.openfilename = filename
            return True

    def set_xdotcode(self, xdotcode: bytes, center: bool = True) -> None:
        assert isinstance(xdotcode, bytes)
        parser = XDotParser(xdotcode)
        self.graph = parser.parse()
        # pprint(self.graph.nodes[0].__dict__)
        self.zoom_image(self.zoom_ratio, center=center)

    def reload(self) -> None:
        if self.openfilename is not None:
            try:
                fp = open(self.openfilename, 'rb')
                self._set_dotcode(fp.read(), self.openfilename, center=False)
                fp.close()
            except IOError:
                pass
            else:
                del self.history_back[:], self.history_forward[:]

    def update(self) -> bool:
        if self.openfilename is not None:
            try:
                current_mtime = os.stat(self.openfilename).st_mtime
            except OSError:
                return True
            if current_mtime != self.last_mtime:
                self.last_mtime = current_mtime
                self.reload()
        return True

    def _draw_graph(self, cr: Context, rect: Rectangle) -> None:
        w, h = float(rect.width), float(rect.height)
        cx, cy = 0.5 * w, 0.5 * h
        x, y, ratio = self.x, self.y, self.zoom_ratio
        x0, y0 = x - cx / ratio, y - cy / ratio
        x1, y1 = x0 + w / ratio, y0 + h / ratio
        bounding = (x0, y0, x1, y1)

        cr.translate(cx, cy)
        cr.scale(ratio, ratio)
        cr.translate(-x, -y)
        self.graph.draw(cr, highlight_items=self.highlight, bounding=bounding)

    def on_draw(self, widget, cr: Context) -> bool:
        rect = self.get_allocation()
        Gtk.render_background(self.get_style_context(), cr, 0, 0,
                              rect.width, rect.height)

        cr.save()
        self._draw_graph(cr, rect)
        cr.restore()

        self.drag_action.draw(cr)

        return False

    def get_current_pos(self):
        return self.x, self.y

    def set_current_pos(self, x, y):
        self.x = x
        self.y = y
        self.queue_draw()

    def set_highlight(self, items: Optional[Set[Node]],
          search: bool = False) -> None:
        # Enable or disable search highlight
        if search:
            self.highlight_search = items is not None
        # Ignore cursor highlight while searching
        if self.highlight_search and not search:
            return
        if self.highlight != items:
            self.highlight = items
            self.queue_draw()

    def zoom_image(self, zoom_ratio: float, center: bool = False,
          pos: None = None) -> None:
        # Constrain zoom ratio to a sane range to prevent numeric instability.
        zoom_ratio = min(zoom_ratio, 1E4)
        zoom_ratio = max(zoom_ratio, 1E-6)

        if center:
            self.x = self.graph.width / 2
            self.y = self.graph.height / 2
        elif pos is not None:
            rect = self.get_allocation()
            x, y = pos
            x -= 0.5 * rect.width
            y -= 0.5 * rect.height
            self.x += x / self.zoom_ratio - x / zoom_ratio
            self.y += y / self.zoom_ratio - y / zoom_ratio
        self.zoom_ratio = zoom_ratio
        self.zoom_to_fit_on_resize = False
        self.queue_draw()

    def zoom_to_area(self, x1, y1, x2, y2):
        rect = self.get_allocation()
        width = abs(x1 - x2)
        height = abs(y1 - y2)
        if width == 0 and height == 0:
            self.zoom_ratio *= self.ZOOM_INCREMENT
        else:
            self.zoom_ratio = min(
                  float(rect.width) / float(width),
                  float(rect.height) / float(height)
            )
        self.zoom_to_fit_on_resize = False
        self.x = (x1 + x2) / 2
        self.y = (y1 + y2) / 2
        self.queue_draw()

    def zoom_to_fit(self) -> None:
        rect = self.get_allocation()
        rect.x += self.ZOOM_TO_FIT_MARGIN
        rect.y += self.ZOOM_TO_FIT_MARGIN
        rect.width -= 2 * self.ZOOM_TO_FIT_MARGIN
        rect.height -= 2 * self.ZOOM_TO_FIT_MARGIN
        zoom_ratio = min(
              float(rect.width) / float(self.graph.width),
              float(rect.height) / float(self.graph.height)
        )
        self.zoom_image(zoom_ratio, center=True)
        self.zoom_to_fit_on_resize = True

    ZOOM_INCREMENT = 1.25
    ZOOM_TO_FIT_MARGIN = 12

    def on_zoom_in(self, action):
        self.zoom_image(self.zoom_ratio * self.ZOOM_INCREMENT)

    def on_zoom_out(self, action):
        self.zoom_image(self.zoom_ratio / self.ZOOM_INCREMENT)

    def on_zoom_fit(self, action):
        self.zoom_to_fit()

    def on_zoom_100(self, action):
        self.zoom_image(1.0)

    POS_INCREMENT = 100

    def on_key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_Left:
            self.x -= self.POS_INCREMENT / self.zoom_ratio
            self.queue_draw()
            return True
        if event.keyval == Gdk.KEY_Right:
            self.x += self.POS_INCREMENT / self.zoom_ratio
            self.queue_draw()
            return True
        if event.keyval == Gdk.KEY_Up:
            self.y -= self.POS_INCREMENT / self.zoom_ratio
            self.queue_draw()
            return True
        if event.keyval == Gdk.KEY_Down:
            self.y += self.POS_INCREMENT / self.zoom_ratio
            self.queue_draw()
            return True
        if event.keyval in (Gdk.KEY_Page_Up,
                            Gdk.KEY_plus,
                            Gdk.KEY_equal,
                            Gdk.KEY_KP_Add):
            self.zoom_image(self.zoom_ratio * self.ZOOM_INCREMENT)
            self.queue_draw()
            return True
        if event.keyval in (Gdk.KEY_Page_Down,
                            Gdk.KEY_minus,
                            Gdk.KEY_KP_Subtract):
            self.zoom_image(self.zoom_ratio / self.ZOOM_INCREMENT)
            self.queue_draw()
            return True
        if event.keyval == Gdk.KEY_Escape:
            self.drag_action.abort()
            self.drag_action = actions.NullAction(self)
            return True
        if event.keyval == Gdk.KEY_r:
            self.reload()
            return True
        if event.keyval == Gdk.KEY_f:
            win = widget.get_toplevel()
            find_toolitem = win.uimanager.get_widget('/ToolBar/Find')
            textentry = find_toolitem.get_children()
            win.set_focus(textentry[0])
            return True
        if event.keyval == Gdk.KEY_q:
            Gtk.main_quit()
            return True
        if event.keyval == Gdk.KEY_p:
            self.on_print()
            return True
        return False

    print_settings = None

    def on_print(self, action=None):
        print_op = Gtk.PrintOperation()

        if self.print_settings is not None:
            print_op.set_print_settings(self.print_settings)

        print_op.connect("begin_print", self.begin_print)
        print_op.connect("draw_page", self.draw_page)

        res = print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG,
                           self.get_toplevel())
        if res == Gtk.PrintOperationResult.APPLY:
            self.print_settings = print_op.get_print_settings()

    def begin_print(self, operation, context):
        operation.set_n_pages(1)
        return True

    def draw_page(self, operation, context, page_nr):
        cr = context.get_cairo_context()
        rect = self.get_allocation()
        self._draw_graph(cr, rect)

    def get_drag_action(self, event: EventButton) -> Type[PanAction]:
        state = event.state
        if event.button in (1, 2):  # left or middle button
            modifiers = Gtk.accelerator_get_default_mod_mask()
            if state & modifiers == Gdk.ModifierType.CONTROL_MASK:
                return actions.ZoomAction
            elif state & modifiers == Gdk.ModifierType.SHIFT_MASK:
                return actions.ZoomAreaAction
            else:
                return actions.PanAction
        return actions.NullAction

    def on_area_button_press(self, area, event: EventButton) -> bool:
        self.animation.stop()
        self.drag_action.abort()
        action_type = self.get_drag_action(event)
        self.drag_action = action_type(self)
        self.drag_action.on_button_press(event)
        self.presstime = time.time()
        self.pressx = event.x
        self.pressy = event.y
        return False

    def is_click(self, event: EventButton, click_fuzz: int = 4,
          click_timeout: float = 1.0) -> bool:
        assert event.type == Gdk.EventType.BUTTON_RELEASE
        if self.presstime is None:
            # got a button release without seeing the press?
            return False
        # XXX instead of doing this complicated logic, shouldn't we listen
        # for gtk's clicked event instead?
        deltax = self.pressx - event.x
        deltay = self.pressy - event.y
        return (time.time() < self.presstime + click_timeout and
                math.hypot(deltax, deltay) < click_fuzz)

    def on_click(self, element: Node, event: EventButton) -> bool:
        """Override this method in subclass to process
        click events. Note that element can be None
        (click on empty space)."""
        return False

    def on_area_button_release(self, area, event: EventButton) -> bool:
        self.drag_action.on_button_release(event)
        self.drag_action = actions.NullAction(self)
        x, y = int(event.x), int(event.y)
        if self.is_click(event):
            el = self.get_element(x, y)
            if self.on_click(el, event):
                return True

            if event.button == 1:
                url = self.get_url(x, y)
                if url is not None:
                    self.emit('clicked', url.url, event)
                else:
                    jump = self.get_jump(x, y)
                    if jump is not None:
                        self.animate_to(jump.x, jump.y)

                return True

        if event.button == 1 or event.button == 2:
            return True
        return False

    def on_area_scroll_event(self, area, event):
        if event.direction == Gdk.ScrollDirection.UP:
            self.zoom_image(self.zoom_ratio * self.ZOOM_INCREMENT,
                            pos=(event.x, event.y))
            return True
        if event.direction == Gdk.ScrollDirection.DOWN:
            self.zoom_image(self.zoom_ratio / self.ZOOM_INCREMENT,
                            pos=(event.x, event.y))
            return True
        return False

    def on_area_motion_notify(self, area, event: EventMotion) -> bool:
        self.drag_action.on_motion_notify(event)
        return True

    def on_area_size_allocate(self, area, allocation: Rectangle) -> None:
        if self.zoom_to_fit_on_resize:
            self.zoom_to_fit()

    def animate_to(self, x, y):
        del self.history_forward[:]
        self.history_back.append(self.get_current_pos())
        self.history_changed()
        self._animate_to(x, y)

    def _animate_to(self, x, y):
        self.animation = animation.ZoomToAnimation(self, x, y)
        self.animation.start()

    def history_changed(self):
        self.emit(
              'history',
              bool(self.history_back),
              bool(self.history_forward))

    def on_go_back(self, action=None):
        try:
            item = self.history_back.pop()
        except LookupError:
            return
        self.history_forward.append(self.get_current_pos())
        self.history_changed()
        self._animate_to(*item)

    def on_go_forward(self, action=None):
        try:
            item = self.history_forward.pop()
        except LookupError:
            return
        self.history_back.append(self.get_current_pos())
        self.history_changed()
        self._animate_to(*item)

    def window2graph(self, x: int, y: int) -> Tuple[float, float]:
        rect = self.get_allocation()
        x -= 0.5 * rect.width
        y -= 0.5 * rect.height
        x /= self.zoom_ratio
        y /= self.zoom_ratio
        x += self.x
        y += self.y
        return x, y

    def get_element(self, x: int, y: int) -> Node:
        x, y = self.window2graph(x, y)
        return self.graph.get_element(x, y)

    def get_url(self, x: int, y: int) -> Optional[Url]:
        x, y = self.window2graph(x, y)
        return self.graph.get_url(x, y)

    def get_jump(self, x: int, y: int) -> None:
        x, y = self.window2graph(x, y)
        return self.graph.get_jump(x, y)
