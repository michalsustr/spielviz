import logging

import numpy as np
import pyspiel
from gi.repository import Gtk
from open_spiel.python.observation import make_observation

from spielviz.ui.primitives.tagged_view import TaggedTextView


def _escape(x):
  """Returns a newline-free backslash-escaped version of the given string."""
  x = x.replace("\\", R"\\")
  x = x.replace("\n", R"\n")
  return x


def _format_value(v):
  """Format a single value."""
  if v == 0:
    return "◯"
  elif v == 1:
    return "◉"
  else:
    return ValueError("Values must all be 0 or 1")


def _format_vec(vec):
  return "".join(_format_value(v) for v in vec)


def _format_matrix(mat):
  return np.char.array([_format_vec(row) for row in mat])


def _format_tensor(tensor, tensor_name, max_cols=120):
  """Formats a tensor in an easy-to-view format as a list of lines."""
  if ((tensor.shape == (0,)) or (len(tensor.shape) > 3) or
      not np.logical_or(tensor == 0, tensor == 1).all()):
    vec = ", ".join(str(round(v, 5)) for v in tensor.ravel())
    return ["{} = [{}]".format(tensor_name, vec)]
  elif len(tensor.shape) == 1:
    return ["{}: {}".format(tensor_name, _format_vec(tensor))]
  elif len(tensor.shape) == 2:
    if len(tensor_name) + tensor.shape[0] + 2 < max_cols:
      lines = ["{}: {}".format(tensor_name, _format_vec(tensor[0]))]
      prefix = " " * (len(tensor_name) + 2)
    else:
      lines = ["{}:".format(tensor_name), _format_vec(tensor[0])]
      prefix = ""
    for row in tensor[1:]:
      lines.append(prefix + _format_vec(row))
    return lines
  elif len(tensor.shape) == 3:
    lines = ["{}:".format(tensor_name)]
    rows = []
    for m in tensor:
      formatted_matrix = _format_matrix(m)
      if (not rows) or (len(rows[-1][0] + formatted_matrix[0]) + 2 > max_cols):
        rows.append(formatted_matrix)
      else:
        rows[-1] = rows[-1] + "  " + formatted_matrix
    for i, big_row in enumerate(rows):
      if i > 0:
        lines.append("")
      for row in big_row:
        lines.append("".join(row))
    return lines


class ObservationsView:
  """
  Render information about the current player in pyspiel.State
  """

  def __init__(self, container: Gtk.TextView):
    self.ttv = TaggedTextView(container)

  def change_observation(self,
      game: pyspiel.Game, player: int,
      public_info: bool, perfect_recall: bool,
      private_info: pyspiel.PrivateInfoType):
    self.player = player
    observation_type = pyspiel.IIGObservationType(
        public_info, perfect_recall, private_info)
    logging.info(f"Observing PL{player} by {public_info}")
    self.observation = make_observation(game, observation_type)

  def update(self, state: pyspiel.State):
    self.ttv.clear_text()
    self.observation.set_from(state, player=self.player)

    self.ttv.appendln("Tensor:", self.ttv.TAG_SECTION)
    for name, tensor in self.observation.dict.items():
      for ln in _format_tensor(tensor, name):
        self.ttv.appendln(ln)

    self.ttv.appendln("\nString:", self.ttv.TAG_SECTION)
    obs_string = self.observation.string_from(state, player=self.player)
    if obs_string:
      self.ttv.append(obs_string)
    else:
      self.ttv.append("(empty)", self.ttv.TAG_NOTE)
