"""Build the ESL-flagged patch plugin that gives a race a follower's head parts.

usage: python build_patch.py <config.json>

config:
{
  "search_dirs": ["<follower mod folder>", "<race mod folder>", "<game Data folder>"],   # where plugins are found
  "output": "<patch mod folder>\\<Name>.esp",
  "esl": true,
  "description": "...",
  "follower_plugin": "Follower.esp",

  # EITHER patch an existing custom race ...
  "race": {"plugin": "CustomRace.esp", "edid": "CustomRace"},
  # ... OR create a new playable race cloned from another one (usually a vanilla race)
  "new_race": {"clone_plugin": "Skyrim.esm", "clone_edid": "NordRace", "edid": "MyFollowerRace",
               "name": "Shown In RaceMenu", "description": "...", "rcs_json": true},

  "headparts": {                                  # follower HDPT EditorIDs to make usable by the race
    "Follower_Hair":  {"model": "actors\\character\\X\\Patch\\hair\\Hair.nif", "playable": true},
    "Follower_Scalp": {"model": "...", "drop_tri": true},       # tri file missing / wrong vertex count
    "Follower_Eyes":  {"model": "...", "playable": true, "drop_tnam": true},
    "Follower_LashesUpper": {"model": "...", "tri": "actors\\character\\X\\Patch\\eyes\\LashesUpper.tri"}
  },                                              # HNAM extra parts of listed parts are included automatically
  # "tri" replaces the part's NAM1 path. Use it whenever two parts on one character share a tri file: RaceMenu
  # keys sculpt by tri path, so shared tris merge their sculpt on save (copy the tri per part first).
  "race_defaults": {"female": ["Follower_Head"]}, # replace the race's default head part of the same type
  "skin_arma": ["Follower_BodyAA", "Follower_HandsAA", "Follower_FeetAA"]   # optional: let the race wear the skin
}
"""
import json, os, struct, sys
sys.path.insert(0, os.path.dirname(__file__))
from esp_lib import Plugin, PluginSet, PatchWriter, zstr, zstr_val, u32, HDPT_TYPES

cfg = json.load(open(sys.argv[1], encoding='utf-8'))
ps = PluginSet(cfg['search_dirs'])
F = ps.load(cfg['follower_plugin'])
masters = F.masters + [F.name]

if 'race' in cfg:
    R = ps.load(cfg['race']['plugin'])
    race_fid, race_rec = R.get(cfg['race']['edid'])
    masters += R.masters + [R.name]
    race_src = R
else:
    nr = cfg['new_race']
    C = ps.load(nr['clone_plugin'], {'RACE'})
    race_fid, race_rec = C.get(nr['clone_edid'])
    masters += C.masters + [C.name]
    race_src = C
masters += cfg.get('extra_masters', [])
W = PatchWriter(masters)

if 'race' in cfg:
    target_race = W.remap(R, race_fid)
    race_out_fid = target_race
else:
    target_race = race_out_fid = W.new_fid()
race_edid = zstr_val(Plugin.sub(race_rec[2], 'EDID')) if 'race' in cfg else cfg['new_race']['edid']
print('masters:', W.masters)
print('target race: %s -> %08X' % (race_edid, target_race))


def hdpt_type(plugin, fid):
    """HDPT part type for a FormID as seen from `plugin`."""
    owner = ps.load(plugin.file_of(fid), {'HDPT'})   # the defining plugin, head parts only
    rec = owner.records.get((len(owner.masters) << 24) | (fid & 0xFFFFFF))
    return struct.unpack('<I', Plugin.sub(rec[2], 'PNAM'))[0] if rec else None


# ---------------------------------------------------------------- valid-race lists
flst_map = {}


def list_with_race(src, list_fid):
    g = src.gid(list_fid)
    if g in flst_map:
        return flst_map[g]
    L = ps.load(src.file_of(list_fid), {'FLST'})
    t, fl, subs = L.records[(len(L.masters) << 24) | g[1]]
    try:
        races = [W.remap(L, struct.unpack('<I', v)[0]) for st, v in subs if st == 'LNAM']
    except KeyError as e:
        sys.exit('list %s references a plugin that is not a patch master (%s); add it to "extra_masters"' % (g, e))
    nid = W.new_fid()
    edid = '%s_%s' % (zstr_val(Plugin.sub(subs, 'EDID')), race_edid)
    entries = races + ([target_race] if target_race not in races else [])
    W.add('FLST', 0, nid, [('EDID', zstr(edid))] + [('LNAM', u32(r)) for r in entries])
    flst_map[g] = nid
    print('FLST %08X %s (%d races + target)' % (nid, edid, len(races)))
    return nid


