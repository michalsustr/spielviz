import spielviz.config as cfg
import pyspiel
from gi.repository import Gtk, Pango


def player_to_str(player: int):
  if player >= 0:
    return f"PL{player}"
  elif player == pyspiel.PlayerId.INVALID:
    return "INVALID"
  elif player == pyspiel.PlayerId.TERMINAL:
    return "TERMINAL"
  elif player == pyspiel.PlayerId.CHANCE:
    return "CHANCE"
  elif player == pyspiel.PlayerId.SIMULTANEOUS:
    return "SIMULTANEOUS"
  else:
    raise AttributeError(f"Player not found: {player}")


class HistoryView:
  """
  Render information about the current pyspiel.State in a non-game-specific
  (general) way, like the current history, player(s) to move etc.
  """

  def __init__(self, container: Gtk.TextView):
    self.container = container
    self.textbuffer = Gtk.TextBuffer()
    self.textbuffer.set_text("")
    self.container.set_buffer(self.textbuffer)

    self._tag_note = self.textbuffer.create_tag(
        "n", foreground="#999999")
    self._tag_section = self.textbuffer.create_tag(
        "b", weight=Pango.Weight.BOLD)
    self._tag_player = [
      self.textbuffer.create_tag(f"p{p}", foreground=color)
      for p, color in enumerate(cfg.PLAYER_COLORS)
    ]
    self._tag_invalid = self.textbuffer.create_tag(
        "inv", foreground=cfg.INVALID_PLAYER_COLOR)
    self._tag_terminal = self.textbuffer.create_tag(
        "ter", foreground=cfg.TERMINAL_COLOR)
    self._tag_chance = self.textbuffer.create_tag(
        "chn", foreground=cfg.CHANCE_COLOR)
    self._tag_simultaneous = self.textbuffer.create_tag(
        "sim", foreground=cfg.SIMULTANEOUS_PLAYER_COLOR)

  def update(self, state: pyspiel.State):
    self._clear()
    game = state.get_game()

    self._appendln("History: ", self._tag_section)
    self._appendln(",".join(str(action) for action in state.history()))

    self._append("Current player: ", self._tag_section)
    current_player = state.current_player()
    self._appendln_pl(player_to_str(current_player), current_player)

    self._append("Rewards: ", self._tag_section)
    if not state.is_chance_node():
      for pl, reward in enumerate(state.rewards()):
        if pl > 0:
          self._append(", ")
        self._append_pl(str(reward), pl)
      self._appendln("")
    else:
      self._appendln("(not available)", self._tag_note)

    if cfg.SHOW_ACTIONS:
      self._appendln("")
      self._appendln("Actions:", self._tag_section)
      rollout = game.new_initial_state()
      for action in state.history():
        self._appendln_pl(rollout.action_to_string(action),
                          rollout.current_player())
        rollout.apply_action(action)

    if game.get_type().provides_information_state_string \
        and cfg.SHOW_INFORMATION_STATE_STRING:
      self._appendln("")
      self._appendln("Information state:", self._tag_section)
      if current_player >= 0:
        self._appendln(state.information_state_string())
      else:
        self._appendln("(not available)", self._tag_note)

    if game.get_type().provides_factored_observation_string \
        and cfg.SHOW_PUBLIC_OBSERVATION_HISTORY:
      self._appendln("")
      self._appendln("Public-Observation history:", self._tag_section)
      poh = pyspiel.PublicObservationHistory(state)
      for observation in poh.history():
        self._appendln(observation)

    if game.get_type().provides_observation_string \
        and cfg.SHOW_ACTION_OBSERVATION_HISTORY:
      for player in range(game.num_players()):
        self._appendln("")
        self._appendln(f"Action-Observation history ({player_to_str(player)}):",
                       self._tag_section, self._tag_player[player])
        aoh = pyspiel.ActionObservationHistory(player, state)
        for act_or_obs in aoh.history():
          self._appendln(str(act_or_obs))

  def _append(self, text: str, *tags):
    if tags:
      self.textbuffer.insert_with_tags(
          self.textbuffer.get_end_iter(), text, *tags)
    else:
      self.textbuffer.insert(self.textbuffer.get_end_iter(), text)

  def _appendln(self, text: str, *tags):
    self._append(text + "\n", *tags)

  def _appendln_pl(self, text: str, player: int):
    self._appendln(text, self._player_tag(player))

  def _append_pl(self, text: str, player: int):
    self._append(text, self._player_tag(player))

  def _player_tag(self, player: int):
    if player >= 0:
      return self._tag_player[player]
    elif player == pyspiel.PlayerId.INVALID:
      return self._tag_invalid
    elif player == pyspiel.PlayerId.TERMINAL:
      return self._tag_terminal
    elif player == pyspiel.PlayerId.CHANCE:
      return self._tag_chance
    elif player == pyspiel.PlayerId.SIMULTANEOUS:
      return self._tag_simultaneous
    else:
      raise AttributeError(f"Player not found: {player}")

  def _clear(self):
    self.textbuffer.set_text("")
