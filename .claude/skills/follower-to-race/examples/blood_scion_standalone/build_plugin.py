"""Blood Scion.esp - standalone race: Morrigan race body/skeleton, Requiem Breton gameplay,
Serana (Evigheden) head parts and skin. Masters: Skyrim.esm, Requiem.esp."""
import json, os, struct, sys
sys.path.insert(0, r"C:\Users\fairl\.claude\skills\follower-to-race\scripts")
from esp_lib import Plugin, PluginSet, PatchWriter, FORMID_FIELDS, zstr, zstr_val, u32

MODS = r"D:\SkyrimMod\wabbajack\mods"
OUT = os.path.join(MODS, "Blood Scion")
ESP = os.path.join(OUT, "Blood Scion.esp")
NEW = "actors\\character\\Blood Scion\\"
ps = PluginSet([os.path.join(MODS, "Evigheden - SerketHetyt's Serana Overhaul"), os.path.join(MODS, "SC_DAI_Morrigan_SSE"),
                os.path.join(MODS, "Requiem - The Roleplaying Overhaul"), r"D:\SkyrimMod\wabbajack\Stock Game\Data"])
EV = ps.load("Evigheden - SerketHetyt's Serana Overhaul.esp")
MO = ps.load("SC_DAI_Morrigan.esp")
RQ = ps.load("Requiem.esp", {'RACE'})
SKY = ps.load("Skyrim.esm", {'HDPT'})
W = PatchWriter(['Skyrim.esm', 'Requiem.esp'])
RACE_EDID = 'BloodScionRace'

def check_refs(src, rtype, subs):
    """Every reference to the source plugin's own records must sit in a known FormID field (else it would be lost)."""
    own = {f for f in src.records if src.is_own(f)}
    known = FORMID_FIELDS.get(rtype, {})
    for st, v in subs:
        if st in known:
            continue
        for o in range(0, len(v) - 3):
            if struct.unpack_from('<I', v, o)[0] in own:
                sys.exit('%s %s: unmapped reference in %s+%d' % (src.name, rtype, st, o))

# ---------------------------------------------------------------- allocate ids
race_fid = W.new_fid(); W.redirect[MO.gid(MO.get('SC_DAI_Morrigan_Race')[0])] = race_fid
flst_fid = W.new_fid()
EV_PARTS = ['SH_Serana_Hair', 'SH_Serana_HairHL', 'SH_Serana_HairScalp', 'SH_Serana_HairBraids', 'SH_Serana_HairBraidsHL',
            'SH_Serana_Eyes', 'SH_Serana_EyesOuter', 'SH_Serana_EyesCaruncula', 'SH_Serana_EyesDummyR', 'SH_Serana_EyesDummyL',
            'SH_Serana_EyesAO', 'SH_Serana_EyelashesLower', 'SH_Serana_EyelashesUpper', 'SH_Serana_Head', 'SH_Serana_Brows']
hd = {}
for e in EV_PARTS:
    hd[e] = W.new_fid(); W.redirect[EV.gid(EV.get(e)[0])] = hd[e]
mouth_fid = W.new_fid()
txst = {k: W.new_fid() for k in ('body', 'hands')}
# Morrigan skin texture sets -> our Serana copies; Morrigan ARMAs/ARMO -> ours; Morrigan head parts -> ours by type
W.redirect[MO.gid(MO.get('SC_DAI_Morrigan_Body_TS')[0])] = txst['body']
W.redirect[MO.gid(MO.get('SC_DAI_Morrigan_Hands_TS')[0])] = txst['hands']
arma = {e: W.new_fid() for e in ('SC_DAI_Morrigan_Torso_AA', 'SC_DAI_Morrigan_Hands_AA', 'SC_DAI_Morrigan_Feet_AA')}
for e, f in arma.items():
    W.redirect[MO.gid(MO.get(e)[0])] = f
armo_fid = W.new_fid(); W.redirect[MO.gid(MO.get('SC_DAI_Morrigan_Body')[0])] = armo_fid
W.redirect[MO.gid(MO.get('SC_DAI_Morrigan_Head')[0])] = hd['SH_Serana_Head']
W.redirect[MO.gid(MO.get('SC_DAI_Morrigan_Eyes')[0])] = hd['SH_Serana_Eyes']
W.redirect[MO.gid(MO.get('SC_DAI_Morrigan_Hair')[0])] = hd['SH_Serana_Hair']
W.redirect[MO.gid(MO.get('SC_DAI_Morrigan_Racial')[0])] = 0   # replaced by Requiem Breton abilities below
for e in ('SH_Serana_Eyes_tex', 'SH_Serana_Brows_tex'):          # eye/brow TNAMs are dropped below
    W.redirect[EV.gid(EV.get(e)[0])] = 0

def cc(edid):
    return 'BS_' + edid.replace('SH_Serana_', '').replace('SC_DAI_Morrigan_', '')

# ---------------------------------------------------------------- valid-races list
W.add('FLST', 0, flst_fid, [('EDID', zstr('BS_HeadPartsBloodScion')), ('LNAM', u32(race_fid))])

