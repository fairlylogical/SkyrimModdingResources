"""Assets for the standalone 'Vayne Race' (Dark Elf based) - personal use only (author forbids redistribution).
Source: Velvet Darkness - SerketHetyt's Vayne Overhaul. Re-runnable: wipes and rebuilds meshes/ and textures/."""
import json, os, shutil, struct, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SK = r"C:\Users\fairl\.claude\skills\follower-to-race\scripts"
MODS = r"D:\SkyrimMod\wabbajack\mods"
VD = os.path.join(MODS, "Velvet Darkness - SerketHetyt's Vayne Overhaul")
OUT = os.path.join(MODS, "Vayne Race")
VM = os.path.join(VD, "meshes", "actors", "character", "SerketHetyt's Vayne Overhaul")
VT = os.path.join(VD, "textures", "actors", "character", "SerketHetyt's Vayne Overhaul")
NEW = "actors\\character\\Vayne Race\\"
OLD_T = "textures\\actors\\character\\serkethetyt's vayne overhaul\\"
EFA_TRI = os.path.join(MODS, "Expressive Facial Animation -Female Edition-", "meshes", "actors", "character",
                       "character assets", "EyesFemale.tri")
CVEO = os.path.join(MODS, "Complete Vanilla Eye Overhaul (CVEO) by LDD", "Meshes", "Actors", "Character", "Character Assets")
PY = [sys.executable, '-I']

for d in ('meshes', 'textures'):
    shutil.rmtree(os.path.join(OUT, d), ignore_errors=True)


def copy(src, rel):
    dst = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return dst


# ---------------------------------------------------------------- textures: copy Vayne's whole texture folder
shutil.copytree(VT, os.path.join(OUT, "textures", NEW))

# ---------------------------------------------------------------- makeup baked into the head diffuse
makeup = os.path.join(OUT, "textures", NEW, "Body", "femalehead_makeup.dds")
r = subprocess.run(PY + [os.path.join(SK, 'bake_makeup.py'),
                         '--tint', os.path.join(VD, "textures", "actors", "character", "FaceGenData", "FaceTint", "CSV_Vayne.esp", "00000807.dds"),
                         '--diffuse', os.path.join(VT, "Body", "femalehead.dds"),
                         '--out', makeup, '--preview', os.path.join(HERE, 'makeup_preview.png')])
if r.returncode:
    sys.exit('makeup bake failed')

# ---------------------------------------------------------------- head-part meshes from FaceGen
tri = lambda p: {"tri": p}
parts = [
    ("SH_Vayne_Hair", "hair\\Hair.nif", "facegen"),
    ("SH_Vayne_HairHL", "hair\\HairHL.nif", "facegen"),
    ("SH_Vayne_Scalp", "hair\\Scalp.nif", "facegen"),
    ("SH_Vayne_Eyes", "eyes\\Eyes.nif", {"nif": os.path.join(CVEO, "LDDEyes", "Female", "LDD_FemaleEyes.nif")}),
    ("SH_Vayne_AO", "eyes\\EyesAO.nif", "nearest"),
    ("SH_Vayne_Eyelashes", "eyes\\Eyelashes.nif", {"nif": os.path.join(CVEO, "LDDLashes", "A", "LDD_FemaleLashes.nif")}),
    ("SH_Vayne_Head", "head\\femalehead.nif", {"nif": os.path.join(VM, "Head", "FemaleHead.nif")}),
    ("SH_Vayne_Ears", "head\\ears.nif", tri(os.path.join(VM, "Head", "ElvenEars.tri"))),
    ("SH_Vayne_Brows", "brows\\femalebrows.nif", tri(os.path.join(VM, "Head", "femaleheadbrows.tri"))),
]
cfg = {"facegen": os.path.join(VD, "meshes", "actors", "character", "FaceGenData", "FaceGeom", "CSV_Vayne.esp", "00000807.nif"),
       "out_root": OUT,
       "delta_samples": ["SH_Vayne_Eyes", "SH_Vayne_Eyelashes"],
       "texture_remap": [[OLD_T, "textures\\" + NEW]],
       "parts": [dict(shape=s, out=NEW + o, neutral=n) for s, o, n in parts]}
