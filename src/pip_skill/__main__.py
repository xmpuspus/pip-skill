"""Allow running as python -m pip_skill."""

import sys

from pip_skill.cli import main

if __name__ == "__main__":
    sys.exit(main())
