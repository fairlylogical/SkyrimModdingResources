"""Compare Vayne Race.esp with the working Blood Scion.esp: header, FLST, main HDPTs, race head-related fields, RCS json."""
import os, struct, sys
sys.path.insert(0, r"C:\Users\fairl\.claude\skills\follower-to-race\scripts")
from esp_lib import Plugin, zstr_val
MODS = r"D:\SkyrimMod\wabbajack\mods"
for path in (os.path.join(MODS, "Blood Scion", "Blood Scion.esp"), os.path.join(MODS, "Vayne Race", "Vayne Race.esp")):
    P = Plugin(path)
    print('=' * 20, P.name, 'masters', P.masters, 'flags %X' % P.flags)
    print('  header:', [(st, v.hex() if st == 'HEDR' else zstr_val(v)) for st, v in P.header])
    for fid, (t, fl, subs) in sorted(P.records.items()):
        if t == 'FLST':
            print('  FLST %08X flags %X' % (fid, fl), [(st, v.hex()) for st, v in subs])
        if t == 'HDPT':
            d = Plugin.sub(subs, 'DATA')
            if d[0] & 1:
                print('  HDPT %08X recflags %X %s' % (fid, fl, [(st, zstr_val(v) if st in ('EDID', 'FULL', 'MODL', 'NAM1') else v.hex())
                                                         for st, v in subs if st != 'MODT']))
        if t == 'RACE':
            print('  RACE %08X recflags %X' % (fid, fl))
            for st, v in subs:
                if st in ('EDID', 'FULL', 'RNAM', 'NAM8', 'DFTF', 'HEAD', 'WNAM'):
                    print('    ', st, zstr_val(v) if st in ('EDID', 'FULL') else v.hex())
                if st == 'DATA':
                    print('     DATA flags %08X' % struct.unpack_from('<I', v, 32)[0], 'len', len(v))
    for dp, _, fs in os.walk(os.path.dirname(path)):
        for f in fs:
            if f.endswith('.json') and 'RCS' in dp:
                print('  RCS', open(os.path.join(dp, f)).read())
