import math
import time
from gi.overrides.Gdk import EventButton
from gi.repository import GObject, Gdk, Gtk


class PressState:
  x: int = 0
  y: int = 0
  time: float = 0.

  def is_click(self, event: EventButton, click_fuzz: int = 4,
               click_timeout: float = 1.0) -> bool:
    """
    Differentiate between clicking or start of dragging.
    """
    assert event.type == Gdk.EventType.BUTTON_RELEASE
    dx = self.x - event.x
    dy = self.y - event.y
    return (time.time() < self.time + click_timeout and
            math.hypot(dx, dy) < click_fuzz)

  def update(self, event: EventButton) -> None:
    assert event.type == Gdk.EventType.BUTTON_PRESS
    self.time = time.time()
    self.x = event.x
    self.y = event.y
