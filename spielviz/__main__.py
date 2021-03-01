#!/usr/bin/env python3

import argparse
import logging
import sys
import coloredlogs

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')

from gi.repository import Gtk, Gdk

import spielviz.config as cfg
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
  parser.add_argument('game', nargs="?", default=cfg.DEFAULT_GAME,
                      help='game to view [default: %(default)s]')
  parser.add_argument('--history', default="",
                      help='action history [default: (empty)]')
  options = parser.parse_args()

  coloredlogs.install(level=cfg.LOGGING_LEVEL)

  win = MainWindow()
  win.set_game_from_name(options.game)
  if options.history:
    win.change_history(None, options.history)

  if sys.platform != 'win32':
    # Reset KeyboardInterrupt SIGINT handler,
    # so that glib loop can be stopped by it
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

  Gtk.main()


if __name__ == '__main__':
  main()
