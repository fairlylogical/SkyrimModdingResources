"""Vayne Race.esp - standalone playable race cloned from vanilla DarkElfRace, with Vayne's head parts and skin
(from Velvet Darkness - SerketHetyt's Vayne Overhaul). Master: Skyrim.esm only.
FormIDs are allocated in a fixed order - never reorder (saves reference them)."""
import json, os, struct, sys
sys.path.insert(0, r"C:\Users\fairl\.claude\skills\follower-to-race\scripts")
from esp_lib import Plugin, PatchWriter, FORMID_FIELDS, HDPT_TYPES, zstr, zstr_val, u32

MODS = r"D:\SkyrimMod\wabbajack\mods"
OUT = os.path.join(MODS, "Vayne Race")
ESP = os.path.join(OUT, "Vayne Race.esp")
NEW = "actors\\character\\Vayne Race\\"
OLD = "actors\\character\\serkethetyt's vayne overhaul\\"
RACE_EDID = 'VayneRace'
VD = Plugin(os.path.join(MODS, "Velvet Darkness - SerketHetyt's Vayne Overhaul", "Velvet Darkness - SerketHetyt's Vayne Overhaul.esp"))
SKY = Plugin(r"D:\SkyrimMod\wabbajack\Stock Game\Data\Skyrim.esm", {'HDPT', 'RACE'})
W = PatchWriter(['Skyrim.esm'])


def check_refs(src, rtype, subs):
    own = {f for f in src.records if src.is_own(f)}
    known = FORMID_FIELDS.get(rtype, {})
    for st, v in subs:
        if st in known:
            continue
        for o in range(0, len(v) - 3):
            if struct.unpack_from('<I', v, o)[0] in own:
                sys.exit('%s %s: unmapped reference in %s+%d' % (src.name, rtype, st, o))


gid = lambda e: VD.gid(VD.get(e)[0])
# ---------------------------------------------------------------- allocate ids (fixed order)
race_fid = W.new_fid()
flst_fid = W.new_fid()
PARTS = ['SH_Vayne_Hair', 'SH_Vayne_HairHL', 'SH_Vayne_Scalp', 'SH_Vayne_Eyes', 'SH_Vayne_AO', 'SH_Vayne_Eyelashes',
         'SH_Vayne_Brows', 'SH_Vayne_Head', 'SH_Vayne_Ears']
hd = {}
for e in PARTS:
    hd[e] = W.new_fid(); W.redirect[gid(e)] = hd[e]
piercing_fid = W.new_fid()          # retired (nose piercing removed on request) - slot kept so later ids don't shift
mouth_fid = W.new_fid()
txst = {'head': W.new_fid(), 'body': W.new_fid(), 'hands': W.new_fid()}
W.redirect[gid('SH_Vayne_Body_tex')] = txst['body']
W.redirect[gid('SH_Vayne_Hands_tex')] = txst['hands']
arma = {e: W.new_fid() for e in ('SH_Vayne_BodyAA', 'SH_Vayne_HandsAA', 'SH_Vayne_FeetAA')}
for e, f in arma.items():
    W.redirect[gid(e)] = f
armo_fid = W.new_fid(); W.redirect[gid('SH_Vayne_Body')] = armo_fid
for e in ('SH_Vayne_Eyes_tex', 'SH_Vayne_AO_tex', 'SH_Vayne_Eyelashes_tex', 'SH_Vayne_Brows_tex',
          'SH_Vayne_Head_tex', 'SH_Vayne_Ears_tex'):
    W.redirect[gid(e)] = 0          # TNAMs dropped (meshes carry the textures); head gets our makeup TXST

cc = lambda e: 'VR_' + e.replace('SH_Vayne_', '')

# ---------------------------------------------------------------- valid-races list
W.add('FLST', 0, flst_fid, [('EDID', zstr('VR_HeadPartsVayneRace')), ('LNAM', u32(race_fid))])

# ---------------------------------------------------------------- texture sets
def relocate_txst(src_edid, key, edid, diffuse=None):
    fid, (t, fl, subs) = VD.get(src_edid)
    out = []
    for st, v in subs:
        if st == 'EDID':
            v = zstr(edid)
        elif st.startswith('TX'):
            p = zstr_val(v)
            if p.lower().startswith(OLD):
                p = NEW + p[len(OLD):]
            if st == 'TX00' and diffuse:
                p = diffuse
            assert 'vayne overhaul' not in p.lower(), p
            v = zstr(p)
        out.append((st, v))
    W.add('TXST', fl, txst[key], out)

relocate_txst('SH_Vayne_Head_tex', 'head', 'VR_Head_tex', NEW + "Body\\femalehead_makeup.dds")
relocate_txst('SH_Vayne_Body_tex', 'body', 'VR_Body_tex')
relocate_txst('SH_Vayne_Hands_tex', 'hands', 'VR_Hands_tex')

