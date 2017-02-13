import os
import sys

# Load dependencies in lib
app_root_dir = os.path.dirname(__file__)
server_lib_dir = os.path.join(app_root_dir, 'lib')
if server_lib_dir not in sys.path:
  sys.path.insert(0, server_lib_dir)
