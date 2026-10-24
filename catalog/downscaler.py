"""Convert images to ANSI half-block colour text for terminal display."""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from urllib.request import urlopen

import numpy as np
from PIL import Image

# Default rendering parameters.
DEFAULT_COLS: int = 24
CELL_ASPECT: float = 2.1

# Pre-compiled format string for ANSI escape sequences.
_ANSI_FMT: str = "\x1b[48;2;{};{};{}m\x1b[38;2;{};{};{}m\u2584"


@lru_cache(maxsize=128)
def _read_image(source: str) -> bytes:
    """Fetch raw image bytes from a local file path or HTTP(S) URL.

    The result is cached via :func:`lru_cache` to avoid redundant I/O
    when the same image is rendered multiple times.

    Args:
        source: A file system path or an ``http://`` / ``https://`` URL.

    Returns:
        The complete raw bytes of the image file.

    Raises:
        OSError: If the file cannot be read or the URL cannot be fetched.
    """
    if source.startswith(("http://", "https://")):
        with urlopen(source, timeout=10) as response:
            return response.read()
    with open(source, "rb") as image_file:
        return image_file.read()


@lru_cache(maxsize=64)
def downscale(
    image_path: str,
    cols: int = DEFAULT_COLS,
    cell_aspect: float = CELL_ASPECT,
) -> str:
    """Render an image as ANSI half-block colour text for terminal display.

    The source image is resampled to a grid of *cols* character columns.
    Two pixel rows are combined into a single ANSI half-block character:
    the top row determines the background colour and the bottom row
    determines the foreground colour.

    The result is cached via :func:`lru_cache` keyed by all three
    arguments, so repeated calls with the same parameters return the
    same string without reprocessing.

    Args:
        image_path: Path to the image file or an HTTP(S) URL.
        cols: Number of character columns in the output. Defaults to 24.
        cell_aspect: Aspect ratio of a terminal character cell
            (width divided by height). Defaults to 2.1.

    Returns:
        A string containing ANSI escape sequences that, when printed to
        a colour-capable terminal, renders a scaled-down colour version
        of the source image using half-block characters.
    """
    text_rows: int = max(1, round(cols / cell_aspect))
    W: int = cols
    H: int = text_rows * 2
    image = Image.open(BytesIO(_read_image(image_path)))

    with image:
        image = image.convert("RGB")
        image = image.resize((W, H), Image.BICUBIC)
        arr: np.ndarray = np.asarray(image)

        rows_list: list[np.ndarray] = arr.tolist()
        lines: list[str] = []
        for ty in range(0, H, 2):
            top: list[list[int]] = rows_list[ty]
            bot: list[list[int]] = rows_list[ty + 1]
            line_parts: list[str] = [
                _ANSI_FMT.format(a[0], a[1], a[2], b[0], b[1], b[2])
                for a, b in zip(top, bot)
            ]
            lines.append("".join(line_parts))
        result = "\n".join(lines)

    return result