# ---------------------------------------------------------------- head parts
MODEL = {'SH_Vayne_Hair': 'hair\\Hair.nif', 'SH_Vayne_HairHL': 'hair\\HairHL.nif', 'SH_Vayne_Scalp': 'hair\\Scalp.nif',
         'SH_Vayne_Eyes': 'eyes\\Eyes.nif', 'SH_Vayne_AO': 'eyes\\EyesAO.nif', 'SH_Vayne_Eyelashes': 'eyes\\Eyelashes.nif',
         'SH_Vayne_Brows': 'brows\\femalebrows.nif', 'SH_Vayne_Head': 'head\\femalehead.nif', 'SH_Vayne_Ears': 'head\\ears.nif'}
TRI = {'SH_Vayne_Eyes': 'eyes\\Eyes.tri', 'SH_Vayne_AO': 'eyes\\EyesAO.tri', 'SH_Vayne_Eyelashes': 'eyes\\Eyelashes.tri',
       'SH_Vayne_Brows': 'brows\\femaleheadbrows.tri', 'SH_Vayne_Head': 'head\\femalehead.tri', 'SH_Vayne_Ears': 'head\\ears.tri'}
MAIN = {'SH_Vayne_Hair', 'SH_Vayne_Eyes', 'SH_Vayne_Brows', 'SH_Vayne_Head'}
DISPLAY = {'SH_Vayne_Hair': 'Vayne Hair', 'SH_Vayne_Eyes': 'Vayne Eyes', 'SH_Vayne_Brows': 'Vayne Brows',
           'SH_Vayne_Head': 'Vayne Head'}     # FULL names so the parts are identifiable in RaceMenu lists
for e in PARTS:
    fid, (t, flags, subs) = VD.get(e)
    check_refs(VD, 'HDPT', subs)
    out = []
    for (st, v), (_, rv) in zip(subs, W.remap_subs(VD, 'HDPT', subs)):
        if st == 'EDID':
            rv = zstr(cc(e))
        elif st == 'MODL':
            rv = zstr(NEW + MODEL[e])
        elif st == 'NAM1':
            rv = zstr(NEW + TRI[e]) if e in TRI else None
        elif st == 'RNAM':
            rv = u32(flst_fid)
        elif st == 'DATA' and e in MAIN:
            rv = bytes([v[0] | 1])
        out.append([st, rv])
    if e not in TRI:                                    # scalp tri was never shipped
        out = [x for x in out if x[0] not in ('NAM0', 'NAM1')]
    out = [x for x in out if not (x[0] in ('TNAM', 'FULL'))]
    if e in DISPLAY:
        out.insert(1, ['FULL', zstr(DISPLAY[e])])
    if e == 'SH_Vayne_Head':                            # face: Vayne's head textures + baked makeup
        i = next(k for k, x in enumerate(out) if x[0] == 'RNAM')
        out.insert(i, ['TNAM', u32(txst['head'])])
    for x in out:
        assert x[1] is not None, (e, x)
        assert b'vayne overhaul' not in x[1].lower(), (e, x)
    W.add('HDPT', flags & ~0x4 if e in MAIN else flags, hd[e], out)

# mouth: copy of the vanilla female mouth, valid for our race
mfid, (t, mflags, msubs) = SKY.get('FemaleMouthHumanoidDefault')
mo = [[st, v] for st, v in W.remap_subs(SKY, 'HDPT', msubs) if st != 'FULL']   # FULL there is a localized string id
for x in mo:
    if x[0] == 'EDID': x[1] = zstr('VR_Mouth')
    if x[0] == 'RNAM': x[1] = u32(flst_fid)
W.add('HDPT', mflags, mouth_fid, mo)

# ---------------------------------------------------------------- skin (ARMA/ARMO)
for e, f in arma.items():
    fid, (t, fl, subs) = VD.get(e)
    check_refs(VD, 'ARMA', subs)
    out = []
    for (st, v), (_, rv) in zip(subs, W.remap_subs(VD, 'ARMA', subs)):
        if st == 'EDID':
            rv = zstr(cc(e))
        elif st in ('MOD2', 'MOD3', 'MOD4', 'MOD5'):
            p = zstr_val(v)
            if p.lower().startswith(OLD):
                rv = zstr(NEW + p[len(OLD):])
        out.append([st, rv])
    # Additional races: KEEP DarkElfRace / DarkElfRaceVampire and add ours. Our race's Armor Race (RNAM) is DarkElfRace,
    # so the engine matches skin addons against DarkElfRace - with only our race listed, the naked body was invisible
    # and armor skin shapes fell back to vanilla textures (no skin TXST found).
    last = max(k for k, x in enumerate(out) if x[0] == 'MODL' and len(x[1]) == 4)
    out.insert(last + 1, ['MODL', u32(race_fid)])
    for x in out:
        assert b'vayne overhaul' not in x[1].lower(), (e, x)
    W.add('ARMA', fl, f, out)

