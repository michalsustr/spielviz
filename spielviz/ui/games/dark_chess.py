import logging
import xml.etree.ElementTree as ET
from typing import List

import chess
import numpy as np
import pyspiel
from gi.repository import GdkPixbuf
from gi.repository import Gtk
from open_spiel.python.observation import make_observation

import spielviz.third_party.chess_svg as chess_svg
import spielviz.ui.views.state_view as state_view

# Specific styles that should be applied for highlighting public/hidden squares.

PUBLIC_SQUARE_SVG = """<g id="public"><path d="M2 2 L2 42 L42 42 L42 2 Z"
stroke="#abdbe3" stroke-width="4" fill-opacity="0.0" /></g>"""
HIDDEN_SQUARE_SVG = """<g id="hidden"><path d="M0 0 L0 45 L45 45 L45 0 Z"
fill="#000" fill-opacity="0.60" /></g>"""


def svg_dark_board(public_squares: List[chess.Square] = [],
    hidden_squares: List[chess.Square] = [],
    orientation: chess.Color = chess.WHITE,
    flipped: bool = False,
    coordinates: bool = True,
    **kwargs) -> ET.Element:
  svg = chess_svg.board(**kwargs)
  defs = ET.SubElement(svg, "defs")
  defs.append(ET.fromstring(PUBLIC_SQUARE_SVG))
  defs.append(ET.fromstring(HIDDEN_SQUARE_SVG))

  public_set = chess.SquareSet(public_squares)
  hidden_set = chess.SquareSet(hidden_squares)

  orientation ^= flipped
  margin = 15 if coordinates else 0

  for square, bb in enumerate(chess.BB_SQUARES):
    file_index = chess.square_file(square)
    rank_index = chess.square_rank(square)
    x = (
          file_index if orientation else 7 - file_index) * \
        chess_svg.SQUARE_SIZE + margin
    y = (
          7 - rank_index if orientation else rank_index) * \
        chess_svg.SQUARE_SIZE + margin

    if square in public_set:
      ET.SubElement(svg, "use", chess_svg._attrs({
        "xlink:href": "#public", "x": x, "y": y, }))
    if square in hidden_set:
      ET.SubElement(svg, "use", chess_svg._attrs({
        "xlink:href": "#hidden", "x": x, "y": y, }))

  return svg


def svg_to_string(svg_tree: ET.Element) -> str:
  return chess_svg.SvgWrapper(ET.tostring(svg_tree).decode("utf-8"))


class TwoImagesStateView(state_view.StateView):
  def __init__(self, game: pyspiel.Game, container: Gtk.Frame):
    state_view.StateView.__init__(self, game, container)
    self.game = game
    self.box = Gtk.HBox()
    self.images = []
    for i in range(2):
      self.images.append(Gtk.Image())
      self.images[i].set_halign(Gtk.Align.START)
      self.box.add(self.images[i])

    self._add_single_child(self.box)
    container.show_all()


class DarkChessStateView(TwoImagesStateView):
  def update(self, state: pyspiel.State):
    try:
      fen = str(state)
      board = chess.Board(fen)
      obs_type = pyspiel.IIGObservationType(
          public_info=True, perfect_recall=False,
          private_info=pyspiel.PrivateInfoType.SINGLE_PLAYER)
      observation = make_observation(state.get_game(), obs_type)

      for player in range(2):
        observation.set_from(state, player)
        self.write_image(board, observation, player)
    except RuntimeError as e:
      # Might throw if we use a different board size than 8.
      # Ignore the rendering then.
      logging.warning(e)

  def write_image(self, board, observation, player):
    # Merge all public observations
    public_obs = observation.dict["public_empty_pieces"]  # np.array
    for key, obs in observation.dict.items():
      if key.startswith("public_"):
        public_obs = np.max((public_obs, obs), axis=0)
    public_squares = np.where(public_obs.T.flatten())[0].tolist()

    unknown_obs = [v for k, v in observation.dict.items()
                   if k.endswith("unknown_squares")][0]
    hidden_obs = unknown_obs - public_obs
    hidden_squares = np.where(hidden_obs.T.flatten())[0].tolist()

    svg = svg_to_string(svg_dark_board(
        public_squares=public_squares,
        hidden_squares=hidden_squares,
        board=board, size=250))
    loader = GdkPixbuf.PixbufLoader()
    loader.write(svg.encode())
    loader.close()
    pixbuf = loader.get_pixbuf()
    self.images[player].set_from_pixbuf(pixbuf)
