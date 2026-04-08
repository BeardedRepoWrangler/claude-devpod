import os
import sys

# Ensure the demo root is on sys.path so `import app` works regardless
# of which directory pytest is invoked from.
sys.path.insert(0, os.path.dirname(__file__))
