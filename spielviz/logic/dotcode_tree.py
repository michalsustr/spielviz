# Copyright 2019 DeepMind Technologies Ltd. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Visualizing game trees with graphviz.

GameTree builds a `pygraphviz.AGraph` reprensentation of the game tree. The
resulting tree can be directly visualized in Jupyter notebooks or Google Colab
via SVG plotting - or written to a file by calling `draw(filename, prog="dot")`.

See `examples/treeviz_example.py` for a more detailed example.

This module relies on external dependencies, which need to be installed before
use. On a debian system follow these steps:
```
sudo apt-get install graphviz libgraphviz-dev
pip install pygraphviz
```
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import collections
import pyspiel
import spielviz.config as cfg
from spielviz.logic.state_history import state_from_history

# pylint: disable=g-import-not-at-top
try:
  import pygraphviz
except (ImportError, Exception) as e:
  raise ImportError(
      str(e) + "\nPlease make sure to install the following dependencies:\n"
               "sudo apt-get install graphviz libgraphviz-dev\n"
               "pip install pygraphviz")
# pylint: enable=g-import-not-at-top

_FONTSIZE = 8
_WIDTH = _HEIGHT = 0.25
_ARROWSIZE = .5
_MARGIN = 0.01


class GameTreeViz(pygraphviz.AGraph):
  """Builds `pygraphviz.AGraph` of the game tree."""

  def __init__(self,
      state=None,
      lookahead=1,
      lookbehind=1,
      group_terminal=False,
      group_infosets=False,
      group_pubsets=False,
      target_pubset="*",
      infoset_attrs=None,
      pubset_attrs=None,
      **kwargs):

    kwargs["directed"] = kwargs.get("directed", True)
    super(GameTreeViz, self).__init__(**kwargs)

    # We use pygraphviz.AGraph.add_subgraph to cluster nodes, and it requires a
    # default constructor. Thus game needs to be optional.
    if state is None:
      return

    assert lookbehind >= 0
    assert lookahead >= 0

    self._group_infosets = group_infosets
    self._group_pubsets = group_pubsets

    self._infosets = collections.defaultdict(lambda: [])
    self._pubsets = collections.defaultdict(lambda: [])
    self._terminal_nodes = []

    self.add_node(self.state_to_str(state), **self._node_decorator(state))

    if lookbehind:
      start_from = state_from_history(
          state.get_game(), state.history()[:-lookbehind])
      self.add_node(self.state_to_str(start_from),
                    **self._node_decorator(start_from))
      self._build_lookbehind(start_from, state)
    self._build_lookahead(state, 0, lookahead)

    for (player, info_state), sibblings in self._infosets.items():
      cluster_name = "cluster_{}_{}".format(player, info_state)
      self.add_subgraph(sibblings, cluster_name,
                        **(infoset_attrs or {
                          "style": "dashed"
                        }))

    for pubset, sibblings in self._pubsets.items():
      if target_pubset == "*" or target_pubset == pubset:
        cluster_name = "cluster_{}".format(pubset)
        self.add_subgraph(sibblings, cluster_name,
                          **(pubset_attrs or {
                            "style": "dashed"
                          }))

    if group_terminal:
      self.add_subgraph(self._terminal_nodes, rank="same")

  def state_to_str(self, state):
    """Unique string representation of a state.

    Args:
      state: The state.

    Returns:
      String representation of state.
    """
    assert not state.is_simultaneous_node()
    # AGraph nodes can't have empty string == None as a key, thus we prepend " "
    return " " + state.history_str()

  def _build_lookbehind(self, start_from_state, arrive_to_state):
    if start_from_state.history() == arrive_to_state.history():
      return

    state_str = self.state_to_str(start_from_state)
    for action in start_from_state.legal_actions():
      child = start_from_state.child(action)
      child_str = self.state_to_str(child)
      self.add_node(child_str, **self._node_decorator(child))
      self.add_edge(state_str, child_str,
                    **self._edge_decorator(start_from_state, child, action))

      if arrive_to_state.history()[len(start_from_state.history())] == action:
        self._build_lookbehind(child, arrive_to_state)

  def _build_lookahead(self, state, depth, lookahead):
    """Recursively builds the game tree."""
    state_str = self.state_to_str(state)

    if state.is_terminal():
      self._terminal_nodes.append(state_str)
      return
    if depth >= lookahead >= 0:
      return

    for action in state.legal_actions():
      child = state.child(action)
      child_str = self.state_to_str(child)
      self.add_node(child_str, **self._node_decorator(child))
      self.add_edge(state_str, child_str,
                    **self._edge_decorator(state, child, action))

      if self._group_infosets and not child.is_chance_node() \
          and not child.is_terminal():
        player = child.current_player()
        info_state = child.information_state_string()
        self._infosets[(player, info_state)].append(child_str)

      if self._group_pubsets:
        pub_obs_history = str(pyspiel.PublicObservationHistory(child))
        self._pubsets[pub_obs_history].append(child_str)

      self._build_lookahead(child, depth + 1, lookahead)

  
  def _node_decorator(self, state):
    """Decorates a state-node of the game tree.
  
    This method can be called by a custom decorator to prepopulate the attributes
    dictionary. Then only relevant attributes need to be changed, or added.
  
    Args:
      state: The state.
  
    Returns:
      `dict` with graphviz node style attributes.
    """
    player = state.current_player()
    attrs = {
      "label": "",
      "fontsize": _FONTSIZE,
      "width": _WIDTH,
      "height": _HEIGHT,
      "margin": _MARGIN
    }
    if state.is_terminal():
      attrs["label"] = ", ".join(map(str, state.returns()))
      attrs["shape"] = "diamond"
      attrs["color"] = cfg.TERMINAL_COLOR
    elif state.is_chance_node():
      attrs["shape"] = "circle"
      attrs["width"] = _WIDTH / 2.
      attrs["height"] = _HEIGHT / 2.
      attrs["color"] = cfg.CHANCE_COLOR
    else:
      attrs["label"] = str(state.information_state_string())
      attrs["shape"] = cfg.PLAYER_SHAPES.get(player, "square")
      attrs["color"] = cfg.PLAYER_COLORS.get(player, "black")
    return attrs
  
  
  def _edge_decorator(self, parent, unused_child, action):
    """Decorates a state-node of the game tree.
  
    This method can be called by a custom decorator to prepopulate the attributes
    dictionary. Then only relevant attributes need to be changed, or added.
  
    Args:
      parent: The parent state.
      unused_child: The child state, not used in the default decorator.
      action: `int` the selected action in the parent state.
  
    Returns:
      `dict` with graphviz node style attributes.
    """
    player = parent.current_player()
    attrs = {
      "label": " " + parent.action_to_string(player, action),
      "fontsize": _FONTSIZE,
      "arrowsize": _ARROWSIZE
    }
    attrs["color"] = cfg.PLAYER_COLORS.get(player, "black")
    return attrs


def export_tree_dotcode(state: pyspiel.State, **kwargs) -> bytes:
  """
  Use treeviz to export the current pyspiel.State as graphviz dotcode.
  This will be subsequently rendered in PlotArea.
  """
  gametree = GameTreeViz(state, **kwargs)
  return gametree.to_string().encode()
