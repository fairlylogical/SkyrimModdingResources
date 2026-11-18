"""Check Vayne Race.esp: every FormID resolves to Skyrim.esm or the plugin itself; every asset path exists in the mod."""
import os, struct, sys
sys.path.insert(0, r"C:\Users\fairl\.claude\skills\follower-to-race\scripts")
from esp_lib import Plugin, FORMID_FIELDS, zstr_val
OUT = r"D:\SkyrimMod\wabbajack\mods\Vayne Race"
P = Plugin(os.path.join(OUT, "Vayne Race.esp"))
SKY = Plugin(r"D:\SkyrimMod\wabbajack\Stock Game\Data\Skyrim.esm")
print('masters', P.masters, 'ESL', bool(P.flags & 0x200))
errs = []
for fid, (t, fl, subs) in sorted(P.records.items()):
    edid = zstr_val(Plugin.sub(subs, 'EDID') or b'')
    for st, v in subs:
        spec = FORMID_FIELDS.get(t, {}).get(st)
        if t in ('ARMA', 'ARMO') and st == 'MODL' and len(v) != 4:
            spec = None
        if spec:
            offs = range(0, len(v) - 3, 4) if spec == 'array' else spec
            for o in offs:
                f = struct.unpack_from('<I', v, o)[0]
                if f == 0:
                    continue
                ok = (f in P.records) if f >> 24 == 1 else (f in SKY.records) if f >> 24 == 0 else False
                if not ok:
                    errs.append('%s %s: %s -> %08X unresolved' % (t, edid, st, f))
        path = None
        if st in ('MODL', 'MOD2', 'MOD3', 'MOD4', 'MOD5', 'NAM1') and not (st == 'MODL' and len(v) == 4) \
                and not (t == 'ARMA' and st == 'NAM1'):
            path = os.path.join('meshes', zstr_val(v))
        if t == 'TXST' and st.startswith('TX'):
            path = os.path.join('textures', zstr_val(v))
        if path and 'vayne race' in path.lower() and not os.path.exists(os.path.join(OUT, path)):
            errs.append('%s %s: %s missing %s' % (t, edid, st, path))
        if path and 'vayne overhaul' in path.lower():
            errs.append('%s %s: still points at source mod %s' % (t, edid, path))
    print('%08X %s %s' % (fid, t, edid))
print('\n'.join(errs) or 'ALL REFERENCES AND PATHS OK')
