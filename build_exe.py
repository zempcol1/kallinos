"""Build a stand-alone Windows executable: dist/Kallinos.exe.

    pip install pyinstaller
    python build_exe.py

The exe bundles Python, pygame and the assets folder, so it runs on any
Windows PC without installing anything. Rebuild after changing the game.
"""

import os
import struct

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")   # draw the icon without opening a window

import pygame
import PyInstaller.__main__

import settings as s
from systems.sprites import app_icon

NAME = "Kallinos"
BUILD_DIR = os.path.join(s.BASE_DIR, "build")
DIST_DIR = os.path.join(s.BASE_DIR, "dist")
ICON_SIZES = (256, 64, 48, 32, 16)


def write_icon(path: str) -> None:
    """Write a multi-size .ico whose images are PNGs of the game's app icon."""
    images = []
    for size in ICON_SIZES:
        png_path = os.path.join(BUILD_DIR, f"icon_{size}.png")
        pygame.image.save(app_icon(size), png_path)
        with open(png_path, "rb") as f:
            images.append((size, f.read()))

    header = struct.pack("<HHH", 0, 1, len(images))   # reserved, type 1 = icon, count
    offset = len(header) + 16 * len(images)
    entries, data = b"", b""
    for size, png in images:
        dim = 0 if size >= 256 else size                  # 0 means 256 in the format
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset + len(data))
        data += png
    with open(path, "wb") as f:
        f.write(header + entries + data)


def main() -> None:
    os.makedirs(BUILD_DIR, exist_ok=True)
    icon_path = os.path.join(BUILD_DIR, f"{NAME}.ico")
    write_icon(icon_path)
    PyInstaller.__main__.run([
        os.path.join(s.BASE_DIR, "main.py"),
        "--name", NAME,
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--icon", icon_path,
        "--add-data", f"{s.ASSETS_DIR}{os.pathsep}assets",
        "--distpath", DIST_DIR,
        "--workpath", os.path.join(BUILD_DIR, "pyinstaller"),
        "--specpath", BUILD_DIR,
    ])
    print(f"\nBuilt {os.path.join(DIST_DIR, NAME + '.exe')}")


if __name__ == "__main__":
    main()
