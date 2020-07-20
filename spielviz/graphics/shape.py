import math
import operator
from typing import Iterable

import cairo
from gi.repository import GObject, Gdk, GdkPixbuf, Pango, PangoCairo

_inf = float('inf')
_get_bounding = operator.attrgetter('bounding')


class Shape:
  """Abstract base class for all the drawing shapes."""
  bounding = (-_inf, -_inf, _inf, _inf)

  def __init__(self):
    pass

  def _intersects(self, bounding):
    x0, y0, x1, y1 = bounding
    x2, y2, x3, y3 = self.bounding
    return x2 <= x1 and x0 <= x3 and y2 <= y1 and y0 <= y3

  def _fully_in(self, bounding):
    x0, y0, x1, y1 = bounding
    x2, y2, x3, y3 = self.bounding
    return x0 <= x2 and x3 <= x1 and y0 <= y2 and y3 <= y1

  def _draw(self, cr, highlight, bounding):
    """Actual draw implementation"""
    raise NotImplementedError

  def draw(self, cr, highlight=False, bounding=None):
    """Draw this shape with the given cairo context"""
    if bounding is None or self._intersects(bounding):
      self._draw(cr, highlight, bounding)

  def select_pen(self, highlight):
    if highlight:
      if not hasattr(self, 'highlight_pen'):
        self.highlight_pen = self.pen.highlighted()
      return self.highlight_pen
    else:
      return self.pen

  def search_text(self, regexp):
    return False

  @staticmethod
  def _bounds_from_points(points):
    x0, y0 = points[0]
    x1, y1 = x0, y0
    for i in range(1, len(points)):
      x, y = points[i]
      x0, x1 = min(x0, x), max(x1, x)
      y0, y1 = min(y0, y), max(y1, y)
    return x0, y0, x1, y1

  @staticmethod
  def _envelope_bounds(*args):
    xa = ya = _inf
    xb = yb = -_inf
    for bounds in args:
      for x0, y0, x1, y1 in bounds:
        xa, xb = min(xa, x0), max(xb, x1)
        ya, yb = min(ya, y0), max(yb, y1)
    return xa, ya, xb, yb


class TextShape(Shape):
  LEFT, CENTER, RIGHT = -1, 0, 1

  def __init__(self, pen, x, y, j, w, t):
    Shape.__init__(self)
    self.pen = pen.copy()
    self.x = x
    self.y = y
    self.j = j  # Centering
    self.w = w  # width
    self.t = t  # text

  def _draw(self, cr, highlight, bounding):
    try:
      layout = self.layout
    except AttributeError:
      layout = PangoCairo.create_layout(cr)

      # set font options
      # see http://lists.freedesktop.org/archives/cairo/2007-February/009688.html
      context = layout.get_context()
      fo = cairo.FontOptions()
      fo.set_antialias(cairo.ANTIALIAS_DEFAULT)
      fo.set_hint_style(cairo.HINT_STYLE_NONE)
      fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
      try:
        PangoCairo.context_set_font_options(context, fo)
      except TypeError:
        # XXX: Some broken pangocairo bindings show the error
        # 'TypeError: font_options must be a cairo.FontOptions or None'
        pass
      except KeyError:
        # cairo.FontOptions is not registered as a foreign
        # struct in older PyGObject versions.
        # https://git.gnome.org/browse/pygobject/commit/?id=b21f66d2a399b8c9a36a1758107b7bdff0ec8eaa
        pass

      # set font
      font = Pango.FontDescription()

      # https://developer.gnome.org/pango/stable/PangoMarkupFormat.html
      markup = GObject.markup_escape_text(self.t)
      if self.pen.bold:
        markup = '<b>' + markup + '</b>'
      if self.pen.italic:
        markup = '<i>' + markup + '</i>'
      if self.pen.underline:
        markup = '<span underline="single">' + markup + '</span>'
      if self.pen.strikethrough:
        markup = '<s>' + markup + '</s>'
      if self.pen.superscript:
        markup = '<sup><small>' + markup + '</small></sup>'
      if self.pen.subscript:
        markup = '<sub><small>' + markup + '</small></sub>'

      success, attrs, text, accel_char = Pango.parse_markup(markup, -1,
                                                            '\x00')
      assert success
      layout.set_attributes(attrs)

      font.set_family(self.pen.fontname)
      font.set_absolute_size(self.pen.fontsize * Pango.SCALE)
      layout.set_font_description(font)

      # set text
      layout.set_text(text, -1)

      # cache it
      self.layout = layout
    else:
      PangoCairo.update_layout(cr, layout)

    descent = 2  # XXX get descender from font metrics

    width, height = layout.get_size()
    width = float(width) / Pango.SCALE
    height = float(height) / Pango.SCALE

    # we know the width that dot thinks this text should have
    # we do not necessarily have a font with the same metrics
    # scale it so that the text fits inside its box
    if width > self.w:
      f = self.w / width
      width = self.w  # equivalent to width *= f
      height *= f
      descent *= f
    else:
      f = 1.0

    y = self.y - height + descent

    if bounding is None or (y <= bounding[3] and bounding[1] <= y + height):
      x = self.x - 0.5 * (1 + self.j) * width
      cr.move_to(x, y)

      cr.save()
      cr.scale(f, f)
      cr.set_source_rgba(*self.select_pen(highlight).color)
      PangoCairo.show_layout(cr, layout)
      cr.restore()

  def search_text(self, regexp):
    return regexp.search(self.t) is not None

  @property
  def bounding(self):
    x, w, j = self.x, self.w, self.j
    return x - 0.5 * (1 + j) * w, -_inf, x + 0.5 * (1 - j) * w, _inf


