import pyspiel
import importlib
from gi.repository import Gtk
from spielviz.ui.views.state_view import StateView

_custom_views = dict(
    # kuhn_poker=("spielviz.ui.games.kuhn_poker", "KuhnStateView"),
    chess=("spielviz.ui.games.chess", "ChessStateView"),
    dark_chess=("spielviz.ui.games.dark_chess", "DarkChessStateView")
)


def is_custom_view_registed(game: pyspiel.Game):
  return game.get_type().short_name in _custom_views


def create_custom_state_view(game: pyspiel.Game,
    container: Gtk.ScrolledWindow) -> StateView:
  game_name = game.get_type().short_name
  module_name, class_name = _custom_views[game_name]

  module = importlib.import_module(module_name)
  class_ = getattr(module, class_name)
  return class_(game, container)