next(p for p in cfg["parts"] if p["shape"] == "SH_Vayne_Head")["diffuse"] = "textures\\" + NEW + "Body\\femalehead_makeup.dds"
json.dump(cfg, open(os.path.join(HERE, 'extract.json'), 'w'), indent=1)
r = subprocess.run(PY + [os.path.join(SK, 'extract_headparts.py'), os.path.join(HERE, 'extract.json')])
if r.returncode:
    sys.exit('extraction failed')

# ---------------------------------------------------------------- tris (one file per part: RaceMenu keys sculpt by tri path)
copy(os.path.join(VM, "Head", "femalehead.tri"), "meshes\\" + NEW + "head\\femalehead.tri")
copy(os.path.join(VM, "Head", "ElvenEars.tri"), "meshes\\" + NEW + "head\\ears.tri")
copy(os.path.join(VM, "Head", "femaleheadbrows.tri"), "meshes\\" + NEW + "brows\\femaleheadbrows.tri")
for n in ("Eyes", "EyesAO", "Eyelashes"):
    copy(EFA_TRI, "meshes\\" + NEW + "eyes\\" + n + ".tri")


# ---------------------------------------------------------------- body meshes (retexture Vayne-prefixed paths)
def retexture_prefix(src, dst, old, new):
    """Rewrite texture-path prefixes in every BSShaderTextureSet (layout parsing as in retexture_nif.py)."""
    d = open(src, 'rb').read()
    p = d.index(b'\n') + 1 + 9
    nb, = struct.unpack_from('<I', d, p); p += 8
    for _ in range(3):
        p += 1 + d[p]
    nt, = struct.unpack_from('<H', d, p); p += 2
    types = []
    for _ in range(nt):
        l, = struct.unpack_from('<I', d, p); types.append(d[p + 4:p + 4 + l].decode()); p += 4 + l
    bt = list(struct.unpack_from('<%dH' % nb, d, p)); p += 2 * nb
    bs_off = p; bs = list(struct.unpack_from('<%dI' % nb, d, p)); p += 4 * nb
    ns, _ = struct.unpack_from('<II', d, p); p += 8
    for _ in range(ns):
        l, = struct.unpack_from('<I', d, p); p += 4 + l
    ng, = struct.unpack_from('<I', d, p); p += 4 + 4 * ng
    data0 = p
    blocks, off = [], data0
    for i in range(nb):
        blocks.append(d[off:off + bs[i]]); off += bs[i]
    footer = d[off:]
    n_changed = 0
    for i in range(nb):
        if types[bt[i]] != 'BSShaderTextureSet':
            continue
        b = blocks[i]
        n, = struct.unpack_from('<I', b, 0); q = 4; paths = []
        for _ in range(n):
            l, = struct.unpack_from('<I', b, q); paths.append(b[q + 4:q + 4 + l].decode('latin1')); q += 4 + l
        newp = [new + x[len(old):] if x.lower().startswith(old) else x for x in paths]
        if newp != paths:
            n_changed += 1
        blocks[i] = struct.pack('<I', len(newp)) + b''.join(struct.pack('<I', len(x)) + x.encode('latin1') for x in newp) + b[q:]
        bs[i] = len(blocks[i])
    out = bytearray(d[:bs_off]) + struct.pack('<%dI' % nb, *bs) + d[bs_off + 4 * nb:data0] + b''.join(blocks) + footer
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(bytes(out))
    return n_changed


for n in ("femalebody_0", "femalebody_1", "femalehands_0", "femalehands_1", "femalefeet_0", "femalefeet_1"):
    c = retexture_prefix(os.path.join(VM, "Body", n + ".nif"), os.path.join(OUT, "meshes", NEW, "body", n + ".nif"),
                         OLD_T, "textures\\" + NEW)
    print('body %s: %d texture set(s) relocated' % (n, c))

# ---------------------------------------------------------------- verify: every texture in our meshes resolves
sys.path.insert(0, SK)
from tools import setup_pynifly
setup_pynifly()
from pynifly import NifFile
bad = []
for dp, _, fs in os.walk(os.path.join(OUT, 'meshes')):
    for f in fs:
        if f.lower().endswith('.nif'):
            for s in NifFile(os.path.join(dp, f)).shapes:
                for t in (s.textures or {}).values():
                    if t and 'vayne' in t.lower():
                        if not t.lower().startswith(("textures\\" + NEW).lower()):
                            bad.append((f, t, 'not relocated'))
                        elif not os.path.exists(os.path.join(OUT, t)):
                            bad.append((f, t, 'missing'))
print('texture check:', bad or 'OK')
