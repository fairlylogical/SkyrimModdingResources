"""Dump the head-related parts of VayneRace and the VR_Eyes head part."""
import os, struct, sys
sys.path.insert(0, r"C:\Users\fairl\.claude\skills\follower-to-race\scripts")
from esp_lib import Plugin, zstr_val
P = Plugin(r"D:\SkyrimMod\wabbajack\mods\Vayne Race\Vayne Race.esp")
SKY = Plugin(r"D:\SkyrimMod\wabbajack\Stock Game\Data\Skyrim.esm", {'HDPT'})


def name(f):
    src = P if f >> 24 == 1 else SKY
    r = src.records.get(f & 0xFFFFFF if f >> 24 == 0 else f)
    return zstr_val(Plugin.sub(r[2], 'EDID')) if r else '?'


fid, (t, fl, subs) = P.get('VayneRace')
seq = [st for st, _ in subs]
print('subrecord order:', ' '.join(seq))
for st, v in subs:
    if st in ('HEAD', 'DFTF', 'FTSF', 'WNAM', 'RNAM', 'NAM8'):
        f = struct.unpack('<I', v)[0]
        print('  %s %08X %s' % (st, f, name(f)))
    if st in ('MNAM', 'FNAM', 'NAM0', 'INDX'):
        print('  ', st, v.hex())
for e in ('VR_Eyes', 'VR_AO', 'VR_Eyelashes'):
    fid, (t, fl, subs) = P.get(e)
    print(e, 'recflags %X' % fl, [(st, zstr_val(v) if st in ('MODL', 'NAM1') else v.hex()) for st, v in subs])
