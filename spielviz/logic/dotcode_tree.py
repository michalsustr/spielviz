import collections

import pygraphviz
import pyspiel

import spielviz.config as cfg
from spielviz.logic.state_history import state_from_history


class GameTreeViz(pygraphviz.AGraph):
  """Builds `pygraphviz.AGraph` of the game tree."""

  def __init__(self,
      state=None,
      lookahead=1, lookbehind=1,
      group_terminal=False, group_infosets=False, group_pubsets=False,
      target_pubset="*",
      infoset_attrs=None, pubset_attrs=None,
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

    self.add_node(self.state_to_str(state),
                  **self._node_decorator(state, highlight_node=True))

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
    assert not state.is_simultaneous_node()
    # AGraph nodes can't have empty string == None as a key, thus we prepend " "
    return " " + state.history_str()

  def _build_lookbehind(self, start_from_state, arrive_to_state):
    start_hist = start_from_state.history()
    arrive_hist = arrive_to_state.history()
    if start_hist == arrive_hist:
      return

    state_str = self.state_to_str(start_from_state)
    for action in start_from_state.legal_actions():
      child = start_from_state.child(action)
      child_str = self.state_to_str(child)

      lies_on_trajectory = arrive_hist[len(start_hist)] == action

      self.add_node(child_str, **self._node_decorator(child))
      self.add_edge(state_str, child_str, **self._edge_decorator(
          start_from_state, child, action, highlight_edge=lies_on_trajectory))

      if lies_on_trajectory:
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
      self.add_edge(state_str, child_str, **self._edge_decorator(state, action))

      if self._group_infosets and not child.is_chance_node() \
          and not child.is_terminal():
        player = child.current_player()
        info_state = child.information_state_string()
        self._infosets[(player, info_state)].append(child_str)

      if self._group_pubsets:
        pub_obs_history = str(pyspiel.PublicObservationHistory(child))
        self._pubsets[pub_obs_history].append(child_str)

      self._build_lookahead(child, depth + 1, lookahead)

  def _node_decorator(self, state, highlight_node=False):
    player = state.current_player()
    attrs = {
      "label": "",
      "fontsize": cfg.PLOT_FONTSIZE,
      "width": cfg.PLOT_WIDTH,
      "height": cfg.PLOT_HEIGHT,
      "margin": cfg.PLOT_MARGIN
    }

    if state.is_terminal():
      attrs["label"] = ", ".join(map(str, state.returns()))
      attrs["shape"] = "diamond"
      attrs["color"] = cfg.TERMINAL_COLOR
    elif state.is_chance_node():
      attrs["shape"] = "circle"
      attrs["width"] = cfg.PLOT_WIDTH / 2.
      attrs["height"] = cfg.PLOT_HEIGHT / 2.
      attrs["color"] = cfg.CHANCE_COLOR
    else:
      attrs["label"] = str(state.information_state_string())
      attrs["shape"] = cfg.PLAYER_SHAPES.get(player, "square")
      attrs["color"] = cfg.PLAYER_COLORS.get(player, "black")

    if highlight_node:
      attrs["penwidth"] = cfg.PLOT_HIGHLIGHT_PENWIDTH
    return attrs

  def _edge_decorator(self, parent, action, highlight_edge=False):
    player = parent.current_player()
    attrs = {
      "label": " " + parent.action_to_string(player, action),
      "fontsize": cfg.PLOT_FONTSIZE,
      "arrowsize": cfg.PLOT_ARROWSIZE,
    }
    attrs["color"] = cfg.PLAYER_COLORS.get(player, "black")
    if highlight_edge:
      attrs["penwidth"] = cfg.PLOT_HIGHLIGHT_PENWIDTH
    return attrs


def export_tree_dotcode(state: pyspiel.State, **kwargs) -> bytes:
  """
  Use treeviz to export the current pyspiel.State as graphviz dotcode.
  This will be subsequently rendered in PlotArea.
  """
  gametree = GameTreeViz(state, **kwargs)
  return gametree.to_string().encode()