# ---------------------------------------------------------------- head parts
todo = dict(cfg['headparts'])
queue = list(todo)
while queue:                                      # pull in HNAM extras automatically
    e = queue.pop(0)
    fid, (t, fl, subs) = F.get(e)
    for st, v in subs:
        if st == 'HNAM':
            x = struct.unpack('<I', v)[0]
            if F.is_own(x):
                xe = zstr_val(Plugin.sub(F.records[x][2], 'EDID'))
                if xe not in todo:
                    todo[xe] = {}
                    queue.append(xe)

for edid, opt in todo.items():
    fid, (t, flags, subs) = F.get(edid)
    if not F.is_own(fid):
        sys.exit('%s is defined in %s; this tool only overrides head parts the follower plugin defines' % (edid, F.file_of(fid)))
    out = []
    for (st, v), (_, rv) in zip(subs, W.remap_subs(F, 'HDPT', subs)):
        if st == 'RNAM':
            rv = u32(list_with_race(F, struct.unpack('<I', v)[0]))
        elif st == 'DATA' and opt.get('playable'):
            rv = bytes([v[0] | 0x01])
        elif st in ('NAM0', 'NAM1') and opt.get('drop_tri'):
            continue
        elif st == 'TNAM' and opt.get('drop_tnam'):
            continue
        elif st == 'MODL' and opt.get('model'):
            rv = zstr(opt['model'])
        elif st == 'NAM1' and opt.get('tri') and not opt.get('drop_tri'):
            rv = zstr(opt['tri'])
        out.append((st, rv))
    if opt.get('model') and not any(st == 'MODL' for st, _ in out):
        names = [st for st, _ in out]               # HDPT order: EDID, FULL, MODL, ...
        i = names.index('FULL' if 'FULL' in names else 'EDID') + 1
        out.insert(i, ('MODL', zstr(opt['model'])))
    if not any(st == 'RNAM' for st, _ in out):
        print('  note: %s has no valid-races list; it is usable by any race' % edid)
    if opt.get('playable'):
        flags &= ~0x4                             # HDPT record flag 0x4 = Non-Playable
    W.add('HDPT', flags, W.remap(F, fid), out)
    print('HDPT %08X %-30s %s' % (W.remap(F, fid), edid, ', '.join(k for k in ('model', 'tri', 'playable', 'drop_tri', 'drop_tnam') if opt.get(k))))

# RaceMenu keys sculpt by tri path: warn when parts that will sit on the same character still share one
tri_users = {}
for rec in W.groups.get('HDPT', []):
    subs = __import__('esp_lib').parse_subs(rec[24:])
    e = zstr_val(Plugin.sub(subs, 'EDID'))
    for st, v in subs:
        if st == 'NAM1':
            tri_users.setdefault(zstr_val(v).lower(), []).append(e)
for t, users in tri_users.items():
    if len(users) > 1:
        print('  WARNING: %s share %s - RaceMenu will merge their sculpt on save; give each its own tri ("tri" option)' % (users, t))

# ---------------------------------------------------------------- race
t, rflags, rsubs = race_rec
rsubs_new = [list(x) for x in W.remap_subs(race_src, 'RACE', rsubs)]
wanted = {}                                       # sex -> {type: local fid}
for sex, edids in cfg.get('race_defaults', {}).items():
    for e in edids:
        fid, rec = F.get(e)
        wanted.setdefault(sex, {})[struct.unpack('<I', Plugin.sub(rec[2], 'PNAM'))[0]] = W.remap(F, fid)

# Head data layout: NAM0, MNAM|FNAM, (INDX, HEAD)*, MPAI/MPAV..., then the next NAM0 / FNAM ...
result, sex, in_head = [], None, False
pending, sec_idx, in_list = {}, [], False
def flush_section():
    """Append default parts whose type the race did not list yet, right after the section's HEAD list."""
    global in_list
    if sex and pending.get(sex):
        idx = max(sec_idx + [-1])
        for ptype, lf in pending[sex].items():
            idx += 1
            result.extend([['INDX', u32(idx)], ['HEAD', u32(lf)]])
            print('RACE %s default %s: added %08X' % (sex, HDPT_TYPES[ptype], lf))
        pending[sex] = {}
    in_list = False

