import math
import time

from gi.repository import GLib


class Animation(object):
    step = 0.03  # seconds

    def __init__(self, plot_area) -> None:
        self.plot_area = plot_area
        self.timeout_id = None

    def start(self):
        self.timeout_id = GLib.timeout_add(int(self.step * 1000),
                                           self.__real_tick)

    def stop(self):
        self.plot_area.animation = NoAnimation(self.plot_area)
        if self.timeout_id is not None:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None

    def __real_tick(self):
        try:
            if not self.tick():
                self.stop()
                return False
        except AttributeError as e:
            self.stop()
            raise e
        return True

    def tick(self):
        return False


class NoAnimation(Animation):
    def start(self):
        pass

    def stop(self) -> None:
        pass


class LinearAnimation(Animation):
    duration = 0.6

    def start(self):
        self.started = time.time()
        Animation.start(self)

    def tick(self):
        t = (time.time() - self.started) / self.duration
        self.animate(max(0, min(t, 1)))
        return (t < 1)

    def animate(self, t):
        pass


class MoveToAnimation(LinearAnimation):
    def __init__(self, plot_area, target_x, target_y):
        Animation.__init__(self, plot_area)
        self.source_x = plot_area.x
        self.source_y = plot_area.y
        self.target_x = target_x
        self.target_y = target_y

    def animate(self, t):
        sx, sy = self.source_x, self.source_y
        tx, ty = self.target_x, self.target_y
        self.plot_area.x = tx * t + sx * (1 - t)
        self.plot_area.y = ty * t + sy * (1 - t)
        self.plot_area.area.queue_draw()


class ZoomToAnimation(MoveToAnimation):
    def __init__(self, plot_area, target_x, target_y):
        MoveToAnimation.__init__(self, plot_area, target_x, target_y)
        self.source_zoom = plot_area.zoom_ratio
        self.target_zoom = self.source_zoom
        self.extra_zoom = 0

        middle_zoom = 0.5 * (self.source_zoom + self.target_zoom)

        distance = math.hypot(self.source_x - self.target_x,
                              self.source_y - self.target_y)
        rect = self.plot_area.area.get_allocation()
        visible = min(rect.width, rect.height) / self.plot_area.zoom_ratio
        visible *= 0.9
        if distance > 0:
            desired_middle_zoom = visible / distance
            self.extra_zoom = min(0, 4 * (desired_middle_zoom - middle_zoom))

    def animate(self, t):
        a, b, c = self.source_zoom, self.extra_zoom, self.target_zoom
        self.plot_area.zoom_ratio = c * t + b * t * (1 - t) + a * (1 - t)
        self.plot_area.zoom_to_fit_on_resize = False
        MoveToAnimation.animate(self, t)
