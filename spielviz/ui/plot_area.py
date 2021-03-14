import logging
import math
import time
from typing import Set, Tuple

import cairo
import pyspiel
from gi.overrides.Gdk import EventButton, EventMotion
from gi.repository import GObject, Gdk, Gtk
from gi.repository.Gdk import Rectangle

import spielviz.config as cfg
import spielviz.graphics.elements as elements
from spielviz.dot.parser import make_graph, make_xdotcode
from spielviz.logic.dotcode_tree import GameTreeViz
from spielviz.ui import actions, animation, spielviz_events, press_state


class PlotArea(GObject.GObject):
  """GTK widget that draws dot graphs."""

  __gsignals__ = {
    spielviz_events.CHANGE_HISTORY: (GObject.SIGNAL_RUN_LAST, None, (str,))
  }

  def __init__(self, draw_area: Gtk.DrawingArea, window) -> None:
    GObject.GObject.__init__(self)

    # Gtk objects
    self.area = draw_area
    self.area.set_can_focus(True)
    self.window = window  # MainWindow, no type signature because of cyclic ref.

    # Event listeners.
    self.area.connect("draw", self.on_draw)
    self.area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                         Gdk.EventMask.BUTTON_RELEASE_MASK)
    self.area.connect("button-press-event", self.on_area_button_press)
    self.area.connect("button-release-event", self.on_area_button_release)
    self.area.add_events(Gdk.EventMask.POINTER_MOTION_MASK |
                         Gdk.EventMask.POINTER_MOTION_HINT_MASK |
                         Gdk.EventMask.BUTTON_RELEASE_MASK |
                         Gdk.EventMask.SCROLL_MASK)
    self.area.connect("motion-notify-event", self.on_area_motion_notify)
    self.area.connect("scroll-event", self.on_area_scroll_event)
    self.area.connect("size-allocate", self.on_area_size_allocate)
    self.area.connect('key-press-event', self.on_key_press_event)

    # Underlying x-dotted graph (with positions)
    self.graph = elements.Graph()
    # Set of nodes to highlight.
    self.highlight: Set[elements.Node] = set()

    self.graph_x, self.graph_y = 0.0, 0.0
    self.zoom_ratio = 1.0
    self.zoom_to_fit_on_resize = True
    self.animation = animation.NoAnimation(self)

    # When user presses a button, what drag action should be done?
    self.drag_action = actions.NullAction(self)
    # Differentiate between clicking and dragging in the plot area.
    self.press_state = press_state.PressState()


  def update(self, state: pyspiel.State, **kwargs):
    gametree = GameTreeViz(state=state, **kwargs)
    count = 0
    for _ in gametree.build_tree():
      if count >= cfg.TREE_MAX_NODES:
        logging.warning("There are too many nodes in the tree. "
                        f"Showing only {count} of them.")
        break
      count += 1

    dotcode = gametree.to_string().encode()
    xdotcode = make_xdotcode(dotcode)
    self.graph = make_graph(xdotcode)

  def show_all(self):
    self.zoom_to_fit()
    self.area.queue_draw()

  def _draw_graph(self, cr: cairo.Context, rect: Rectangle) -> None:
    w, h = float(rect.width), float(rect.height)
    cx, cy = 0.5 * w, 0.5 * h
    x, y, ratio = self.graph_x, self.graph_y, self.zoom_ratio
    x0, y0 = x - cx / ratio, y - cy / ratio
    x1, y1 = x0 + w / ratio, y0 + h / ratio
    bounding = (x0, y0, x1, y1)

    cr.translate(cx, cy)
    cr.scale(ratio, ratio)
    cr.translate(-x, -y)
    self.graph.draw(cr, highlight_items=self.highlight, bounding=bounding)

  def on_draw(self, widget, cr: cairo.Context) -> bool:
    rect = self.area.get_allocation()
    Gtk.render_background(self.area.get_style_context(), cr, 0, 0,
                          rect.width, rect.height)

    cr.save()
    self._draw_graph(cr, rect)
    cr.restore()

    self.drag_action.draw(cr)

    return False

  def get_current_pos(self):
    return self.graph_x, self.graph_y

  def set_current_pos(self, x, y):
    self.graph_x = x
    self.graph_y = y
    self.area.queue_draw()

  def set_highlight(self, items: Set[elements.Node] = set()) -> None:
    if self.highlight != items:
      self.highlight = items
      self.area.queue_draw()

  def zoom_image(self, zoom_ratio: float, center: bool = False,
      pos: None = None) -> None:
    # Constrain zoom ratio to a sane range to prevent numeric instability.
    zoom_ratio = min(zoom_ratio, 1E4)
    zoom_ratio = max(zoom_ratio, 1E-6)

    if center:
      self.graph_x = self.graph.width / 2
      self.graph_y = self.graph.height / 2
    elif pos is not None:
      rect = self.area.get_allocation()
      x, y = pos
      x -= 0.5 * rect.width
      y -= 0.5 * rect.height
      self.graph_x += x / self.zoom_ratio - x / zoom_ratio
      self.graph_y += y / self.zoom_ratio - y / zoom_ratio
    self.zoom_ratio = zoom_ratio
    self.zoom_to_fit_on_resize = False
    self.area.queue_draw()

  def zoom_to_area(self, x1, y1, x2, y2):
    rect = self.area.get_allocation()
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
    self.graph_x = (x1 + x2) / 2
    self.graph_y = (y1 + y2) / 2
    self.area.queue_draw()

  def zoom_to_fit(self) -> None:
    rect = self.area.get_allocation()
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
  POS_INCREMENT = 100

  def on_key_press_event(self, widget, event):
    if event.keyval == Gdk.KEY_Left:
      self.graph_x -= self.POS_INCREMENT / self.zoom_ratio
      self.area.queue_draw()
      return True
    if event.keyval == Gdk.KEY_Right:
      self.graph_x += self.POS_INCREMENT / self.zoom_ratio
      self.area.queue_draw()
      return True
    if event.keyval == Gdk.KEY_Up:
      self.graph_y -= self.POS_INCREMENT / self.zoom_ratio
      self.area.queue_draw()
      return True
    if event.keyval == Gdk.KEY_Down:
      self.graph_y += self.POS_INCREMENT / self.zoom_ratio
      self.area.queue_draw()
      return True
    if event.keyval in (Gdk.KEY_Page_Up,
                        Gdk.KEY_plus,
                        Gdk.KEY_equal,
                        Gdk.KEY_KP_Add):
      self.zoom_image(self.zoom_ratio * self.ZOOM_INCREMENT)
      self.area.queue_draw()
      return True
    if event.keyval in (Gdk.KEY_Page_Down,
                        Gdk.KEY_minus,
                        Gdk.KEY_KP_Subtract):
      self.zoom_image(self.zoom_ratio / self.ZOOM_INCREMENT)
      self.area.queue_draw()
      return True
    if event.keyval == Gdk.KEY_Escape:
      self.drag_action.abort()
      self.drag_action = actions.NullAction(self)
      return True
    if event.keyval == Gdk.KEY_f:
      win = widget.self.area.get_toplevel()
      find_toolitem = win.uimanager.get_widget('/ToolBar/Find')
      textentry = find_toolitem.get_children()
      win.set_focus(textentry[0])
      return True
    if event.keyval == Gdk.KEY_q:
      Gtk.main_quit()
      return True
    return False

  def draw_page(self, operation, context, page_nr):
    cr = context.get_cairo_context()
    rect = self.area.get_allocation()
    self._draw_graph(cr, rect)

  def on_area_button_press(self, area, event: EventButton) -> bool:
    self.animation.stop()
    self.drag_action.abort()
    action_type = actions.get_drag_action(event)
    self.drag_action = action_type(self)
    self.drag_action.on_button_press(event)
    self.press_state.update(event)
    return False

  def on_click(self, element: elements.Element, event: EventButton) -> bool:
    """Override this method in subclass to process
    click events. Note that element can be None
    (click on empty space)."""
    if isinstance(element, elements.Node):
      history_str = element.id.decode().strip()
      self.emit(spielviz_events.CHANGE_HISTORY, history_str)
    return False

  def on_area_button_release(self, area, event: EventButton) -> bool:
    self.drag_action.on_button_release(event)
    self.drag_action = actions.NullAction(self)
    x, y = int(event.x), int(event.y)
    if self.press_state.is_click(event):
      el = self.get_element(x, y)
      if self.on_click(el, event):
        return True

    return event.button in (Gdk.BUTTON_PRIMARY, Gdk.BUTTON_MIDDLE)

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
    self.animation = animation.ZoomToAnimation(self, x, y)
    self.animation.start()

  def window2graph(self, x: int, y: int) -> Tuple[float, float]:
    rect = self.area.get_allocation()
    x -= 0.5 * rect.width
    y -= 0.5 * rect.height
    x /= self.zoom_ratio
    y /= self.zoom_ratio
    x += self.graph_x
    y += self.graph_y
    return x, y

  def get_element(self, x: int, y: int) -> elements.Node:
    x, y = self.window2graph(x, y)
    return self.graph.get_element(x, y)

  def get_jump(self, x: int, y: int) -> None:
    x, y = self.window2graph(x, y)
    return self.graph.get_jump(x, y)