# ---------------------------------------------------------------- head parts (copies of Evigheden's, relocated)
MODEL = {'SH_Serana_Hair': 'hair\\Hair.nif', 'SH_Serana_HairHL': 'hair\\HairHL.nif', 'SH_Serana_HairScalp': 'hair\\Scalp.nif',
         'SH_Serana_HairBraids': 'hair\\HairBraids.nif', 'SH_Serana_HairBraidsHL': 'hair\\HairBraidsHL.nif',
         'SH_Serana_Eyes': 'eyes\\Eyes.nif', 'SH_Serana_EyesOuter': 'eyes\\EyesOuter.nif', 'SH_Serana_EyesCaruncula': 'eyes\\EyesCaruncula.nif',
         'SH_Serana_EyesDummyR': 'eyes\\EyesDummyR.nif', 'SH_Serana_EyesDummyL': 'eyes\\EyesDummyL.nif', 'SH_Serana_EyesAO': 'eyes\\EyesAO.nif',
         'SH_Serana_EyelashesLower': 'eyes\\EyelashesLower.nif', 'SH_Serana_EyelashesUpper': 'eyes\\EyelashesUpper.nif',
         'SH_Serana_Head': 'head\\femalehead.nif', 'SH_Serana_Brows': 'brows\\femalebrows.nif'}
TRIDIR = {'eyes\\': 'eyes\\', 'body\\femalehead.tri': 'head\\femalehead.tri', 'body\\femaleheadbrows.tri': 'brows\\femaleheadbrows.tri'}
MAIN = {'SH_Serana_Hair', 'SH_Serana_Eyes', 'SH_Serana_Head', 'SH_Serana_Brows'}
OLD = "actors\\character\\serkethetyt's serana overhaul\\"
for e in EV_PARTS:
    fid, (t, flags, subs) = EV.get(e)
    check_refs(EV, 'HDPT', subs)
    out = []
    for (st, v), (_, rv) in zip(subs, W.remap_subs(EV, 'HDPT', subs)):
        if st == 'EDID':
            rv = zstr(cc(e))
        elif st == 'MODL':
            rv = zstr(NEW + MODEL[e])
        elif st == 'NAM1':
            p = zstr_val(v)
            if p.lower().startswith(OLD):
                rel = p[len(OLD):]
                for a, b in TRIDIR.items():
                    if rel.lower().startswith(a):
                        rel = b + rel[len(a):]
                rv = zstr(NEW + rel)
        elif st == 'RNAM':
            rv = u32(flst_fid)
        elif st == 'DATA' and e in MAIN:
            rv = bytes([v[0] | 1])
        out.append([st, rv])
    if e == 'SH_Serana_HairScalp':        # Scalp.tri was never shipped
        out = [x for x in out if x[0] not in ('NAM0', 'NAM1')]
    if e in ('SH_Serana_Eyes', 'SH_Serana_Brows'):   # meshes now carry the correct textures
        out = [x for x in out if x[0] != 'TNAM']
    if e in ('SH_Serana_EyelashesLower', 'SH_Serana_EyelashesUpper'):
        # Each lash part gets its OWN copy of the expression tri. RaceMenu saves sculpt keyed by tri path: with both
        # parts on the shared EyesFemale.tri, saving collapsed their imported sculpt into one entry and reloading
        # applied the same offsets to both lids.
        name = 'EyelashesLower' if e.endswith('Lower') else 'EyelashesUpper'
        for x in out:
            if x[0] == 'NAM1': x[1] = zstr(NEW + 'eyes\\' + name + '.tri')
    for _, v in out:
        assert b'SerketHetyt' not in v and b'serkethetyt' not in v, (e, v)
    W.add('HDPT', flags & ~0x4 if e in MAIN else flags, hd[e], out)

# mouth: copy of the vanilla female mouth, valid for our race (Serana's head has no mouth interior of its own)
mfid, (t, mflags, msubs) = SKY.get('FemaleMouthHumanoidDefault')
mo = [[st, v] for st, v in W.remap_subs(SKY, 'HDPT', msubs)]
for x in mo:
    if x[0] == 'EDID': x[1] = zstr('BS_Mouth')
    if x[0] == 'RNAM': x[1] = u32(flst_fid)
W.add('HDPT', mflags, mouth_fid, mo)

# ---------------------------------------------------------------- skin
for k, e in (('body', 'SH_Serana_Body_tex'), ('hands', 'SH_Serana_Hands_tex')):
    fid, (t, fl, subs) = EV.get(e)
    out = []
    for st, v in subs:
        if st == 'EDID':
            v = zstr('BS_%s_tex' % k.capitalize())
        elif st.startswith('TX'):
            p = zstr_val(v)
            assert p.lower().startswith(OLD), p
            v = zstr(NEW + p[len(OLD):])
        out.append((st, v))
    W.add('TXST', fl, txst[k], out)