class ImageShape(Shape):
  def __init__(self, pen, x0, y0, w, h, path):
    Shape.__init__(self)
    self.pen = pen.copy()
    self.x0 = x0
    self.y0 = y0
    self.w = w
    self.h = h
    self.path = path

  def _draw(self, cr, highlight, bounding):
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(self.path)
    sx = float(self.w) / float(pixbuf.get_width())
    sy = float(self.h) / float(pixbuf.get_height())
    cr.save()
    cr.translate(self.x0, self.y0 - self.h)
    cr.scale(sx, sy)
    Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
    cr.paint()
    cr.restore()

  @property
  def bounding(self):
    x0, y0 = self.x0, self.y0
    return x0, y0 - self.h, x0 + self.w, y0


class EllipseShape(Shape):
  def __init__(self, pen, x0, y0, w, h, filled=False):
    Shape.__init__(self)
    self.pen = pen.copy()
    self.x0 = x0
    self.y0 = y0
    self.w = w
    self.h = h
    self.filled = filled

  def _draw(self, cr, highlight, bounding):
    cr.save()
    cr.translate(self.x0, self.y0)
    cr.scale(self.w, self.h)
    cr.move_to(1.0, 0.0)
    cr.arc(0.0, 0.0, 1.0, 0, 2.0 * math.pi)
    cr.restore()
    pen = self.select_pen(highlight)
    if self.filled:
      cr.set_source_rgba(*pen.fillcolor)
      cr.fill()
    else:
      cr.set_dash(pen.dash)
      cr.set_line_width(pen.linewidth)
      cr.set_source_rgba(*pen.color)
      cr.stroke()

  @property
  def bounding(self):
    x0, y0, w, h = self.x0, self.y0, self.w, self.h
    bt = 0 if self.filled else self.pen.linewidth / 2.
    w, h = w + bt, h + bt
    return x0 - w, y0 - h, x0 + w, y0 + h


class PolygonShape(Shape):
  def __init__(self, pen, points, filled=False):
    Shape.__init__(self)
    self.pen = pen.copy()
    self.points = points
    self.filled = filled

    x0, y0, x1, y1 = Shape._bounds_from_points(self.points)
    bt = 0 if self.filled else self.pen.linewidth / 2.
    self.bounding = x0 - bt, y0 - bt, x1 + bt, y1 + bt

  def _draw(self, cr, highlight, bounding):
    x0, y0 = self.points[-1]
    cr.move_to(x0, y0)
    for x, y in self.points:
      cr.line_to(x, y)
    cr.close_path()
    pen = self.select_pen(highlight)
    if self.filled:
      cr.set_source_rgba(*pen.fillcolor)
      cr.fill_preserve()
      cr.fill()
    else:
      cr.set_dash(pen.dash)
      cr.set_line_width(pen.linewidth)
      cr.set_source_rgba(*pen.color)
      cr.stroke()


