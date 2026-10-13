"""Minimal TES4 (Skyrim SE) plugin reader/writer.

Model:
  Plugin -> list of top-level nodes (Record | Group)
  Group  -> header fields + list of child nodes
  Record -> type, flags, formid, header meta, subrecords [[sig, bytes], ...]

Compressed records keep their original compressed payload so an untouched
record round-trips byte-for-byte; they are only re-deflated if their
subrecords actually changed.
"""
import struct
import zlib

REC_HDR = struct.Struct('<4sIIIHHHH')    # type, dataSize, flags, formid, ts, vcs, ver, unk
GRP_HDR = struct.Struct('<4sI4sIHHHH')   # GRUP, size, label, gtype, ts, vcs, ver, unk
SUB_HDR = struct.Struct('<4sH')

COMPRESSED = 0x00040000


class Record:
    __slots__ = ('type', 'flags', 'formid', 'ts', 'vcs', 'ver', 'unk',
                 'subs', 'compressed', '_raw_data', '_raw_payload')

    def __init__(self, type_, flags, formid, meta, subs, compressed=False,
                 raw_data=None, raw_payload=None):
        self.type = type_
        self.flags = flags
        self.formid = formid
        self.ts, self.vcs, self.ver, self.unk = meta
        self.subs = subs          # list of [sig(bytes4), data(bytes)]
        self.compressed = compressed
        self._raw_data = raw_data          # decompressed subrecord blob as loaded
        self._raw_payload = raw_payload    # on-disk payload as loaded

    @property
    def meta(self):
        return (self.ts, self.vcs, self.ver, self.unk)

    # --- subrecord helpers -------------------------------------------------
    def get(self, sig):
        if isinstance(sig, str):
            sig = sig.encode()
        for s, d in self.subs:
            if s == sig:
                return d
        return None

    def get_all(self, sig):
        if isinstance(sig, str):
            sig = sig.encode()
        return [d for s, d in self.subs if s == sig]

    def index_of(self, sig):
        if isinstance(sig, str):
            sig = sig.encode()
        for i, (s, _d) in enumerate(self.subs):
            if s == sig:
                return i
        return -1

    def set(self, sig, data):
        """Replace first occurrence, or append if absent."""
        if isinstance(sig, str):
            sig = sig.encode()
        i = self.index_of(sig)
        if i < 0:
            self.subs.append([sig, data])
        else:
            self.subs[i][1] = data

    def remove_all(self, sig):
        if isinstance(sig, str):
            sig = sig.encode()
        self.subs = [[s, d] for s, d in self.subs if s != sig]

    def insert_after(self, after_sig, sig, data):
        """Insert (sig,data) right after the last run of after_sig, else append."""
        if isinstance(after_sig, str):
            after_sig = after_sig.encode()
        if isinstance(sig, str):
            sig = sig.encode()
        last = -1
        for i, (s, _d) in enumerate(self.subs):
            if s == after_sig:
                last = i
        if last < 0:
            self.subs.append([sig, data])
        else:
            self.subs.insert(last + 1, [sig, data])

    @property
    def editor_id(self):
        d = self.get(b'EDID')
        return d[:-1].split(b'\x00')[0].decode('cp1252', 'replace') if d else None

    @editor_id.setter
    def editor_id(self, value):
        self.set(b'EDID', value.encode('cp1252') + b'\x00')

    def copy(self):
        """Deep-ish copy: fresh subrecord list, no raw payload reuse."""
        return Record(self.type, self.flags, self.formid, self.meta,
                      [[s, d] for s, d in self.subs], self.compressed)

    def __repr__(self):
        return '<%s %08X %s>' % (self.type.decode(), self.formid, self.editor_id)


class Group:
    __slots__ = ('label', 'gtype', 'ts', 'vcs', 'ver', 'unk', 'items')

    def __init__(self, label, gtype, meta, items):
        self.label = label      # raw 4 bytes
        self.gtype = gtype
        self.ts, self.vcs, self.ver, self.unk = meta
        self.items = items

    @property
    def meta(self):
        return (self.ts, self.vcs, self.ver, self.unk)

    def __repr__(self):
        lbl = self.label.decode('cp1252', 'replace') if self.gtype == 0 else self.label.hex()
        return '<GRUP t%d %s n=%d>' % (self.gtype, lbl, len(self.items))


def parse_subrecords(data):
    """Return list of [sig, data]; honours XXXX oversized-length prefix."""
    subs = []
    off = 0
    n = len(data)
    override = None
    while off + 6 <= n:
        sig, size = SUB_HDR.unpack_from(data, off)
        off += 6
        if sig == b'XXXX':
            override = struct.unpack_from('<I', data, off)[0]
            off += size
            continue
        if override is not None:
            size = override
            override = None
        subs.append([sig, data[off:off + size]])
        off += size
    return subs


def build_subrecords(subs):
    out = bytearray()
    for sig, data in subs:
        if len(data) > 0xFFFF:
            out += SUB_HDR.pack(b'XXXX', 4)
            out += struct.pack('<I', len(data))
            out += SUB_HDR.pack(sig, 0)
            out += data
        else:
            out += SUB_HDR.pack(sig, len(data))
            out += data
    return bytes(out)


