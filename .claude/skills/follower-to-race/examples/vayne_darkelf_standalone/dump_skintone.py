"""Show VayneRace's SkinTone tint layers (per sex) with their colour presets."""
import struct, sys
sys.path.insert(0, r"C:\Users\fairl\.claude\skills\follower-to-race\scripts")
from esp_lib import Plugin, zstr_val
P = Plugin(r"D:\SkyrimMod\wabbajack\mods\Vayne Race\Vayne Race.esp")
S = Plugin(r"D:\SkyrimMod\wabbajack\Stock Game\Data\Skyrim.esm", {'CLFM'})


def clfm(f):
    src = P if f >> 24 == 1 else S
    r = src.records.get(f)
    if not r:
        return '%08X ?' % f
    c = Plugin.sub(r[2], 'CNAM')
    return '%08X %s #%02X%02X%02X' % (f, zstr_val(Plugin.sub(r[2], 'EDID')), c[0], c[1], c[2])


fid, (t, fl, subs) = P.get('VayneRace')
sex, on = None, False
for st, v in subs:
    if st == 'NAM0':
        sex = 'male' if sex is None else 'female'
    if st == 'TINI':
        on, idx = False, struct.unpack('<H', v)[0]
    if st == 'TINT' and zstr_val(v).lower().endswith('skintone.dds'):
        on = True
        print(sex, 'TINI', idx, zstr_val(v))
    if on and st in ('TINP', 'TIND', 'TINC', 'TINV', 'TIRS'):
        if st in ('TIND', 'TINC'):
            print('   ', st, clfm(struct.unpack('<I', v)[0]))
        elif st == 'TINV':
            print('   ', st, struct.unpack('<f', v)[0])
        else:
            print('   ', st, v.hex())
