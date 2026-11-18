"""Reconnaissance: what head assets does a follower really use, and are the standalone meshes real?

usage: python inspect_follower.py --plugin <follower.esp> --mod-dir <follower mod folder> [--mod-dir ...]
                                  [--npc EDID] [--race-plugin <race.esp> --race EDID] [--data <game Data dir>]
"""
import argparse, os, struct, sys
sys.path.insert(0, os.path.dirname(__file__))
from esp_lib import Plugin, PluginSet, HDPT_TYPES, zstr_val, gid_str
from tools import setup_pynifly, LooseFiles

ap = argparse.ArgumentParser()
ap.add_argument('--plugin', required=True)
ap.add_argument('--mod-dir', action='append', default=[])
ap.add_argument('--npc')
ap.add_argument('--race-plugin')
ap.add_argument('--race')
ap.add_argument('--data', help='game Data folder (to resolve masters)')
a = ap.parse_args()

setup_pynifly()
from pynifly import NifFile
from trihandler import TriFile

mod_dirs = a.mod_dir or [os.path.dirname(os.path.abspath(a.plugin))]
loose = LooseFiles(mod_dirs)
pset = PluginSet(mod_dirs + ([os.path.dirname(os.path.abspath(a.race_plugin))] if a.race_plugin else []) + ([a.data] if a.data else []))
P = Plugin(a.plugin)
print('PLUGIN %s  masters=%s  ESL=%s' % (P.name, P.masters, bool(P.flags & 0x200)))

npcs = [(fid, r) for fid, r in P.records.items() if r[0] == 'NPC_' and any(st == 'PNAM' for st, _ in r[2])]
print('\nNPCs with head parts:')
for fid, r in npcs:
    print('  %08X %-30s origin=%s' % (fid, zstr_val(Plugin.sub(r[2], 'EDID') or b''), P.file_of(fid)))
if not npcs:
    sys.exit('no NPC_ with head parts in this plugin')
if a.npc:
    fid, rec = P.get(a.npc)
else:
    fid, rec = npcs[0]
npc_subs = rec[2]
origin, obj = P.file_of(fid), fid & 0xFFFFFF
print('\n== NPC %s  (FaceGen key: %s / %08X)' % (zstr_val(Plugin.sub(npc_subs, 'EDID')), origin, obj))
race = struct.unpack('<I', Plugin.sub(npc_subs, 'RNAM'))[0]
print('race:', gid_str(P.gid(race)), ' skin WNAM:', '%08X' % struct.unpack('<I', Plugin.sub(npc_subs, 'WNAM'))[0] if Plugin.sub(npc_subs, 'WNAM') else None)

fg_rel = 'meshes\\actors\\character\\facegendata\\facegeom\\%s\\%08x.nif' % (origin.lower(), obj)
ft_rel = 'textures\\actors\\character\\facegendata\\facetint\\%s\\%08x.dds' % (origin.lower(), obj)
fg_path, ft_path = loose.find(fg_rel), loose.find(ft_rel)
print('FaceGen mesh :', fg_path or 'NOT FOUND (%s) - maybe in a BSA; extract it first' % fg_rel)
print('FaceGen tint :', ft_path or 'NOT FOUND (%s)' % ft_rel)

fg_shapes = {}
if fg_path:
    print('\nFaceGen shapes:')
    for s in NifFile(fg_path).shapes:
        fg_shapes[s.name] = s
        tex = s.textures.get('Diffuse', '') if s.textures else ''
        print('  %-28s %-18s verts=%-6d shader=%-5s parts=%s diffuse=%s' % (
            s.name, s.blockname, len(s.verts), s.properties.shaderPropertyID != 0xFFFFFFFF,
            [p.id for p in s.partitions], tex))

def tri_count(path):
    try:
        return len(TriFile.from_file(path).vertices)
    except Exception as e:
        return 'unreadable (%s)' % e

