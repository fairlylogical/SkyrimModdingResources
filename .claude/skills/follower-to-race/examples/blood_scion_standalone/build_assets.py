"""Assets for the standalone 'Blood Scion' race mod."""
import json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SK = r"C:\Users\fairl\.claude\skills\follower-to-race\scripts"
MODS = r"D:\SkyrimMod\wabbajack\mods"
EV = os.path.join(MODS, "Evigheden - SerketHetyt's Serana Overhaul")
MORR = os.path.join(MODS, "SC_DAI_Morrigan_SSE")
PATCH = os.path.join(MODS, "Evigheden - Morrigan Race Patch")
OUT = os.path.join(MODS, "Blood Scion")
EVM = os.path.join(EV, "Meshes", "actors", "character", "SerketHetyt's Serana Overhaul")
EVT = os.path.join(EV, "Textures", "actors", "character", "SerketHetyt's Serana Overhaul")
NEW = "actors\\character\\Blood Scion\\"          # relative to meshes\ and textures\
OLD_T = "textures\\actors\\character\\serkethetyt's serana overhaul\\"

if os.path.exists(OUT):
    sys.exit('%s already exists - remove it first' % OUT)

# ---------------------------------------------------------------- head-part meshes from FaceGen
tri = lambda n: {"tri": os.path.join(EVM, "eyes", n)}
parts = [
    ("SH_Serana_Hair", "hair\\Hair.nif", "facegen"),
    ("SH_Serana_HairHL", "hair\\HairHL.nif", "facegen"),
    ("SH_Serana_HairScalp", "hair\\Scalp.nif", "facegen"),
    ("SH_Serana_HairBraids", "hair\\HairBraids.nif", "facegen"),
    ("SH_Serana_HairBraidsHL", "hair\\HairBraidsHL.nif", "facegen"),
    ("SH_Serana_Eyes", "eyes\\Eyes.nif", tri("LDD_Eye_Inner.tri")),
    ("SH_Serana_EyesOuter", "eyes\\EyesOuter.nif", tri("LDD_Eye_Outer.tri")),
    ("SH_Serana_EyesAO", "eyes\\EyesAO.nif", tri("LDD_Eye_Shadow.tri")),
    ("SH_Serana_EyesCaruncula", "eyes\\EyesCaruncula.nif", tri("LDD_Eye_Caruncula.tri")),
    ("SH_Serana_EyesDummyR", "eyes\\EyesDummyR.nif", tri("LDD_Eye_Inner_LensR.tri")),
    ("SH_Serana_EyesDummyL", "eyes\\EyesDummyL.nif", tri("LDD_Eye_Inner_LensL.tri")),
    ("SH_Serana_EyelashesLower", "eyes\\EyelashesLower.nif", "nearest"),
    ("SH_Serana_EyelashesUpper", "eyes\\EyelashesUpper.nif", "nearest"),
    ("SH_Serana_Head", "head\\femalehead.nif", {"nif": os.path.join(EVM, "body", "femalehead.nif")}),
    ("SH_Serana_Brows", "brows\\femalebrows.nif", {"nif": os.path.join(EVM, "body", "femalebrows.nif")}),
]
cfg = {"facegen": os.path.join(EV, "Meshes", "actors", "character", "FaceGenData", "FaceGeom", "Dawnguard.esm", "00002B6C.nif"),
       "out_root": OUT,
       "delta_samples": ["SH_Serana_EyesOuter", "SH_Serana_EyesCaruncula"],
       "texture_remap": [[OLD_T, "textures\\" + NEW]],
       "parts": [dict(shape=s, out=NEW + o, neutral=n) for s, o, n in parts]}
next(p for p in cfg["parts"] if p["shape"] == "SH_Serana_Head")["diffuse"] = "textures\\" + NEW + "head\\femalehead_makeup.dds"
json.dump(cfg, open(os.path.join(HERE, 'extract.json'), 'w'), indent=1)
r = subprocess.run([sys.executable, '-I', os.path.join(SK, 'extract_headparts.py'), os.path.join(HERE, 'extract.json')])
if r.returncode:
    sys.exit('extraction failed')

def copy(src, dst_rel_under_out):
    dst = os.path.join(OUT, dst_rel_under_out)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return dst

# ---------------------------------------------------------------- lashes: one expression tri copy PER lash part
# RaceMenu keys sculpt by tri path; a shared EyesFemale.tri merged both lids' sculpt on save.
EFA_TRI = os.path.join(MODS, 'Expressive Facial Animation -Female Edition-', 'meshes', 'actors', 'character',
                       'character assets', 'EyesFemale.tri')
for n in ('EyelashesLower', 'EyelashesUpper'):
    copy(EFA_TRI, 'meshes\\' + NEW + 'eyes\\' + n + '.tri')

# ---------------------------------------------------------------- tris, body, skeleton
for n in ("LDD_Eye_Inner", "LDD_Eye_Outer", "LDD_Eye_Shadow", "LDD_Eye_Caruncula", "LDD_Eye_Inner_LensR", "LDD_Eye_Inner_LensL"):
    copy(os.path.join(EVM, "eyes", n + ".tri"), "meshes\\" + NEW + "eyes\\" + n + ".tri")
copy(os.path.join(EVM, "body", "femalehead.tri"), "meshes\\" + NEW + "head\\femalehead.tri")
copy(os.path.join(EVM, "body", "femaleheadbrows.tri"), "meshes\\" + NEW + "brows\\femaleheadbrows.tri")
for n in ("femalebody_0", "femalebody_1", "femalehands_0", "femalehands_1", "femalefeet_0", "femalefeet_1"):
    copy(os.path.join(EVM, "body", n + ".nif"), "meshes\\" + NEW + "body\\" + n + ".nif")
SKEL = os.path.join(MORR, "meshes", "SC", "0_Followers", "000_Morrigan", "Body")
for n in ("skeleton_female.nif", "skeleton_female.hkx", "skeleton_female.xml"):
    copy(os.path.join(SKEL, n), "meshes\\" + NEW + "skeleton\\" + n)

# ---------------------------------------------------------------- textures referenced by the new meshes + skin
sys.path.insert(0, SK)
from tools import setup_pynifly
setup_pynifly()
from pynifly import NifFile
wanted = set()
for dp, _, fs in os.walk(os.path.join(OUT, 'meshes')):
    for f in fs:
        if f.lower().endswith('.nif') and 'skeleton' not in f.lower() and '\\body' not in dp.lower():
            for s in NifFile(os.path.join(dp, f)).shapes:
                wanted |= {t for t in (s.textures or {}).values() if t}
for n in ("femalebody_1", "femalebody_1_msn", "femalebody_1_sk", "femalebody_1_s",
          "femalehands_1", "femalehands_1_msn", "femalehands_1_sk", "femalehands_1_s"):
    wanted.add("textures\\" + NEW + "body\\" + n + ".dds")
newt = ("textures\\" + NEW).lower()
missing = []
for t in sorted(wanted, key=str.lower):
    if not t.lower().startswith(newt):
        print('  external (kept as-is):', t); continue
    rel = t[len(newt):]
    if rel.lower() == 'head\\femalehead_makeup.dds':
        src = os.path.join(PATCH, "textures", "actors", "character", "SerketHetyt's Serana Overhaul", "MorriganPatch", "head", "femalehead_makeup.dds")
    else:
        src = os.path.join(EVT, rel)
    if not os.path.exists(src):
        missing.append(t); continue
    copy(src, t)
print('textures copied:', len(wanted) - len(missing), '| missing:', missing)
