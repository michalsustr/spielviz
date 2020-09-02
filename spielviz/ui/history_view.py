import spielviz.config as cfg
from spielviz.ui.primitives.tagged_view import TaggedTextView
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
    self.ttv = TaggedTextView(container)

  def update(self, state: pyspiel.State):
    self.ttv.clear_text()
    game = state.get_game()

    self.ttv.appendln("History: ", self.ttv.TAG_SECTION)
    self.ttv.appendln(",".join(str(action) for action in state.history()))

    self.ttv.append("Current player: ", self.ttv.TAG_SECTION)
    current_player = state.current_player()
    self.ttv.appendln_pl(player_to_str(current_player), current_player)

    self.ttv.append("Rewards: ", self.ttv.TAG_SECTION)
    if not state.is_chance_node():
      self.ttv.append_player_list(state.rewards())
      self.ttv.appendln("")
    else:
      self.ttv.appendln("(not available)", self.ttv.TAG_NOTE)

    if cfg.SHOW_ACTIONS:
      self.ttv.appendln("")
      self.ttv.appendln("Actions:", self.ttv.TAG_SECTION)
      rollout = game.new_initial_state()
      for action in state.history():
        self.ttv.appendln_pl(rollout.action_to_string(action),
                             rollout.current_player())
        rollout.apply_action(action)

    if game.get_type().provides_information_state_string \
        and cfg.SHOW_INFORMATION_STATE_STRING:
      self.ttv.appendln("")
      self.ttv.appendln("Information state:", self.ttv.TAG_SECTION)
      if current_player >= 0:
        self.ttv.appendln(state.information_state_string())
      else:
        self.ttv.appendln("(not available)", self.ttv.TAG_NOTE)

    if game.get_type().provides_factored_observation_string \
        and cfg.SHOW_PUBLIC_OBSERVATION_HISTORY:
      self.ttv.appendln("")
      self.ttv.appendln("Public-Observation history:", self.ttv.TAG_SECTION)
      poh = pyspiel.PublicObservationHistory(state)
      for observation in poh.history():
        self.ttv.appendln(observation)

    if game.get_type().provides_observation_string \
        and cfg.SHOW_ACTION_OBSERVATION_HISTORY:
      for player in range(game.num_players()):
        self.ttv.appendln("")
        self.ttv.appendln(f"Action-Observation history ({player_to_str(player)}):",
                          self.ttv.TAG_SECTION, self.ttv.TAG_PLAYER[player])
        aoh = pyspiel.ActionObservationHistory(player, state)
        for act_or_obs in aoh.history():
          self.ttv.appendln(str(act_or_obs))
