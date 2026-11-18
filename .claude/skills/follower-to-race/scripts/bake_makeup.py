"""Bake an NPC's FaceGen tint (makeup) into a head diffuse texture.

usage: python bake_makeup.py --tint <FaceTint .dds> --diffuse <head diffuse .dds> --out <new .dds>
                             [--strength 1.0] [--keep-skin-tone] [--preview <png>] [--texconv <exe>]

Skyrim SE's FaceGen shader combines diffuse b and tint t as   out = b*b + 2*t*b*(1-b)   (t = 0.5 -> unchanged).
By default the tint is normalised so its dominant (median) colour - the NPC's base skin tone - maps to 0.5,
so only the makeup is baked and the player's RaceMenu skin-tone layer still controls complexion.
--keep-skin-tone bakes the NPC's complexion too (the player's skin tone then stacks on top).
"""
import argparse, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from tools import find_texconv

ap = argparse.ArgumentParser()
ap.add_argument('--tint', required=True)
ap.add_argument('--diffuse', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--strength', type=float, default=1.0, help='scale makeup intensity (0..1+)')
ap.add_argument('--keep-skin-tone', action='store_true')
ap.add_argument('--preview')
ap.add_argument('--texconv')
ap.add_argument('--format', default='BC7_UNORM')
a = ap.parse_args()
tc = find_texconv(a.texconv)


def run(args):
    r = subprocess.run([tc, '-nologo', '-y'] + args, capture_output=True, text=True)
    if r.returncode != 0 or 'FAILED' in r.stdout:
        sys.exit(r.stdout + r.stderr)


with tempfile.TemporaryDirectory() as tmp:
    for f in (a.tint, a.diffuse):
        run(['-ft', 'png', '-f', 'R8G8B8A8_UNORM', '-m', '1', '-o', tmp, os.path.normpath(f)])
    png = lambda f: os.path.join(tmp, os.path.splitext(os.path.basename(f))[0] + '.png')
    if os.path.basename(a.tint).lower() == os.path.basename(a.diffuse).lower():
        sys.exit('tint and diffuse share a file name; copy one first')
    b = np.asarray(Image.open(png(a.diffuse)).convert('RGBA')).astype(np.float32) / 255
    t = Image.open(png(a.tint)).convert('RGB').resize(b.shape[1::-1], Image.BICUBIC)
    t = np.asarray(t).astype(np.float32) / 255
    base = np.median(t.reshape(-1, 3), 0)
    tn = np.clip(0.5 * t / base, 0, 1) if not a.keep_skin_tone else t
    tn = 0.5 + (tn - 0.5) * a.strength
    rgb = b[..., :3]
    out = np.clip(rgb * rgb + 2 * tn * rgb * (1 - rgb), 0, 1)
    res = np.concatenate([out, b[..., 3:]], -1)
    stem = os.path.splitext(os.path.basename(a.out))[0]
    outpng = os.path.join(tmp, stem + '.png')
    Image.fromarray((res * 255 + 0.5).astype(np.uint8), 'RGBA').save(outpng)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    run(['-f', a.format, '-m', '0', '-o', os.path.dirname(os.path.abspath(a.out)), outpng])
    if a.preview:
        w = out.shape[1]
        side = Image.fromarray(np.concatenate([(rgb * 255).astype(np.uint8), (out * 255).astype(np.uint8)], 1))
        side.resize((1024, 512)).save(a.preview)
print('tint base colour %s | mean change %.4f, max %.3f -> %s' % (base.round(3), np.abs(out - rgb).mean(), np.abs(out - rgb).max(), a.out))
