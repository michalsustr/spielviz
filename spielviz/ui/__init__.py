import gi

gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')

from spielviz.ui.window import DotWidget, DotWindow

__all__ = ['actions', 'animation', 'colors', 'elements', 'pen', 'window']