class LineShape(Shape):
  def __init__(self, pen, points):
    Shape.__init__(self)
    self.pen = pen.copy()
    self.points = points

    x0, y0, x1, y1 = Shape._bounds_from_points(self.points)
    bt = self.pen.linewidth / 2.
    self.bounding = x0 - bt, y0 - bt, x1 + bt, y1 + bt

  def _draw(self, cr, highlight, bounding):
    x0, y0 = self.points[0]
    cr.move_to(x0, y0)
    for x1, y1 in self.points[1:]:
      cr.line_to(x1, y1)
    pen = self.select_pen(highlight)
    cr.set_dash(pen.dash)
    cr.set_line_width(pen.linewidth)
    cr.set_source_rgba(*pen.color)
    cr.stroke()


class BezierShape(Shape):
  def __init__(self, pen, points, filled=False):
    Shape.__init__(self)
    self.pen = pen.copy()
    self.points = points
    self.filled = filled

    x0, y0 = self.points[0]
    xa = xb = x0
    ya = yb = y0
    for i in range(1, len(self.points), 3):
      (x1, y1), (x2, y2), (x3, y3) = self.points[i:i + 3]
      for t in self._cubic_bernstein_extrema(x0, x1, x2, x3):
        if 0 < t < 1:  # We're dealing only with Bezier curves
          v = self._cubic_bernstein(x0, x1, x2, x3, t)
          xa, xb = min(xa, v), max(xb, v)
      xa, xb = min(xa, x3), max(xb, x3)  # t=0 / t=1
      for t in self._cubic_bernstein_extrema(y0, y1, y2, y3):
        if 0 < t < 1:  # We're dealing only with Bezier curves
          v = self._cubic_bernstein(y0, y1, y2, y3, t)
          ya, yb = min(ya, v), max(yb, v)
      ya, yb = min(ya, y3), max(yb, y3)  # t=0 / t=1
      x0, y0 = x3, y3

    bt = 0 if self.filled else self.pen.linewidth / 2.
    self.bounding = xa - bt, ya - bt, xb + bt, yb + bt

  @staticmethod
  def _cubic_bernstein_extrema(p0: float, p1: float, p2: float, p3: float) -> \
      Iterable[float]:
    """
    Find extremas of a function of real domain defined by evaluating
    a cubic bernstein polynomial of given bernstein coefficients.
    """
    # compute coefficients of derivative
    a = 3. * (p3 - p0 + 3. * (p1 - p2))
    b = 6. * (p0 + p2 - 2. * p1)
    c = 3. * (p1 - p0)

    if a == 0:
      if b == 0:
        return ()  # constant
      return (-c / b,)  # linear

    # quadratic
    # compute discriminant
    d = b * b - 4. * a * c
    if d < 0:
      return ()

    k = -2. * a
    if d == 0:
      return (b / k,)

    r = math.sqrt(d)
    return ((b + r) / k, (b - r) / k)

  @staticmethod
  def _cubic_bernstein(p0, p1, p2, p3, t):
    """
    Evaluate polynomial of given bernstein coefficients
    using de Casteljau's algorithm.
    """
    u = 1 - t
    return p0 * (u ** 3) + 3 * t * u * (p1 * u + p2 * t) + p3 * (t ** 3)

  def _draw(self, cr, highlight, bounding):
    x0, y0 = self.points[0]
    cr.move_to(x0, y0)
    for i in range(1, len(self.points), 3):
      (x1, y1), (x2, y2), (x3, y3) = self.points[i:i + 3]
      cr.curve_to(x1, y1, x2, y2, x3, y3)
    pen = self.select_pen(highlight)
    if self.filled:
      cr.set_source_rgba(*pen.fillcolor)
      cr.fill_preserve()
      cr.fill()
    else:
      cr.set_dash(pen.dash)
      cr.set_line_width(pen.linewidth)
      cr.set_source_rgba(*pen.color)
      cr.stroke()


class CompoundShape(Shape):
  def __init__(self, shapes):
    Shape.__init__(self)
    self.shapes = shapes
    self.bounding = Shape._envelope_bounds(map(_get_bounding, self.shapes))

  def _draw(self, cr, highlight, bounding):
    if bounding is not None and self._fully_in(bounding):
      bounding = None
    for shape in self.shapes:
      if bounding is None or shape._intersects(bounding):
        shape._draw(cr, highlight, bounding)

  def search_text(self, regexp):
    for shape in self.shapes:
      if shape.search_text(regexp):
        return True
    return False
