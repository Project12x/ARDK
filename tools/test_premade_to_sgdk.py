"""TDD tests for premade_to_sgdk: pre-made pixel-art strip -> SGDK indexed PNG.

Run from the ardk repo root:  python -m tools.test_premade_to_sgdk
"""
import sys
import numpy as np
from PIL import Image

from tools.premade_to_sgdk import convert_image

_run = 0
_fail = 0


def check(cond, msg):
    global _run, _fail
    _run += 1
    if not cond:
        _fail += 1
        print(f"FAIL: {msg}")


def test_basic_indexing():
    # 2x2 RGBA: (0,0)=transparent, (0,1)=red, (1,0)=green, (1,1)=red
    arr = np.array([[[0, 0, 0, 0], [200, 0, 0, 255]],
                    [[0, 200, 0, 255], [200, 0, 0, 255]]], dtype=np.uint8)
    out = convert_image(Image.fromarray(arr), max_colors=15)
    check(out.mode == "P", "output is P-mode (indexed)")
    idx = np.asarray(out)
    check(idx[0, 0] == 0, "transparent pixel -> palette index 0")
    check(idx[0, 1] != 0, "opaque red -> nonzero index")
    check(idx[1, 0] != 0, "opaque green -> nonzero index")
    check(idx[0, 1] == idx[1, 1], "same colour -> same index")
    check(idx[0, 1] != idx[1, 0], "different colours -> different index")
    check(int(idx.max()) <= 15, "all indices within 0..15")


def test_color_cap():
    # 1x20 row of 20 distinct opaque colours -> must cap to <=15 indices (+ idx0)
    cols = np.array([[[(i * 12) % 256, (i * 7) % 256, (i * 5) % 256, 255]
                      for i in range(20)]], dtype=np.uint8)
    out = convert_image(Image.fromarray(cols), max_colors=15)
    idx = np.asarray(out)
    check(int(idx.max()) <= 15, "quantised to <=15 colour indices")


def test_match_palette_extraction():
    import os
    import tempfile
    from tools.premade_to_sgdk import palette_from_indexed_png
    idx = np.array([[0, 1, 2, 1]], dtype=np.uint8)  # index 0 = transparent
    im = Image.frombytes("P", (4, 1), idx.tobytes())
    im.putpalette([255, 0, 255, 10, 20, 30, 40, 50, 60] + [0] * (768 - 9))
    p = os.path.join(tempfile.gettempdir(), "_premade_pal_test.png")
    im.save(p)
    cols = palette_from_indexed_png(p)
    check(cols == [(10, 20, 30), (40, 50, 60)],
          "match-palette extracts used colours, skipping index 0")


def main():
    test_basic_indexing()
    test_color_cap()
    test_match_palette_extraction()
    print(f"premade_to_sgdk: {_run - _fail}/{_run} checks passed")
    sys.exit(1 if _fail else 0)


if __name__ == "__main__":
    main()
