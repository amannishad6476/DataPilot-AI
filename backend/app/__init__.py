import os

# Ensure pure-Python execution mode for SQLAlchemy under strict Windows AppLocker/WDAC policies
os.environ.setdefault("SQLALCHEMY_CYTHON", "0")
