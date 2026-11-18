"""Raw record headers + every HDPT of Blood Scion.esp vs Vayne Race.esp."""
import os, struct, sys, zlib
MODS = r"D:\SkyrimMod\wabbajack\mods"


def walk(path):
    d = open(path, 'rb').read()
    hsz, = struct.unpack_from('<I', d, 4)
    out = [('TES4', d[0:24].hex())]
    i = 24 + hsz
    while i < len(d):
        t = d[i:i + 4].decode('latin1'); sz, = struct.unpack_from('<I', d, i + 4)
        if t == 'GRUP':
            out.append(('GRUP', d[i + 8:i + 12].decode('latin1'), d[i + 12:i + 24].hex()))
            i += 24; continue
        flags, fid, vc, ver, unk = struct.unpack_from('<IIIHH', d, i + 8)
        body = d[i + 24:i + 24 + sz]
        subs, j = [], 0
        while j < len(body):
            st = body[j:j + 4].decode('latin1'); n, = struct.unpack_from('<H', body, j + 4)
            subs.append((st, body[j + 6:j + 6 + n])); j += 6 + n
        out.append((t, '%08X' % fid, 'flags %X vc %X ver %d unk %d' % (flags, vc, ver, unk), subs))
        i += 24 + sz
    return out


for name in (r"Blood Scion\Blood Scion.esp", r"Vayne Race\Vayne Race.esp"):
    print('=' * 10, name)
    for r in walk(os.path.join(MODS, name)):
        if r[0] in ('TES4', 'GRUP'):
            print(' ', r)
        elif r[0] == 'HDPT':
            subs = r[3]
            show = [(st, v.split(b'\0')[0].decode('latin1') if st in ('EDID', 'FULL') else v.hex()) for st, v in subs
                    if st not in ('MODT', 'MODL', 'NAM1')]
            print('  HDPT', r[1], r[2], show)
        else:
            print(' ', r[0], r[1], r[2])
