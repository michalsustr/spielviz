import pygraphviz
import pyspiel
import itertools
import spielviz.config as cfg
from spielviz.logic.state_history import state_from_history, state_undo_n_moves


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
        start_from = state_undo_n_moves(self.state, self.lookbehind)
        self.add_node(self.state_to_str(start_from),
                      **self._node_decorator(start_from))
        yield from self._build_lookbehind(start_from, self.state)
      yield from self._build_lookahead(self.state, 0, self.lookahead)

    self.add_node(self.state_to_str(self.state),
                  **self._node_decorator(self.state, highlight_node=True))
    yield self.state

  def state_to_str(self, state: pyspiel.State):
    # AGraph nodes can't have empty string == None as a key, thus we prepend " "
    return " " + state.history_str()

  def _children_generator(self, state: pyspiel.State):
    if state.is_player_node() or state.is_chance_node():
      for action in state.legal_actions():
        child = state.child(action)
        yield child, [action]
    elif state.is_simultaneous_node():
      player_actions = [state.legal_actions(p)
                        for p in range(state.num_players())]
      for actions in itertools.product(*player_actions):
        child = state.clone()
        child.apply_actions(actions)
        yield child, list(actions)
    elif state.is_terminal():
      return
    else:
      raise RuntimeError(f"Unhandled type of state! {str(state)}")

  def _build_full_tree(self, start_from_state, arrive_to_state):
    start_hist = start_from_state.history()
    arrive_hist = arrive_to_state.history()
    state_lies_on_trajectory = (
        len(start_hist) < len(arrive_hist)
        and arrive_hist[:len(start_hist)] == start_hist)
    state_str = self.state_to_str(start_from_state)
    len_sh = len(start_hist)

    for child, actions in self._children_generator(start_from_state):
      child_str = self.state_to_str(child)

      edge_lies_on_trajectory = (
          state_lies_on_trajectory
          and arrive_hist[len_sh:len_sh+len(actions)] == actions)

      self.add_node(child_str, **self._node_decorator(child))
      self.add_edge(state_str, child_str, **self._edge_decorator(
          start_from_state, actions, highlight_edge=edge_lies_on_trajectory))

      yield child
      yield from self._build_full_tree(child, arrive_to_state)

  def _build_lookbehind(self, start_from_state, arrive_to_state):
    start_hist = start_from_state.history()
    arrive_hist = arrive_to_state.history()
    if start_hist == arrive_hist:
      return

    state_str = self.state_to_str(start_from_state)
    len_sh = len(start_hist)
    for child, actions in self._children_generator(start_from_state):
      child_str = self.state_to_str(child)

      lies_on_trajectory = arrive_hist[len_sh:len_sh+len(actions)] == actions

      self.add_node(child_str, **self._node_decorator(child))
      self.add_edge(state_str, child_str, **self._edge_decorator(
          start_from_state, actions, highlight_edge=lies_on_trajectory))

      yield child
      if lies_on_trajectory:
        yield from self._build_lookbehind(child, arrive_to_state)

  def _build_lookahead(self, state, depth, lookahead):
    state_str = self.state_to_str(state)

    if state.is_terminal():
      return
    if depth >= lookahead >= 0:
      return

    for child, actions in self._children_generator(state):
      child_str = self.state_to_str(child)
      self.add_node(child_str, **self._node_decorator(child))
      self.add_edge(state_str, child_str, **self._edge_decorator(state, actions))
      yield child
      yield from self._build_lookahead(child, depth + 1, lookahead)

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

  def _edge_decorator(self, parent, actions, highlight_edge=False):
    player = parent.current_player()
    if len(actions) == 1:
      label = parent.action_to_string(player, actions[0])
    else:
      label = "\n ".join([parent.action_to_string(p, action)
                         for p, action in enumerate(actions)])
    if parent.is_chance_node():
      assert len(actions) == 1
      prob = [p for action, p in parent.chance_outcomes()
              if action == actions[0]]
      # todo: format as a note
      label += f"\n (p={prob[0]:.2f})"
    attrs = dict(
        label=" " + label,
        fontsize=cfg.PLOT_FONTSIZE,
        arrowsize=cfg.PLOT_ARROWSIZE,
    )
    attrs["color"] = cfg.PLAYER_COLORS.get(player, "black")
    if highlight_edge:
      attrs["penwidth"] = cfg.PLOT_HIGHLIGHT_PENWIDTH
    return attrs
