#!/usr/bin/env python3

import argparse
import sys

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')

from gi.repository import Gtk, Gdk

from spielviz.ui.window import MainWindow

usage_tips = '''
Shortcuts:
  Up, Down, Left, Right     scroll
  PageUp, +, =              zoom in
  PageDown, -               zoom out
  R                         reload dot file
  F                         find
  Q                         quit
  P                         print
  Escape                    halt animation
  Ctrl-drag                 zoom in/out
  Shift-drag                zooms an area
'''


def main():
    parser = argparse.ArgumentParser(
          description="SpielViz is an interactive viewer for OpenSpiel games",
          formatter_class=argparse.RawDescriptionHelpFormatter,
          epilog=usage_tips)
    parser.add_argument(
          'game', metavar='game', default="kuhn_poker", help='game to view')
    parser.add_argument(
          '-f', '--filter', choices=['dot', 'neato', 'twopi', 'circo', 'fdp'],
          dest='filter', default='dot', metavar='FILTER',
          help='graphviz filter: dot, neato, twopi, circo, or fdp [default: %(default)s]')
    parser.add_argument(
          '-n', '--no-filter',
          action='store_const', const=None, dest='filter',
          help='assume input is already filtered into xdot format (use e.g. dot -Txdot)')

    options = parser.parse_args()

    win = MainWindow()
    win.set_filter(options.filter)
    win.set_game(options.game)

    if sys.platform != 'win32':
        # Reset KeyboardInterrupt SIGINT handler,
        # so that glib loop can be stopped by it
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    Gtk.main()


if __name__ == '__main__':
    main()
