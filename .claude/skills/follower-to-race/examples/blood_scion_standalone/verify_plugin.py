import os, struct, sys
sys.path.insert(0, r"C:\Users\fairl\.claude\skills\follower-to-race\scripts")
from esp_lib import Plugin, FORMID_FIELDS, zstr_val, HDPT_TYPES
MODS = r"D:\SkyrimMod\wabbajack\mods"
OUT = os.path.join(MODS, "Blood Scion")
P = Plugin(os.path.join(OUT, "Blood Scion.esp"))
print('masters', P.masters, 'ESL', bool(P.flags & 0x200))
sky = Plugin(r"D:\SkyrimMod\wabbajack\Stock Game\Data\Skyrim.esm")
req = Plugin(os.path.join(MODS, "Requiem - The Roleplaying Overhaul", "Requiem.esp"))
srcs = {'skyrim.esm': sky, 'requiem.esp': req}

def exists(g):
    if g[0] == P.name.lower():
        return any(P.gid(f) == g for f in P.records)
    pl = srcs[g[0]]
    return any(pl.gid(f) == g for f in pl.records) if g[0] != 'skyrim.esm' else (g[1] in pl.records)

bad, nrefs = [], 0
for fid, (t, fl, subs) in P.records.items():
    table = FORMID_FIELDS.get(t, {})
    for st, v in subs:
        spec = table.get(st)
        if t in ('ARMA', 'ARMO') and st == 'MODL' and len(v) != 4:
            spec = None
        if not spec:
            continue
        offs = range(0, len(v) - 3, 4) if spec == 'array' else spec
        for o in offs:
            x = struct.unpack_from('<I', v, o)[0]
            if x == 0:
                if not (t == 'RACE' and st == 'ATKD'):   # empty attack spell is normal
                    bad.append((t, zstr_val(Plugin.sub(subs, 'EDID')), st, 'NULL'))
                continue
            nrefs += 1
            if not exists(P.gid(x)):
                bad.append((t, zstr_val(Plugin.sub(subs, 'EDID')), st, '%s:%06X' % P.gid(x)))
print('formid refs checked: %d, bad: %s' % (nrefs, bad))

# file paths
loose = {}
for dp, _, fs in os.walk(OUT):
    for f in fs:
        loose[os.path.relpath(os.path.join(dp, f), OUT).lower()] = 1
paths, missing = 0, []
for fid, (t, fl, subs) in P.records.items():
    for st, v in subs:
        isp = (st in ('MODL', 'MOD2', 'MOD3', 'MOD4', 'MOD5', 'ANAM', 'NAM1') and len(v) > 4 and v.endswith(b'\0')) or (t == 'TXST' and st.startswith('TX'))
        if t == 'RACE' and st == 'NAM1':
            isp = False
        if not isp:
            continue
        p = zstr_val(v)
        if not p:
            continue
        paths += 1
        root = 'textures' if (t == 'TXST') else 'meshes'
        rel = (root + '\\' + p).lower()
        if "coldharbour's child" in p.lower():
            if rel not in loose:
                missing.append(rel)
        elif any(s in p.lower() for s in ('serkethetyt', '000_morrigan', 'sc\\0_followers', 'morriganpatch')):
            missing.append('DEPENDS ON OLD MOD: ' + p)
print('paths checked: %d, missing: %s' % (paths, missing))
for f in loose:
    if f.endswith('.nif') and 'skeleton' not in f:
        b = open(os.path.join(OUT, f), 'rb').read().lower()
        for s in (b'serkethetyt', b'000_morrigan', b'morriganpatch'):
            if s in b:
                print('NIF still references old mod:', f, s)

# summary of the race
r = next(r for r in P.records.values() if r[0] == 'RACE')[2]
print('\nRACE', zstr_val(Plugin.sub(r, 'EDID')), '/', zstr_val(Plugin.sub(r, 'FULL')))
for st, v in r:
    if st == 'SPLO':
        g = P.gid(struct.unpack('<I', v)[0]); pl = srcs[g[0]]
        f = next(f for f in pl.records if pl.gid(f) == g)
        print('  ability:', zstr_val(Plugin.sub(pl.records[f][2], 'FULL')))
kw = Plugin.sub(r, 'KWDA')
print('  keywords:', [zstr_val(Plugin.sub(srcs[g[0]].records[next(f for f in srcs[g[0]].records if srcs[g[0]].gid(f) == g)][2], 'EDID'))
                      for g in (P.gid(x) for x in struct.unpack('<%dI' % (len(kw) // 4), kw))])
d = Plugin.sub(r, 'DATA')
print('  skills', d[:14].hex(), 'H/M/S', struct.unpack_from('<3f', d, 36), 'carry', struct.unpack_from('<f', d, 48)[0],
      'regen', [round(x, 3) for x in struct.unpack_from('<3f', d, 84)], 'heights', struct.unpack_from('<2f', d, 16), 'playable', bool(struct.unpack_from('<I', d, 32)[0] & 1))
print('  attacks', sum(1 for st, _ in r if st == 'ATKD'), '| skeleton', [zstr_val(v) for st, v in r if st == 'ANAM'])
sex, inh = None, False
for st, v in r:
    if st == 'NAM0': inh = True
    if inh and st in ('MNAM', 'FNAM'): sex = st
    if inh and st == 'HEAD' and sex == 'FNAM':
        x = struct.unpack('<I', v)[0]
        h = P.records[x][2]
        print('  female default:', zstr_val(Plugin.sub(h, 'EDID')), HDPT_TYPES[struct.unpack('<I', Plugin.sub(h, 'PNAM'))[0]])
print('  skin WNAM ->', zstr_val(Plugin.sub(P.records[struct.unpack('<I', Plugin.sub(r, 'WNAM'))[0]][2], 'EDID')))
