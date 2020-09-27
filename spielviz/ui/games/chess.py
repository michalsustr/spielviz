import chess
import chess.svg
import pyspiel
from gi.repository import GdkPixbuf

from spielviz.ui.views.state_view import ImageStateView


class ChessStateView(ImageStateView):
  def update(self, state: pyspiel.chess.ChessState):
    fen = str(state)
    board = chess.Board(fen)
    svg = chess.svg.board(board)

    loader = GdkPixbuf.PixbufLoader()
    loader.write(svg.encode())
    loader.close()
    pixbuf = loader.get_pixbuf()
    self.image.set_from_pixbuf(pixbuf)