MORR_BODY = "sc\\0_followers\\000_morrigan\\body\\"
for e, f in arma.items():
    fid, (t, fl, subs) = MO.get(e)
    check_refs(MO, 'ARMA', subs)
    out = []
    for (st, v), (_, rv) in zip(subs, W.remap_subs(MO, 'ARMA', subs)):
        if st == 'EDID':
            rv = zstr(cc(e))
        elif st in ('MOD3', 'MOD5'):
            p = zstr_val(v)
            if p.lower().startswith(MORR_BODY):
                rv = zstr(NEW + 'body\\' + p[len(MORR_BODY):])
        out.append([st, rv])
    W.add('ARMA', fl, f, out)

fid, (t, fl, subs) = MO.get('SC_DAI_Morrigan_Body')
check_refs(MO, 'ARMO', subs)
out = [[st, v] for st, v in W.remap_subs(MO, 'ARMO', subs)]
for x in out:
    if x[0] == 'EDID': x[1] = zstr('BS_Skin')
    if x[0] == 'FULL': x[1] = zstr("Blood Scion Skin")
W.add('ARMO', fl, armo_fid, out)

# ---------------------------------------------------------------- race
rfid, (t, rflags, rsubs) = MO.get('SC_DAI_Morrigan_Race')
check_refs(MO, 'RACE', rsubs)
race = [[st, v] for st, v in W.remap_subs(MO, 'RACE', rsubs)]
bfid = (RQ.masters.index('Skyrim.esm') << 24) | 0x13741
req = [[st, v] for st, v in W.remap_subs(RQ, 'RACE', RQ.records[bfid][2])]
rq = lambda t: [x for x in req if x[0] == t]

def replace_run(types, new):
    """Replace all subrecords of `types` with `new`, placed where the first of them was."""
    global race
    i = next(k for k, x in enumerate(race) if x[0] in types)
    race = race[:i] + [x for x in race[i:] if x[0] not in types]
    race[i:i] = [list(x) for x in new]

for x in race:
    if x[0] == 'EDID': x[1] = zstr(RACE_EDID)
    if x[0] == 'FULL': x[1] = zstr("Blood Scion")
    if x[0] == 'DESC': x[1] = zstr("Heirs to an old Breton bloodline touched by vampiric nobility, Blood Scions carry the arcane "
                                   "resilience of their mortal forebears and the pale, ageless beauty of the night.")
    if x[0] == 'ANAM' and b'000_Morrigan' in x[1]:
        x[1] = zstr(NEW + 'skeleton\\skeleton_female.nif')
replace_run({'SPCT', 'SPLO'}, rq('SPCT') + rq('SPLO'))
replace_run({'KSIZ', 'KWDA'}, rq('KSIZ') + rq('KWDA'))
replace_run({'ATKD', 'ATKE'}, [x for x in req if x[0] in ('ATKD', 'ATKE')])
replace_run({'VNAM'}, rq('VNAM'))
replace_run({'QNAM'}, rq('QNAM'))
d = bytearray(next(x[1] for x in race if x[0] == 'DATA'))
rd = rq('DATA')[0][1]
for a, b in ((0, 16), (36, 52), (84, 104), (124, 128)):   # skills, H/M/S + carry weight, regen + unarmed, flags2
    d[a:b] = rd[a:b]
for x in race:
    if x[0] == 'DATA': x[1] = bytes(d)

# female default head parts: Face/Eyes/Hair already redirected; add Brows + Mouth after the female HEAD list
sex, in_head, last_head, idx = None, False, None, []
for k, (st, v) in enumerate(race):
    if st == 'NAM0': in_head = True
    if in_head and st in ('MNAM', 'FNAM'): sex = st
    if in_head and sex == 'FNAM' and st == 'INDX': idx.append(struct.unpack('<I', v)[0])
    if in_head and sex == 'FNAM' and st == 'HEAD': last_head = k
n = max(idx)
race[last_head + 1:last_head + 1] = [['INDX', u32(n + 1)], ['HEAD', u32(hd['SH_Serana_Brows'])],
                                     ['INDX', u32(n + 2)], ['HEAD', u32(mouth_fid)]]
assert not any(x[0] == 'SPLO' and struct.unpack('<I', x[1])[0] == 0 for x in race)
W.add('RACE', rflags, race_fid, [tuple(x) for x in race])

n = W.write(ESP, esl=True, author="Blood Scion",
            description="Standalone playable race: Requiem Breton abilities, Serana's look (Evigheden assets), SC_DAI Morrigan body/skeleton.")
print('wrote', ESP, n, 'records+groups; masters', W.masters)

# ---------------------------------------------------------------- Race Compatibility SKSE
rcs = os.path.join(OUT, 'SKSE', 'Plugins', 'RCS', 'BloodScion.json')
os.makedirs(os.path.dirname(rcs), exist_ok=True)
variants = [{"slots": [30, 31, 42], "proxy": "DefaultRace"}]
json.dump({"RCS": [{"name": "BloodScion",
                    "race": {"form": RACE_EDID, "proxies": ["BretonRace"], "armor": {"race": "BretonRace", "variants": variants}},
                    "vampireRace": {"form": RACE_EDID, "proxies": ["BretonRaceVampire"],
                                    "armor": {"race": "BretonRaceVampire", "variants": variants}},
                    "headPart": "Human"}]}, open(rcs, 'w'), indent=4)
print('wrote', rcs)
