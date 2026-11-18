"""Minimal Skyrim SE plugin (ESP/ESM/ESL) reader/writer with master-aware FormID remapping."""
import os, struct, zlib

HDPT_TYPES = {0: 'Misc', 1: 'Face', 2: 'Eyes', 3: 'Hair', 4: 'FacialHair', 5: 'Scar', 6: 'Eyebrows'}
HDPT_TYPE_IDS = {v.lower(): k for k, v in HDPT_TYPES.items()}

# FormID-carrying subrecords per record type: subrecord -> byte offsets, or 'array' (every dword).
FORMID_FIELDS = {
    'HDPT': {'HNAM': [0], 'TNAM': [0], 'CNAM': [0], 'RNAM': [0]},
    'FLST': {'LNAM': [0]},
    'ARMO': {'RNAM': [0], 'MODL': [0], 'KWDA': 'array', 'EITM': [0], 'ETYP': [0], 'BIDS': [0], 'BAMT': [0],
             'YNAM': [0], 'ZNAM': [0], 'TNAM': [0]},
    'ARMA': {'RNAM': [0], 'MODL': [0], 'NAM0': [0], 'NAM1': [0], 'NAM2': [0], 'NAM3': [0], 'SNDD': [0], 'ONAM': [0]},
    'RACE': {'SPLO': [0], 'WNAM': [0], 'KWDA': 'array', 'VTCK': [0, 4], 'DNAM': [0, 4], 'HCLF': [0, 4],
             'ATKD': [8, 28], 'GNAM': [0], 'NAM4': [0], 'NAM5': [0], 'NAM7': [0], 'ONAM': [0], 'LNAM': [0],
             'QNAM': [0], 'UNES': [0], 'HEAD': [0], 'AHCM': [0], 'AHCF': [0], 'FTSM': [0], 'FTSF': [0],
             'DFTM': [0], 'DFTF': [0], 'RPRM': [0], 'RPRF': [0], 'TIND': [0], 'TINC': [0], 'NAM8': [0],
             'RNAM': [0], 'WKMV': [0], 'RNMV': [0], 'SWMV': [0], 'FLMV': [0], 'SNMV': [0], 'SPMV': [0], 'ATKR': [0]},
}
# In ARMA/ARMO, MODL of size 4 is a FormID (race / armor addon); MOD2..MOD5 are model paths.


def parse_subs(body):
    out, i, big = [], 0, None
    while i < len(body):
        t = body[i:i + 4].decode('latin1'); sz, = struct.unpack_from('<H', body, i + 4); i += 6
        if big is not None:
            sz, big = big, None
        if t == 'XXXX':
            big, = struct.unpack_from('<I', body, i); i += sz; continue
        out.append([t, bytes(body[i:i + sz])]); i += sz
    return out


def gid_str(g):
    return '%s:%06X' % (g[0], g[1])


def zstr_val(v):
    return v.split(b'\0')[0].decode('cp1252', 'replace')


class Plugin:
    """Parsed plugin. records: fid -> [type, flags, subs]. Optionally restrict to some record types."""
    def __init__(self, path, types=None):
        self.path, self.name = path, os.path.basename(path)
        d = open(path, 'rb').read()
        hsz, = struct.unpack_from('<I', d, 4)
        self.flags, = struct.unpack_from('<I', d, 8)
        self.header = parse_subs(d[24:24 + hsz])
        self.masters = [zstr_val(v) for t, v in self.header if t == 'MAST']
        self.records, self.by_edid = {}, {}

        def walk(i, end):
            while i < end:
                t = d[i:i + 4].decode('latin1'); sz, = struct.unpack_from('<I', d, i + 4)
                if t == 'GRUP':
                    label = d[i + 8:i + 12].decode('latin1'); gtype, = struct.unpack_from('<I', d, i + 12)
                    if types is None or gtype != 0 or label in types:
                        walk(i + 24, i + sz)
                    i += sz; continue
                flags, fid = struct.unpack_from('<II', d, i + 8)
                if types is None or t in types:
                    body = d[i + 24:i + 24 + sz]
                    if flags & 0x40000:
                        body = zlib.decompress(body[4:]); flags &= ~0x40000
                    subs = parse_subs(body)
                    self.records[fid] = [t, flags, subs]
                    for st, v in subs:
                        if st == 'EDID':
                            self.by_edid[zstr_val(v).lower()] = fid
                            break
                i += 24 + sz
        walk(24 + hsz, len(d))

    def file_of(self, fid):
        i = fid >> 24
        return self.masters[i] if i < len(self.masters) else self.name

    def gid(self, fid):
        """Load-order independent id: (plugin name lower, object id)."""
        return (self.file_of(fid).lower(), fid & 0xFFFFFF)

    def is_own(self, fid):
        return (fid >> 24) >= len(self.masters)

    def get(self, edid_or_fid):
        fid = edid_or_fid if isinstance(edid_or_fid, int) else self.by_edid.get(edid_or_fid.lower())
        if fid is None or fid not in self.records:
            raise KeyError('%s not found in %s' % (edid_or_fid, self.name))
        return fid, self.records[fid]

    @staticmethod
    def sub(subs, t):
        return next((v for st, v in subs if st == t), None)


