#!/usr/bin/env python3
"""Install both battle views of a Reedwake creature using a shared palette."""
import sys
from pathlib import Path

from emerald_sprites import install_pair

install_pair(*map(Path, sys.argv[1:4]))
