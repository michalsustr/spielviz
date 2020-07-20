import os


def get_resource_path(rel_path):
  dir_of_py_file = os.path.dirname(__file__)
  rel_path_to_resource = os.path.join(
      dir_of_py_file, "../resources", rel_path)
  abs_path_to_resource = os.path.abspath(rel_path_to_resource)
  return abs_path_to_resource