print('\nHead parts (PNAM + HNAM extras):')
seen = set()
def show(hfid, depth):
    if hfid in seen:
        return
    seen.add(hfid)
    if not P.is_own(hfid):
        print('  ' * depth + '  %08X from master %s (not editable from this plugin; fine if vanilla)' % (hfid, P.file_of(hfid)))
        return
    t, flags, subs = P.records[hfid]
    edid = zstr_val(Plugin.sub(subs, 'EDID'))
    data = Plugin.sub(subs, 'DATA')[0]
    ptype = struct.unpack('<I', Plugin.sub(subs, 'PNAM'))[0]
    modl = zstr_val(Plugin.sub(subs, 'MODL')) if Plugin.sub(subs, 'MODL') else None
    tri = next((zstr_val(v) for st, v in subs if st == 'NAM1'), None)
    rnam = Plugin.sub(subs, 'RNAM')
    tnam = Plugin.sub(subs, 'TNAM')
    flagtxt = ','.join(n for b, n in [(1, 'Playable'), (2, 'Male'), (4, 'Female'), (8, 'Extra')] if data & b)
    print('  ' * depth + '  %08X %-28s type=%-9s DATA=%s%s' % (hfid, edid, HDPT_TYPES.get(ptype, ptype), flagtxt,
          '  [record flag Non-Playable]' if flags & 4 else ''))
    ind = '  ' * depth + '      '
    mp = loose.find(modl, 'meshes') if modl else None
    fg = fg_shapes.get(edid)
    print(ind + 'MODL %s -> %s' % (modl, mp or ('MISSING' if modl else 'none')))
    if mp:
        shapes = NifFile(mp).shapes
        desc = ', '.join('%s(%d verts)' % (s.name, len(s.verts)) for s in shapes)
        verdict = ''
        if fg is not None:
            same = len(shapes) == 1 and len(shapes[0].verts) == len(fg.verts) and shapes[0].tris == fg.tris
            verdict = '  -> matches FaceGen topology' if same else '  -> DOES NOT match FaceGen shape (placeholder/shared mesh?)'
        print(ind + 'mesh shapes: %s%s' % (desc, verdict))
        for s in shapes[:1]:
            print(ind + 'mesh diffuse: %s' % (s.textures.get('Diffuse') if s.textures else None))
    if tri:
        tp = loose.find(tri, 'meshes')
        n = tri_count(tp) if tp else None
        cmp = ''
        if isinstance(n, int) and fg is not None:
            cmp = '  (FaceGen shape has %d -> %s)' % (len(fg.verts), 'OK' if n == len(fg.verts) else 'MISMATCH')
        print(ind + 'TRI  %s -> %s%s' % (tri, ('%s verts' % n) if tp else 'not loose (vanilla BSA or missing)', cmp))
    if fg is None:
        print(ind + 'FaceGen shape named %s: NOT FOUND (check names above; they may differ from the EDID)' % edid)
    if tnam:
        print(ind + 'TNAM %s' % ('%08X' % struct.unpack('<I', tnam)[0]))
    if rnam:
        print(ind + 'RNAM valid-races list %s' % gid_str(P.gid(struct.unpack('<I', rnam)[0])))
    for st, v in subs:
        if st == 'HNAM':
            show(struct.unpack('<I', v)[0], depth + 1)

for st, v in npc_subs:
    if st == 'PNAM':
        show(struct.unpack('<I', v)[0], 0)

if a.race_plugin and a.race:
    R = Plugin(a.race_plugin)
    rfid, (t, rflags, rsubs) = R.get(a.race)
    print('\n== RACE %s (%s %08X)' % (a.race, R.name, rfid))
    data = Plugin.sub(rsubs, 'DATA')
    print('playable:', bool(struct.unpack_from('<I', data, 32)[0] & 1))
    sex, in_head = None, False
    for st, v in rsubs:
        if st == 'NAM0':
            in_head = True
        elif st in ('MNAM', 'FNAM') and in_head:
            sex = 'male' if st == 'MNAM' else 'female'
        elif st == 'HEAD':
            h = struct.unpack('<I', v)[0]
            name = R.file_of(h)
            try:
                hp = R if R.is_own(h) else pset.load(name, {'HDPT'})
                hh = hp.records[(len(hp.masters) << 24) | (h & 0xFFFFFF)]   # id as stored in its own plugin
                desc = '%s %s' % (zstr_val(Plugin.sub(hh[2], 'EDID')), HDPT_TYPES.get(struct.unpack('<I', Plugin.sub(hh[2], 'PNAM'))[0]))
            except Exception:
                desc = '(in %s)' % name
            print('  %s default head part: %s %s' % (sex, gid_str(R.gid(h)), desc))
    print('tint layers (TINI):', sum(1 for st, _ in rsubs if st == 'TINI'),
          '-> if 1, only SkinTone exists; makeup must be baked into the head diffuse')
    for st, v in rsubs:
        if st == 'TINT':
            print('  mask', zstr_val(v))
