SpielViz
========

_SpielViz_ is an interactive viewer for [OpenSpiel](https://github.com/deepmind/open_spiel) games.

It is based on [xdot.py](https://github.com/jrfonseca/xdot.py/), a GraphViz's viewer in Python.

Screenshots
===========

[![Profile 1 Screenshot](https://raw.github.com/wiki/jrfonseca/xdot.py/xdot-profile1_small.png)](https://raw.github.com/wiki/jrfonseca/xdot.py/xdot-profile1.png)
[![Profile 2 Screenshot](https://raw.github.com/wiki/jrfonseca/xdot.py/xdot-profile2_small.png)](https://raw.github.com/wiki/jrfonseca/xdot.py/xdot-profile2.png)
[![Control Flow Graph](https://raw.github.com/wiki/jrfonseca/xdot.py/xdot-cfg_small.png)](https://raw.github.com/wiki/jrfonseca/xdot.py/xdot-cfg.png)


Features
========

TODO:

 * Configuration
 * Arrow movement withing Graph
 * Scrolling
 * State view components -- down_class python bindings
 * Public / private trees
 
 
 * Since it doesn't use bitmaps it is fast and has a small memory footprint.
 * Arbitrary zoom.
 * Keyboard/mouse navigation.
 * Supports events on the nodes with URLs.
 * Animated jumping between nodes.
 * Highlights node/edge under mouse.

Install
=======

See [INSTALL.md](INSTALL.md) for details. 

Usage
=====

Command Line
------------

If you install _SpielViz_ from PyPI or from your Linux distribution package managing system, you should have the `spielviz` somewhere in your `PATH` automatically.

When running _SpielViz_ from its source tree, you can run it by first setting `PYTHONPATH` environment variable to the full path of _SpielViz_'s source tree, then running:

    python3 -m spielviz

You can also pass the following options:

    Usage:
    	spielviz [file|-]
    
    Options:
      -h, --help            show this help message and exit
      -f FILTER, --filter=FILTER
                            graphviz filter: dot, neato, twopi, circo, or fdp
                            [default: dot]
      -n, --no-filter       assume input is already filtered into xdot format (use
                            e.g. dot -Txdot)
      -g GEOMETRY           default window size in form WxH
    
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

Versioning
==========

We use [Semantic Versioning](https://semver.org/).
