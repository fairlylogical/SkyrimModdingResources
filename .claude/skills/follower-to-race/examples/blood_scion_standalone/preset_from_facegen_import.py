"""Preset v3: what RaceMenu's import of 00002B6C.nif produces, but with each lash part under its own tri key.
Sculpt = FaceGen shape verts - Blood Scion mesh verts (same local frame), per part; head/brows/mouth keep the user's import."""
import json, os, sys
import numpy as np
sys.path.insert(0, r"C:\Users\fairl\.claude\skills\follower-to-race\scripts")
from tools import setup_pynifly
setup_pynifly()
from pynifly import NifFile
M = r"D:\SkyrimMod\wabbajack\mods"
BS = os.path.join(M, 'Blood Scion', 'meshes', 'actors', 'character', 'Blood Scion', 'eyes')
FG = os.path.join(M, "Evigheden - SerketHetyt's Serana Overhaul", "Meshes", "actors", "character", "FaceGenData", "FaceGeom", "Dawnguard.esm", "00002B6C.nif")
PRE = r"D:\SkyrimMod\wabbajack\overwrite\SKSE\Plugins\CharGen\Presets"
SRC = os.path.join(PRE, 'serana_evgheny_standalone.jslot')
DST = os.path.join(PRE, 'serana_evgheny_standalone_lashfix.jslot')
H = "actors\\character\\Blood Scion\\eyes\\"

d = json.load(open(SRC, encoding='utf-8')); div = d['morphs']['sculptDivisor']
fg = {s.name: s for s in NifFile(FG).shapes}
parts = [('Eyes.nif', 'SH_Serana_Eyes', 'LDD_Eye_Inner.tri'), ('EyesOuter.nif', 'SH_Serana_EyesOuter', 'LDD_Eye_Outer.tri'),
         ('EyesAO.nif', 'SH_Serana_EyesAO', 'LDD_Eye_Shadow.tri'), ('EyesCaruncula.nif', 'SH_Serana_EyesCaruncula', 'LDD_Eye_Caruncula.tri'),
         ('EyesDummyR.nif', 'SH_Serana_EyesDummyR', 'LDD_Eye_Inner_LensR.tri'), ('EyesDummyL.nif', 'SH_Serana_EyesDummyL', 'LDD_Eye_Inner_LensL.tri'),
         ('EyelashesLower.nif', 'SH_Serana_EyelashesLower', 'EyelashesLower.tri'), ('EyelashesUpper.nif', 'SH_Serana_EyelashesUpper', 'EyelashesUpper.tri')]
new = {}
for nif, fgname, tri in parts:
    s = NifFile(os.path.join(BS, nif)).shapes[0]; f = fg[fgname]
    assert np.allclose(s.transform.translation[:], f.transform.translation[:], atol=1e-3), nif   # same local frame
    off = np.array(f.verts) - np.array(s.verts)
    q = np.rint(off * div).astype(int)
    new[(H + tri).lower()] = {'host': H + tri, 'data': [[int(i), int(a), int(b), int(c)] for i, (a, b, c) in enumerate(q) if a or b or c]}
    print('%-20s -> %-24s offset mean %s max %.2f' % (nif, tri, off.mean(0).round(3), np.abs(off).max()))
drop = {'actors\\character\\character assets\\eyesfemale.tri', (H + 'eyelashes.tri').lower()}
kept = [e for e in d['morphs']['sculpt'] if e['host'].lower() not in new and e['host'].lower() not in drop]
d['morphs']['sculpt'] = kept + list(new.values())
json.dump(d, open(DST, 'w', encoding='utf-8'), indent=4)
print('kept from your import:', [e['host'].split('\\')[-1] for e in kept])
print('hosts now unique:', len({e['host'].lower() for e in d['morphs']['sculpt']}) == len(d['morphs']['sculpt']))
print('wrote', DST)