class PluginSet:
    """Loads plugins by name from a list of folders (mod folders first, then game Data)."""
    def __init__(self, dirs):
        self.dirs, self.cache = dirs, {}

    def path(self, name):
        for d in self.dirs:
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.lower() == name.lower():
                        return os.path.join(d, f)
        raise FileNotFoundError('plugin %s not found in %s' % (name, self.dirs))

    def load(self, name, types=None):
        key = (name.lower(), tuple(sorted(types)) if types else None)
        if key not in self.cache:
            self.cache[key] = Plugin(self.path(name), types)
        return self.cache[key]


# ------------------------------------------------------------------ writing
def zstr(s):
    return s.encode('cp1252') + b'\0'


def u32(v):
    return struct.pack('<I', v)


def sub_bytes(t, data):
    if len(data) >= 0x10000:
        return b'XXXX' + struct.pack('<HI', 4, len(data)) + t.encode() + struct.pack('<H', 0) + data
    return t.encode() + struct.pack('<H', len(data)) + data


def record_bytes(t, flags, fid, subs):
    body = b''.join(sub_bytes(st, v) for st, v in subs)
    return t.encode() + struct.pack('<IIIIHH', len(body), flags, fid, 0, 44, 0) + body


def group_bytes(label, recs):
    body = b''.join(recs)
    return b'GRUP' + struct.pack('<I', 24 + len(body)) + label.encode() + struct.pack('<IIHH', 0, 0, 0, 0) + body


# Top-level group order used by the game/CK for the types we emit.
GROUP_ORDER = ['TXST', 'HDPT', 'RACE', 'ARMO', 'FLST', 'ARMA']

VANILLA_ESM = ['skyrim.esm', 'update.esm', 'dawnguard.esm', 'hearthfires.esm', 'dragonborn.esm']


class PatchWriter:
    def __init__(self, masters):
        def key(m):
            ml = m.lower()
            if ml in VANILLA_ESM:
                return (0, VANILLA_ESM.index(ml))
            return (1 if ml.endswith('.esm') else 2, 0)
        seen, ordered = set(), []
        for m in masters:
            if m.lower() not in seen:
                seen.add(m.lower()); ordered.append(m)
        self.masters = sorted(ordered, key=key)          # stable: keeps input order within a class
        self.self_index = len(self.masters)
        self.next_obj = 0x800
        self.groups = {}
        self.warnings = []
        # gid -> local FormID for records absorbed from plugins that are NOT masters (standalone builds)
        self.redirect = {}

    def master_index(self, name):
        for i, m in enumerate(self.masters):
            if m.lower() == name.lower():
                return i
        raise KeyError('%s is not a master of the patch' % name)

    def local(self, gid):
        if gid in self.redirect:
            return self.redirect[gid]
        name, obj = gid
        return (self.master_index(name) << 24) | obj

    def remap(self, src, fid):
        if fid == 0:
            return 0
        return self.local(src.gid(fid))

    def new_fid(self):
        fid = (self.self_index << 24) | self.next_obj
        self.next_obj += 1
        return fid

    def remap_subs(self, src, rtype, subs):
        """Copy subrecords from plugin `src`, rewriting FormIDs into the patch's master numbering."""
        table = FORMID_FIELDS.get(rtype, {})
        out = []
        for st, v in subs:
            spec = table.get(st)
            if rtype in ('ARMA', 'ARMO') and st == 'MODL' and len(v) != 4:
                spec = None
            if spec:
                b = bytearray(v)
                offs = range(0, len(v) - 3, 4) if spec == 'array' else spec
                for o in offs:
                    if o + 4 <= len(b):
                        struct.pack_into('<I', b, o, self.remap(src, struct.unpack_from('<I', b, o)[0]))
                v = bytes(b)
            out.append([st, v])
        return out

    def add(self, rtype, flags, fid, subs):
        self.groups.setdefault(rtype, []).append(record_bytes(rtype, flags, fid, subs))

    def write(self, path, esl=True, author='Patch', description=''):
        groups = [(t, self.groups[t]) for t in GROUP_ORDER if t in self.groups]
        groups += [(t, r) for t, r in self.groups.items() if t not in GROUP_ORDER]
        nrec = sum(len(r) for _, r in groups) + len(groups)
        hdr = [('HEDR', struct.pack('<fII', 1.7, nrec, self.next_obj)), ('CNAM', zstr(author))]
        if description:
            hdr.append(('SNAM', zstr(description)))
        for m in self.masters:
            hdr += [('MAST', zstr(m)), ('DATA', b'\0' * 8)]
        data = record_bytes('TES4', 0x200 if esl else 0, 0, hdr) + b''.join(group_bytes(t, r) for t, r in groups)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        open(path, 'wb').write(data)
        return nrec
