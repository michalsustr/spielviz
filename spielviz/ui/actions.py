from cairo import Context
from gi.overrides.Gdk import EventButton, EventMotion
from gi.repository import Gdk, Gtk
from typing import Type


class DragAction(object):
  def __init__(self, plot_area) -> None:
    self.plot_area = plot_area

  def on_button_press(self, event: EventButton) -> None:
    self.startmousex = self.prevmousex = event.x
    self.startmousey = self.prevmousey = event.y
    self.start()

  def on_motion_notify(self, event: EventButton):
    if event.is_hint:
      window, x, y, state = event.window.get_device_position(event.device)
    else:
      x, y, state = event.x, event.y, event.state
    deltax = self.prevmousex - x
    deltay = self.prevmousey - y
    self.drag(deltax, deltay)
    self.prevmousex = x
    self.prevmousey = y

  def on_button_release(self, event: EventButton) -> None:
    self.stopmousex = event.x
    self.stopmousey = event.y
    self.stop()

  def draw(self, cr: Context) -> None:
    pass

  def start(self):
    pass

  def drag(self, deltax, deltay):
    pass

  def stop(self):
    pass

  def abort(self) -> None:
    pass


class NullAction(DragAction):
  def on_motion_notify(self, event: EventMotion) -> None:
    if event.is_hint:
      window, x, y, state = event.window.get_device_position(event.device)
    else:
      x, y, state = event.x, event.y, event.state
    item = self.plot_area.get_jump(x, y)
    if item is not None:
      self.plot_area.area.get_window().set_cursor(
        Gdk.Cursor(Gdk.CursorType.HAND2))
      self.plot_area.set_highlight(item.highlight)
    else:
      # plot_area.get_window().set_cursor(None)
      self.plot_area.set_highlight(None)


class PanAction(DragAction):
  def start(self) -> None:
    self.plot_area.area.get_window().set_cursor(
        Gdk.Cursor(Gdk.CursorType.FLEUR))

  def drag(self, deltax, deltay):
    self.plot_area.graph_x += deltax / self.plot_area.zoom_ratio
    self.plot_area.graph_y += deltay / self.plot_area.zoom_ratio
    self.plot_area.area.queue_draw()

  def stop(self) -> None:
    self.plot_area.area.get_window().set_cursor(None)

  abort = stop


class ZoomAction(DragAction):
  def drag(self, deltax, deltay):
    self.plot_area.zoom_ratio *= 1.005 ** (deltax + deltay)
    self.plot_area.zoom_to_fit_on_resize = False
    self.plot_area.area.queue_draw()

  def stop(self):
    self.plot_area.area.queue_draw()


class ZoomAreaAction(DragAction):
  def drag(self, deltax, deltay):
    self.plot_area.area.queue_draw()

  def draw(self, cr):
    cr.save()
    cr.set_source_rgba(.5, .5, 1.0, 0.25)
    cr.rectangle(self.startmousex, self.startmousey,
                 self.prevmousex - self.startmousex,
                 self.prevmousey - self.startmousey)
    cr.fill()
    cr.set_source_rgba(.5, .5, 1.0, 1.0)
    cr.set_line_width(1)
    cr.rectangle(self.startmousex - .5, self.startmousey - .5,
                 self.prevmousex - self.startmousex + 1,
                 self.prevmousey - self.startmousey + 1)
    cr.stroke()
    cr.restore()

  def stop(self):
    x1, y1 = self.plot_area.window2graph(self.startmousex,
                                         self.startmousey)
    x2, y2 = self.plot_area.window2graph(self.stopmousex,
                                         self.stopmousey)
    self.plot_area.zoom_to_area(x1, y1, x2, y2)

  def abort(self):
    self.plot_area.area.queue_draw()


def get_drag_action(event: EventButton) -> Type[DragAction]:
  state = event.state
  if event.button in (Gdk.BUTTON_PRIMARY, Gdk.BUTTON_MIDDLE):
    modifiers = Gtk.accelerator_get_default_mod_mask()
    if state & modifiers == Gdk.ModifierType.CONTROL_MASK:
      return ZoomAction
    elif state & modifiers == Gdk.ModifierType.SHIFT_MASK:
      return ZoomAreaAction
    else:
      return PanAction
  return NullAction
