import pygraphviz
import pyspiel

import spielviz.config as cfg
from spielviz.logic.state_history import state_from_history


class GameTreeViz(pygraphviz.AGraph):
  """Builds `pygraphviz.AGraph` of the game tree."""

  def __init__(self, state: pyspiel.State = None,
      full_tree: bool = False,
      lookahead: int = 1,
      lookbehind: int = 1):

    super(GameTreeViz, self).__init__(directed=True)
    assert lookbehind >= 0
    assert lookahead >= 0
    self.state = state
    self.game = state.get_game()
    self.full_tree = full_tree
    self.lookahead = lookahead
    self.lookbehind = lookbehind

  def build_tree(self):
    if self.full_tree:
      yield from self._build_full_tree(self.game.new_initial_state(),
                                       self.state)
    else:
      if self.lookbehind:
        start_from = state_from_history(self.game,
                                        self.state.history()[:-self.lookbehind])
        self.add_node(self.state_to_str(start_from),
                      **self._node_decorator(start_from))
        yield from self._build_lookbehind(start_from, self.state)
      yield from self._build_lookahead(self.state, 0, self.lookahead)

    self.add_node(self.state_to_str(self.state),
                  **self._node_decorator(self.state, highlight_node=True))
    yield self.state

  def state_to_str(self, state):
    assert not state.is_simultaneous_node()
    # AGraph nodes can't have empty string == None as a key, thus we prepend " "
    return " " + state.history_str()

  def _build_full_tree(self, start_from_state, arrive_to_state):
    start_hist = start_from_state.history()
    arrive_hist = arrive_to_state.history()
    state_lies_on_trajectory = (
        len(start_hist) < len(arrive_hist)
        and arrive_hist[:len(start_hist)] == start_hist)
    state_str = self.state_to_str(start_from_state)

    for action in start_from_state.legal_actions():
      child = start_from_state.child(action)
      child_str = self.state_to_str(child)

      edge_lies_on_trajectory = (
          state_lies_on_trajectory and arrive_hist[len(start_hist)] == action)

      self.add_node(child_str, **self._node_decorator(child))
      self.add_edge(state_str, child_str, **self._edge_decorator(
          start_from_state, action, highlight_edge=edge_lies_on_trajectory))

      yield child
      yield from self._build_full_tree(child, arrive_to_state)

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

      yield child
      if lies_on_trajectory:
        yield from self._build_lookbehind(child, arrive_to_state)

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
      yield child
      for node in self._build_lookahead(child, depth + 1, lookahead):
        yield child

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
      attrs["shape"] = cfg.PLAYER_SHAPES[pyspiel.PlayerId.TERMINAL]
      attrs["color"] = cfg.PLAYER_COLORS[pyspiel.PlayerId.TERMINAL]
    elif state.is_chance_node():
      attrs["width"] = cfg.PLOT_WIDTH / 2.
      attrs["height"] = cfg.PLOT_HEIGHT / 2.
      attrs["shape"] = cfg.PLAYER_SHAPES[pyspiel.PlayerId.CHANCE]
      attrs["color"] = cfg.PLAYER_COLORS[pyspiel.PlayerId.CHANCE]
    else:
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
