import os
import sys

# Ensure backend root is on sys.path and SQLAlchemy Cython is disabled
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("SQLALCHEMY_CYTHON", "0")
