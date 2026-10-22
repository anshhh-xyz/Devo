"""Executable entrypoint for python -m devo."""
import sys
from devo.cli import main

if __name__ == "__main__":
    sys.exit(main())
