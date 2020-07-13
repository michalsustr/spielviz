import operator

import cairo

from spielviz.graphics.shape import Shape, CompoundShape

_inf = float('inf')
_get_bounding = operator.attrgetter('bounding')


class Url(object):
    def __init__(self, item, url, highlight=None):
        self.item = item
        self.url = url
        if highlight is None:
            highlight = set([item])
        self.highlight = highlight


class Jump(object):
    def __init__(self, item, x, y, highlight=None):
        self.item = item
        self.x = x
        self.y = y
        if highlight is None:
            highlight = set([item])
        self.highlight = highlight


class Element(CompoundShape):
    """Base class for graph nodes and edges."""

    def __init__(self, shapes):
        CompoundShape.__init__(self, shapes)

    def is_inside(self, x, y):
        return False

    def get_url(self, x, y):
        return None

    def get_jump(self, x, y):
        return None


class Node(Element):
    def __init__(self, id, x, y, w, h, shapes, url):
        Element.__init__(self, shapes)

        self.id = id
        self.x = x
        self.y = y

        self.x1 = x - 0.5 * w
        self.y1 = y - 0.5 * h
        self.x2 = x + 0.5 * w
        self.y2 = y + 0.5 * h

        self.url = url

    def is_inside(self, x, y):
        return self.x1 <= x and x <= self.x2 and self.y1 <= y and y <= self.y2

    def get_url(self, x, y):
        if self.url is None:
            return None
        if self.is_inside(x, y):
            return Url(self, self.url)
        return None

    def get_jump(self, x, y):
        if self.is_inside(x, y):
            return Jump(self, self.x, self.y)
        return None

    def __repr__(self):
        return "<Node %s>" % self.id


def square_distance(x1, y1, x2, y2):
    deltax = x2 - x1
    deltay = y2 - y1
    return deltax * deltax + deltay * deltay


class Edge(Element):
    def __init__(self, src, dst, points, shapes):
        Element.__init__(self, shapes)
        self.src = src
        self.dst = dst
        self.points = points

    RADIUS = 10

    def is_inside_begin(self, x, y):
        return square_distance(x, y,
                               *self.points[0]) <= self.RADIUS * self.RADIUS

    def is_inside_end(self, x, y):
        return square_distance(x, y,
                               *self.points[-1]) <= self.RADIUS * self.RADIUS

    def is_inside(self, x, y):
        if self.is_inside_begin(x, y):
            return True
        if self.is_inside_end(x, y):
            return True
        return False

    def get_jump(self, x, y):
        if self.is_inside_begin(x, y):
            return Jump(self, self.dst.x, self.dst.y,
                        highlight=set([self, self.dst]))
        if self.is_inside_end(x, y):
            return Jump(self, self.src.x, self.src.y,
                        highlight=set([self, self.src]))
        return None

    def __repr__(self):
        return "<Edge %s -> %s>" % (self.src, self.dst)


class Graph(Shape):
    def __init__(self, width=1, height=1, shapes=(), nodes=(), edges=(),
          outputorder='breadthfirst'):
        Shape.__init__(self)

        self.width = width
        self.height = height
        self.shapes = shapes
        self.nodes = nodes
        self.edges = edges
        self.outputorder = outputorder

        self.bounding = Shape._envelope_bounds(
              map(_get_bounding, self.shapes),
              map(_get_bounding, self.nodes),
              map(_get_bounding, self.edges))

    def get_size(self):
        return self.width, self.height

    def _draw_shapes(self, cr, bounding):
        for shape in self.shapes:
            if bounding is None or shape._intersects(bounding):
                shape._draw(cr, highlight=False, bounding=bounding)

    def _draw_nodes(self, cr, bounding, highlight_items):
        for node in self.nodes:
            if bounding is None or node._intersects(bounding):
                node._draw(cr, highlight=(node in highlight_items),
                           bounding=bounding)

    def _draw_edges(self, cr, bounding, highlight_items):
        for edge in self.edges:
            if bounding is None or edge._intersects(bounding):
                should_highlight = any(e in highlight_items
                                       for e in (edge, edge.src, edge.dst))
                edge._draw(cr, highlight=should_highlight, bounding=bounding)

    def draw(self, cr, highlight_items=None, bounding=None):
        if bounding is not None:
            if not self._intersects(bounding):
                return
            if self._fully_in(bounding):
                bounding = None

        if highlight_items is None:
            highlight_items = ()
        cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)

        cr.set_line_cap(cairo.LINE_CAP_BUTT)
        cr.set_line_join(cairo.LINE_JOIN_MITER)

        self._draw_shapes(cr, bounding)
        if self.outputorder == 'edgesfirst':
            self._draw_edges(cr, bounding, highlight_items)
            self._draw_nodes(cr, bounding, highlight_items)
        else:
            self._draw_nodes(cr, bounding, highlight_items)
            self._draw_edges(cr, bounding, highlight_items)

    def get_element(self, x, y):
        for node in self.nodes:
            if node.is_inside(x, y):
                return node
        for edge in self.edges:
            if edge.is_inside(x, y):
                return edge

    def get_url(self, x, y):
        for node in self.nodes:
            url = node.get_url(x, y)
            if url is not None:
                return url
        return None

    def get_jump(self, x, y):
        for edge in self.edges:
            jump = edge.get_jump(x, y)
            if jump is not None:
                return jump
        for node in self.nodes:
            jump = node.get_jump(x, y)
            if jump is not None:
                return jump
        return None
