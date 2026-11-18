"""Subrecord-type sequence (run-length) and selected values of BloodScionRace vs VayneRace."""
import itertools, os, struct, sys
sys.path.insert(0, r"C:\Users\fairl\.claude\skills\follower-to-race\scripts")
from esp_lib import Plugin, zstr_val
MODS = r"D:\SkyrimMod\wabbajack\mods"
for path, edid in ((r"Blood Scion\Blood Scion.esp", 'BloodScionRace'), (r"Vayne Race\Vayne Race.esp", 'VayneRace')):
    P = Plugin(os.path.join(MODS, path))
    fid, (t, fl, subs) = P.get(edid)
    seq = ['%s%s' % (k, 'x%d' % n if n > 1 else '') for k, n in ((k, len(list(g))) for k, g in itertools.groupby(st for st, _ in subs))]
    print('=' * 8, edid)
    print(' ', ' '.join(seq)[:1500])
    for st, v in subs:
        if st in ('RPRM', 'RPRF', 'DFTM', 'DFTF', 'FTSF', 'NAM8', 'RNAM', 'WNAM', 'PNAM', 'UNAM', 'TINL'):
            print('   ', st, v.hex())