for (st, v), (_, nv) in zip(rsubs, rsubs_new):
    if st == 'NAM0':
        in_head = True
    if in_head and st in ('MNAM', 'FNAM'):
        flush_section()
        sex = 'male' if st == 'MNAM' else 'female'
        pending[sex] = dict(wanted.get(sex, {}))
        sec_idx, in_list = [], True
        result.append([st, nv])
        continue
    if in_list and st not in ('INDX', 'HEAD'):
        flush_section()                           # HEAD list (possibly empty) just ended
    if in_list and st == 'INDX':
        sec_idx.append(struct.unpack('<I', v)[0])
    if st == 'HEAD' and in_head and sex in wanted:
        ptype = hdpt_type(race_src, struct.unpack('<I', v)[0])
        if ptype in wanted[sex]:
            nv = u32(wanted[sex][ptype])
            pending[sex].pop(ptype, None)
            print('RACE %s default %s: replaced with %08X' % (sex, HDPT_TYPES[ptype], wanted[sex][ptype]))
    result.append([st, nv])
flush_section()

if 'new_race' in cfg:
    nr = cfg['new_race']
    def setsub(t, val, after='EDID'):
        for x in result:
            if x[0] == t:
                x[1] = val; return
        i = next(k for k, x in enumerate(result) if x[0] == after) + 1
        result.insert(i, [t, val])
    setsub('EDID', zstr(nr['edid']))
    setsub('FULL', zstr(nr.get('name', nr['edid'])))
    setsub('DESC', zstr(nr.get('description', '')), 'FULL')
    data = bytearray(Plugin.sub(result, 'DATA'))
    struct.pack_into('<I', data, 32, struct.unpack_from('<I', data, 32)[0] | 0x1)   # Playable
    setsub('DATA', bytes(data))
    clone_local = W.remap(C, race_fid)
    # Armor race: lets the new race use every armor addon made for the clone source, without RCS.
    rn = [x for x in result if x[0] == 'RNAM']
    if not rn or struct.unpack('<I', rn[-1][1])[0] == 0:
        if rn:
            rn[-1][1] = u32(clone_local)
        else:
            result.append(['RNAM', u32(clone_local)])
    if not any(x[0] == 'NAM8' for x in result):
        result.insert(len(result) - 1, ['NAM8', u32(clone_local)])
    rflags &= ~0x40000
W.add('RACE', rflags, race_out_fid, [tuple(x) for x in result])

# ---------------------------------------------------------------- skin
for e in cfg.get('skin_arma', []):
    fid, (t, fl, subs) = F.get(e)
    out = W.remap_subs(F, 'ARMA', subs)
    if u32(target_race) not in [v for st, v in out if st == 'MODL' and len(v) == 4]:
        last = max(k for k, (st, v) in enumerate(out) if st == 'MODL' and len(v) == 4)
        out.insert(last + 1, ['MODL', u32(target_race)])
    W.add('ARMA', fl, W.remap(F, fid), out)
    print('ARMA %08X %s + target race' % (W.remap(F, fid), e))

n = W.write(cfg['output'], esl=cfg.get('esl', True), description=cfg.get('description', ''))
print('wrote %s (%d records+groups)' % (cfg['output'], n))

if 'new_race' in cfg and cfg['new_race'].get('rcs_json', True):
    nr = cfg['new_race']
    root = os.path.dirname(os.path.abspath(cfg['output']))
    p = os.path.join(root, 'SKSE', 'Plugins', 'RCS', nr['edid'] + '.json')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    ce = nr['clone_edid']
    json.dump({'RCS': [{'name': nr['edid'],
                        'race': {'form': nr['edid'], 'proxies': [ce], 'armor': {'race': ce}},
                        'vampireRace': {'form': nr['edid'], 'proxies': [ce + 'Vampire'], 'armor': {'race': ce + 'Vampire'}},
                        'headPart': 'Human'}]}, open(p, 'w'), indent=4)
    print('wrote Race Compatibility SKSE config', p)