fid, (t, fl, subs) = VD.get('SH_Vayne_Body')
check_refs(VD, 'ARMO', subs)
out = [[st, v] for st, v in W.remap_subs(VD, 'ARMO', subs)]
for x in out:
    if x[0] == 'EDID': x[1] = zstr('VR_Skin')
W.add('ARMO', fl, armo_fid, out)

# ---------------------------------------------------------------- race (clone of DarkElfRace)
rfid, (t, rflags, rsubs) = SKY.get('DarkElfRace')
race = [[st, v] for st, v in W.remap_subs(SKY, 'RACE', rsubs)]
dark_elf = W.remap(SKY, rfid)
hdpt_type = {fid: struct.unpack('<I', Plugin.sub(r[2], 'PNAM'))[0] for fid, r in SKY.records.items() if r[0] == 'HDPT'}
ours_by_type = {1: hd['SH_Vayne_Head'], 2: hd['SH_Vayne_Eyes'], 3: hd['SH_Vayne_Hair'], 0: mouth_fid}

for x in race:
    if x[0] == 'EDID': x[1] = zstr(RACE_EDID)
    if x[0] == 'FULL': x[1] = zstr('Vayne')
    if x[0] == 'DESC': x[1] = zstr("Dunmer of the shadows - white-haired, violet-eyed and lethal. "
                                   "Dark Elf abilities and gameplay, Vayne's look.")
    if x[0] == 'WNAM': x[1] = u32(armo_fid)

sex, in_head, female_head_idx, last_head = None, False, [], None
for k, x in enumerate(race):
    st, v = x
    if st == 'NAM0': in_head = True
    if in_head and st in ('MNAM', 'FNAM'): sex = st
    if in_head and sex == 'FNAM':
        if st == 'INDX': female_head_idx.append(struct.unpack('<I', v)[0])
        if st == 'HEAD':
            vanilla = struct.unpack('<I', v)[0]
            typ = hdpt_type[vanilla & 0xFFFFFF]
            if typ in ours_by_type:
                x[1] = u32(ours_by_type.pop(typ))
            last_head = k
        if st == 'FTSF': x[1] = None
        if st == 'DFTF': x[1] = u32(txst['head'])
assert not ours_by_type, ours_by_type
n = max(female_head_idx)
race[last_head + 1:last_head + 1] = [['INDX', u32(n + 1)], ['HEAD', u32(hd['SH_Vayne_Brows'])]]
# female face texture choices: just ours (placed where the first FTSF was)
i = next(k for k, x in enumerate(race) if x[0] == 'FTSF' and x[1] is None)
race[i][1] = u32(txst['head'])
race = [x for x in race if x[1] is not None]
# Drop the racial presets (RPRM/RPRF = vanilla Dark Elf preset NPCs). Chargen applies a preset NPC's head parts to the
# player, so new characters got vanilla Dark Elf eyes/hair and RaceMenu showed Dark Elf lists without Vayne's parts.
# Blood Scion (cloned from a race with no presets) never had the problem.
race = [x for x in race if x[0] not in ('RPRM', 'RPRF')]
data = bytearray(Plugin.sub(race, 'DATA'))
struct.pack_into('<I', data, 32, struct.unpack_from('<I', data, 32)[0] | 0x1)   # playable
for x in race:
    if x[0] == 'DATA': x[1] = bytes(data)
assert not any(x[0] in ('RNAM', 'NAM8') for x in race)
# Armor race = Dark Elf. NO morph race (NAM8): with NAM8 set, chargen uses the morph race's head parts/defaults
# (that's how vampire races borrow them), so our own hair/eyes vanished from RaceMenu's lists.
race += [['RNAM', u32(dark_elf)]]
W.add('RACE', rflags & ~0x40000, race_fid, [tuple(x) for x in race])

n = W.write(ESP, esl=True, author="Vayne Race (personal)",
            description="Playable Dark Elf-based race with Vayne's look (Velvet Darkness assets). Personal use only.")
print('wrote', ESP, n, 'records+groups; masters', W.masters)

# ---------------------------------------------------------------- Race Compatibility SKSE
rcs = os.path.join(OUT, 'SKSE', 'Plugins', 'RCS', 'VayneRace.json')
os.makedirs(os.path.dirname(rcs), exist_ok=True)
form = 'Vayne Race.esp|0x%X' % (race_fid & 0xFFFFFF)
json.dump({"RCS": [{"name": "Vayne",
                    "race": {"form": form, "proxies": ["DarkElfRace"], "armor": {"race": "DarkElfRace"}},
                    "vampireRace": {"form": form, "proxies": ["DarkElfRaceVampire"], "armor": {"race": "DarkElfRaceVampire"}},
                    "headPart": "DarkElf"}]}, open(rcs, 'w'), indent=4)
print('wrote', rcs)
