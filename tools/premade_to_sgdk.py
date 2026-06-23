"""Convert pre-made pixel-art sprite strips into SGDK/rescomp-ready indexed PNGs.

The unified ardk pipeline (tools.pipeline.cli) is built for AI-generated sheets:
it flood-fills a background and AI-detects sprites, which mangles clean, tight,
pre-made pixel art (it extracts nothing). This focused tool skips all detection:
it takes art that is *already* a tight transparent-background strip and just
indexes it to a Genesis-legal palette in epoch's proven format:

    P-mode PNG, <=16 palette entries, **index 0 = transparent** (rescomp convention),
    referenced from resources.res via  SPRITE name "path.png" <tilesW> <tilesH> NONE 0

Shared-palette mode quantises a *set* of sprites to one palette so they fit the
Genesis 4-CRAM-line budget (e.g. all enemy variants -> one enemy palette).

CLI (run from the ardk repo root):
    python -m tools.premade_to_sgdk in.png -o out/ --frame 2x2
    python -m tools.premade_to_sgdk a.png b.png c.png -o out/ --shared --frame 4x4
"""
import os

import numpy as np
from PIL import Image

# rescomp treats palette index 0 as transparent regardless of its colour; magenta
# makes accidental index-0 pixels obvious in previews.
TRANSPARENT_RGB = (255, 0, 255)


def _flat_palette(colors):
    """768-entry flat RGB palette: index 0 = transparent, then `colors`, padded."""
    flat = list(TRANSPARENT_RGB)
    for (r, g, b) in colors:
        flat += [int(r), int(g), int(b)]
    flat += [0] * (768 - len(flat))
    return flat[:768]


def _quantize_colors(rgb_pixels, max_colors):
    """Up to `max_colors` representative RGB tuples for the given opaque pixels."""
    uniq = np.unique(rgb_pixels.reshape(-1, 3), axis=0)
    if len(uniq) <= max_colors:
        return [tuple(int(c) for c in row) for row in uniq]
    # Too many colours: median-cut the opaque pixels (laid out as a 1px-wide strip).
    strip = Image.fromarray(rgb_pixels.reshape(-1, 1, 3).astype(np.uint8), "RGB")
    pal_img = strip.quantize(colors=max_colors, method=Image.MEDIANCUT)
    pal = pal_img.getpalette()[: max_colors * 3]
    return [tuple(pal[i:i + 3]) for i in range(0, len(pal), 3)]


def build_shared_palette(images, max_colors=15):
    """Collect opaque colours across a set of RGBA images -> one shared palette."""
    chunks = []
    for img in images:
        rgba = np.asarray(img.convert("RGBA"))
        opaque = rgba[:, :, 3] >= 128
        chunks.append(rgba[:, :, :3][opaque])
    chunks = [c for c in chunks if len(c)]
    if not chunks:
        return []
    return _quantize_colors(np.concatenate(chunks, axis=0), max_colors)


def convert_image(img, max_colors=15, palette=None):
    """Pre-made RGBA pixel art -> P-mode indexed Image (palette index 0 = transparent).

    `palette` (list of RGB tuples) forces a shared palette; otherwise one is derived
    from this image's own opaque colours. Opaque pixels map to the nearest palette
    entry (indices 1..N); transparent pixels (alpha < 128) map to index 0.
    """
    rgba = np.asarray(img.convert("RGBA"))
    h, w = rgba.shape[:2]
    rgb = rgba[:, :, :3]
    opaque = rgba[:, :, 3] >= 128

    if palette is None:
        opaque_px = rgb[opaque]
        palette = _quantize_colors(opaque_px, max_colors) if len(opaque_px) else []

    out = np.zeros((h, w), dtype=np.uint8)  # default 0 == transparent
    if palette:
        pal = np.array(palette, dtype=np.int16)            # K,3
        px = rgb[opaque].astype(np.int16)                  # N,3
        dist = ((px[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)  # N,K
        out[opaque] = (dist.argmin(axis=1) + 1).astype(np.uint8)      # 1..K

    pimg = Image.frombytes("P", (w, h), out.tobytes())
    pimg.putpalette(_flat_palette(palette))
    return pimg


def convert_file(src, dst, max_colors=15, palette=None):
    out = convert_image(Image.open(src), max_colors=max_colors, palette=palette)
    out.save(dst)
    return out


def res_lines(sprite_name, png_rel, frame_tiles_w, frame_tiles_h, palette_name):
    return (f'SPRITE {sprite_name} "{png_rel}" {frame_tiles_w} {frame_tiles_h} NONE 0\n'
            f'PALETTE {palette_name} "{png_rel}"')


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(
        description="Pre-made pixel art -> SGDK indexed PNG (rescomp-ready).")
    ap.add_argument("inputs", nargs="+", help="Input PNG sprite strip(s)")
    ap.add_argument("-o", "--outdir", required=True, help="Output directory")
    ap.add_argument("--max-colors", type=int, default=15, help="Max colours (<=15)")
    ap.add_argument("--shared", action="store_true",
                    help="Quantise all inputs to ONE shared palette (4-CRAM budget)")
    ap.add_argument("--frame", default="2x2",
                    help="Frame size in TILES WxH for the .res SPRITE def "
                         "(2x2=16x16, 4x4=32x32)")
    args = ap.parse_args(argv)

    os.makedirs(args.outdir, exist_ok=True)
    fw, fh = (int(x) for x in args.frame.lower().split("x"))
    pal = build_shared_palette([Image.open(p) for p in args.inputs],
                               args.max_colors) if args.shared else None
    if pal is not None:
        print(f"shared palette: {len(pal)} colours")

    res = []
    for src in args.inputs:
        name = os.path.splitext(os.path.basename(src))[0].replace(" ", "_").lower()
        dst = os.path.join(args.outdir, name + ".png")
        out = convert_file(src, dst, args.max_colors, palette=pal)
        used = int(np.asarray(out).max())
        print(f"  {name}: {out.size}  indices 0..{used}  -> {dst}")
        res.append(res_lines(f"spr_{name}", f"sprites/{name}.png", fw, fh, f"pal_{name}"))

    res_path = os.path.join(args.outdir, "generated.res")
    with open(res_path, "w") as f:
        f.write("\n".join(res) + "\n")
    print(f"Wrote {len(args.inputs)} sprite(s) + {res_path}")


if __name__ == "__main__":
    main()