def _read_nodes(buf, start, end):
    items = []
    off = start
    while off < end:
        sig = buf[off:off + 4]
        if sig == b'GRUP':
            _, gsize, label, gtype, ts, vcs, ver, unk = GRP_HDR.unpack_from(buf, off)
            children = _read_nodes(buf, off + 24, off + gsize)
            items.append(Group(label, gtype, (ts, vcs, ver, unk), children))
            off += gsize
        else:
            type_, dsize, flags, formid, ts, vcs, ver, unk = REC_HDR.unpack_from(buf, off)
            payload = buf[off + 24:off + 24 + dsize]
            comp = bool(flags & COMPRESSED)
            data = zlib.decompress(payload[4:]) if comp else payload
            items.append(Record(type_, flags, formid, (ts, vcs, ver, unk),
                                parse_subrecords(data), comp,
                                raw_data=data, raw_payload=payload))
            off += 24 + dsize
    return items


def _write_nodes(items, out):
    for it in items:
        if isinstance(it, Group):
            head = len(out)
            out += b'\x00' * 24
            _write_nodes(it.items, out)
            gsize = len(out) - head
            GRP_HDR.pack_into(out, head, b'GRUP', gsize, it.label, it.gtype,
                              it.ts, it.vcs, it.ver, it.unk)
        else:
            data = build_subrecords(it.subs)
            flags = it.flags
            if it.compressed:
                if data == it._raw_data and it._raw_payload is not None:
                    payload = it._raw_payload      # byte-exact passthrough
                else:
                    payload = struct.pack('<I', len(data)) + zlib.compress(data, 9)
                flags |= COMPRESSED
            else:
                payload = data
                flags &= ~COMPRESSED
            out += REC_HDR.pack(it.type, len(payload), flags, it.formid,
                                it.ts, it.vcs, it.ver, it.unk)
            out += payload


class Plugin:
    def __init__(self, path=None):
        self.tes4 = None
        self.nodes = []
        self.path = path
        if path:
            self.load(path)

    def load(self, path):
        with open(path, 'rb') as f:
            buf = f.read()
        self.path = path
        type_, dsize, flags, formid, ts, vcs, ver, unk = REC_HDR.unpack_from(buf, 0)
        assert type_ == b'TES4', type_
        self.tes4 = Record(type_, flags, formid, (ts, vcs, ver, unk),
                           parse_subrecords(buf[24:24 + dsize]))
        self.nodes = _read_nodes(buf, 24 + dsize, len(buf))

    def to_bytes(self):
        out = bytearray()
        _write_nodes(self.nodes, out)
        hdr_data = build_subrecords(self.tes4.subs)
        head = bytearray()
        head += REC_HDR.pack(b'TES4', len(hdr_data), self.tes4.flags,
                             self.tes4.formid, self.tes4.ts, self.tes4.vcs,
                             self.tes4.ver, self.tes4.unk)
        head += hdr_data
        return bytes(head) + bytes(out)

    def save(self, path):
        with open(path, 'wb') as f:
            f.write(self.to_bytes())

    # --- traversal ---------------------------------------------------------
    def walk(self, items=None):
        """Yield every Record (recursively)."""
        if items is None:
            items = self.nodes
        for it in items:
            if isinstance(it, Group):
                yield from self.walk(it.items)
            else:
                yield it

    def walk_with_parent(self, items=None, parent=None):
        if items is None:
            items = self.nodes
        for it in items:
            if isinstance(it, Group):
                yield from self.walk_with_parent(it.items, it)
            else:
                yield it, parent

    def groups(self, items=None):
        if items is None:
            items = self.nodes
        for it in items:
            if isinstance(it, Group):
                yield it
                yield from self.groups(it.items)

    def records(self, type_):
        if isinstance(type_, str):
            type_ = type_.encode()
        return [r for r in self.walk() if r.type == type_]

    def by_formid(self, fid):
        for r in self.walk():
            if r.formid == fid:
                return r
        return None

    def top_group(self, sig):
        if isinstance(sig, str):
            sig = sig.encode()
        for it in self.nodes:
            if isinstance(it, Group) and it.gtype == 0 and it.label == sig:
                return it
        return None

    # --- masters -----------------------------------------------------------
    @property
    def masters(self):
        return [d.split(b'\x00')[0].decode('cp1252') for s, d in self.tes4.subs
                if s == b'MAST']

    def add_master(self, name):
        """Append a master after the existing MAST/DATA pairs. Returns its index."""
        ms = self.masters
        if name in ms:
            return ms.index(name)
        last = -1
        for i, (s, _d) in enumerate(self.tes4.subs):
            if s in (b'MAST', b'DATA'):
                last = i
        self.tes4.subs.insert(last + 1, [b'MAST', name.encode('cp1252') + b'\x00'])
        self.tes4.subs.insert(last + 2, [b'DATA', struct.pack('<Q', 0)])
        return len(ms)

    def hedr(self):
        return struct.unpack('<fII', self.tes4.get(b'HEDR'))

    def set_hedr(self, ver=None, numrec=None, nextid=None):
        v, n, x = self.hedr()
        self.tes4.set(b'HEDR', struct.pack('<fII',
                                           v if ver is None else ver,
                                           n if numrec is None else numrec,
                                           x if nextid is None else nextid))

    def count_records(self):
        return sum(1 for _ in self.walk())


def u32(b, off=0):
    return struct.unpack_from('<I', b, off)[0]


def p32(v):
    return struct.pack('<I', v)
