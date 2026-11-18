"""Rewrite texture paths inside a NIF's BSShaderTextureSet blocks (binary-safe; everything else is untouched).

usage: python retexture_nif.py <in.nif> <out.nif> <slot>=<path> [<slot>=<path> ...]
       slot is the texture-set index (0 diffuse, 1 normal, 2 glow/skin, 3 height/detail, 4 env, 5 env mask, 6 tint, 7 specular)
"""
import struct, sys


def retexture(src, dst, slots):
    d = open(src, 'rb').read()
    p = d.index(b'\n') + 1 + 9
    nb, = struct.unpack_from('<I', d, p); p += 8
    for _ in range(3):
        p += 1 + d[p]
    nt, = struct.unpack_from('<H', d, p); p += 2
    types = []
    for _ in range(nt):
        l, = struct.unpack_from('<I', d, p); types.append(d[p + 4:p + 4 + l].decode()); p += 4 + l
    bt = list(struct.unpack_from('<%dH' % nb, d, p)); p += 2 * nb
    bs_off = p; bs = list(struct.unpack_from('<%dI' % nb, d, p)); p += 4 * nb
    ns, _ = struct.unpack_from('<II', d, p); p += 8
    for _ in range(ns):
        l, = struct.unpack_from('<I', d, p); p += 4 + l
    ng, = struct.unpack_from('<I', d, p); p += 4 + 4 * ng
    data0 = p
    blocks, off = [], data0
    for i in range(nb):
        blocks.append(d[off:off + bs[i]]); off += bs[i]
    footer = d[off:]
    changed = 0
    for i in range(nb):
        if types[bt[i]] != 'BSShaderTextureSet':
            continue
        b = blocks[i]
        n, = struct.unpack_from('<I', b, 0); q = 4; paths = []
        for _ in range(n):
            l, = struct.unpack_from('<I', b, q); paths.append(b[q + 4:q + 4 + l].decode('latin1')); q += 4 + l
        for slot, path in slots.items():
            while len(paths) <= slot:
                paths.append('')
            paths[slot] = path
        nbk = struct.pack('<I', len(paths)) + b''.join(struct.pack('<I', len(x)) + x.encode('latin1') for x in paths) + b[q:]
        blocks[i] = nbk; bs[i] = len(nbk); changed += 1
    if not changed:
        sys.exit('no BSShaderTextureSet in %s' % src)
    out = bytearray(d[:bs_off]) + struct.pack('<%dI' % nb, *bs) + d[bs_off + 4 * nb:data0] + b''.join(blocks) + footer
    open(dst, 'wb').write(bytes(out))
    return changed


if __name__ == '__main__':
    slots = {int(a.split('=', 1)[0]): a.split('=', 1)[1] for a in sys.argv[3:]}
    print('retextured %d texture set(s) -> %s' % (retexture(sys.argv[1], sys.argv[2], slots), sys.argv[2]))
