#!/usr/bin/env python3

import argparse
import sys

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')

from gi.repository import Gtk

from spielviz.ui.window import MainWindow


def main():
    parser = argparse.ArgumentParser(
          description="xdot.py is an interactive viewer for graphs written in Graphviz's dot language.",
          formatter_class=argparse.RawDescriptionHelpFormatter,
          epilog='''
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
    )
    parser.add_argument(
          'inputfile', metavar='file', nargs='?',
          help='input file to be viewed')
    parser.add_argument(
          '-f', '--filter', choices=['dot', 'neato', 'twopi', 'circo', 'fdp'],
          dest='filter', default='dot', metavar='FILTER',
          help='graphviz filter: dot, neato, twopi, circo, or fdp [default: %(default)s]')
    parser.add_argument(
          '-n', '--no-filter',
          action='store_const', const=None, dest='filter',
          help='assume input is already filtered into xdot format (use e.g. dot -Txdot)')
    parser.add_argument(
          '-g', '--geometry',
          action='store', dest='geometry',
          help='default window size in form WxH')

    options = parser.parse_args()
    inputfile = options.inputfile

    width, height = 610, 610
    if options.geometry:
        try:
            width, height = (int(i) for i in options.geometry.split('x'))
        except ValueError:
            parser.error('invalid window geometry')

    win = MainWindow(width=width, height=height)
    win.connect('delete-event', Gtk.main_quit)
    win.set_filter(options.filter)
    if inputfile and len(inputfile) >= 1:
        if inputfile == '-':
            win.set_dotcode(sys.stdin.buffer.read())
        else:
            win.open_file(inputfile)

    if sys.platform != 'win32':
        # Reset KeyboardInterrupt SIGINT handler, so that glib loop can be stopped by it
        import signal
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    Gtk.main()


if __name__ == '__main__':
    main()
