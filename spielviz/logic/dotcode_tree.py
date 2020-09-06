import collections

import pygraphviz
import pyspiel

import spielviz.config as cfg
from spielviz.logic.state_history import state_from_history


class GameTreeViz(pygraphviz.AGraph):
  """Builds `pygraphviz.AGraph` of the game tree."""

  def __init__(self, state: pyspiel.State = None, lookahead: int = 1,
      lookbehind: int = 1):

    super(GameTreeViz, self).__init__(directed=True)

    assert lookbehind >= 0
    assert lookahead >= 0

    self.add_node(self.state_to_str(state),
                  **self._node_decorator(state, highlight_node=True))

    if lookbehind:
      start_from = state_from_history(
          state.get_game(), state.history()[:-lookbehind])
      self.add_node(self.state_to_str(start_from),
                    **self._node_decorator(start_from))
      self._build_lookbehind(start_from, state)
    self._build_lookahead(state, 0, lookahead)

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
          start_from_state, action, highlight_edge=lies_on_trajectory))

      if lies_on_trajectory:
        self._build_lookbehind(child, arrive_to_state)

  def _build_lookahead(self, state, depth, lookahead):
    state_str = self.state_to_str(state)

    if state.is_terminal():
      return
    if depth >= lookahead >= 0:
      return

    for action in state.legal_actions():
      child = state.child(action)
      child_str = self.state_to_str(child)
      self.add_node(child_str, **self._node_decorator(child))
      self.add_edge(state_str, child_str, **self._edge_decorator(state, action))
      self._build_lookahead(child, depth + 1, lookahead)

  def _node_decorator(self, state, highlight_node=False):
    player = state.current_player()
    attrs = dict(
        label="",
        fontsize=cfg.PLOT_FONTSIZE,
        width=cfg.PLOT_WIDTH,
        height=cfg.PLOT_HEIGHT,
        margin=cfg.PLOT_MARGIN
    )

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
    attrs = dict(
        label=" " + parent.action_to_string(player, action),
        fontsize=cfg.PLOT_FONTSIZE,
        arrowsize=cfg.PLOT_ARROWSIZE,
    )
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
