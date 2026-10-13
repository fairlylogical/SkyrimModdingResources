"""VMAD (script metadata) reader/writer for Skyrim SE records.

Only the shapes actually present in Lawbringer are supported: object-format 2
script lists on REFR/ACTI/QUST, with QUST fragment/alias tails preserved as an
opaque byte tail.
"""
import struct

# property types
PT_OBJECT = 1
PT_STRING = 2
PT_INT = 3
PT_FLOAT = 4
PT_BOOL = 5
PT_ARRAY_OBJECT = 11
PT_ARRAY_STRING = 12
PT_ARRAY_INT = 13
PT_ARRAY_FLOAT = 14
PT_ARRAY_BOOL = 15


class Reader:
    def __init__(self, data, off=0):
        self.d = data
        self.o = off

    def u8(self):
        v = self.d[self.o]
        self.o += 1
        return v

    def i8(self):
        v = struct.unpack_from('<b', self.d, self.o)[0]
        self.o += 1
        return v

    def u16(self):
        v = struct.unpack_from('<H', self.d, self.o)[0]
        self.o += 2
        return v

    def i16(self):
        v = struct.unpack_from('<h', self.d, self.o)[0]
        self.o += 2
        return v

    def u32(self):
        v = struct.unpack_from('<I', self.d, self.o)[0]
        self.o += 4
        return v

    def i32(self):
        v = struct.unpack_from('<i', self.d, self.o)[0]
        self.o += 4
        return v

    def f32(self):
        v = struct.unpack_from('<f', self.d, self.o)[0]
        self.o += 4
        return v

    def wstr(self):
        n = self.u16()
        s = self.d[self.o:self.o + n].decode('cp1252', 'replace')
        self.o += n
        return s

    def raw(self, n):
        v = self.d[self.o:self.o + n]
        self.o += n
        return v


class Writer:
    def __init__(self):
        self.b = bytearray()

    def u8(self, v):
        self.b += struct.pack('<B', v)

    def i8(self, v):
        self.b += struct.pack('<b', v)

    def u16(self, v):
        self.b += struct.pack('<H', v)

    def i16(self, v):
        self.b += struct.pack('<h', v)

    def u32(self, v):
        self.b += struct.pack('<I', v)

    def i32(self, v):
        self.b += struct.pack('<i', v)

    def f32(self, v):
        self.b += struct.pack('<f', v)

    def wstr(self, s):
        e = s.encode('cp1252')
        self.u16(len(e))
        self.b += e

    def raw(self, v):
        self.b += v


class Property:
    def __init__(self, name, ptype, status, value):
        self.name = name
        self.ptype = ptype
        self.status = status
        self.value = value

    def __repr__(self):
        return '%s(t%d)=%r' % (self.name, self.ptype, self.value)


class Script:
    def __init__(self, name, status, props):
        self.name = name
        self.status = status
        self.props = props

    def prop(self, name):
        low = name.lower()
        for p in self.props:
            if p.name.lower() == low:
                return p
        return None

    def __repr__(self):
        return '<Script %s props=%d>' % (self.name, len(self.props))


def _read_prop_value(r, ptype, objfmt):
    if ptype == PT_OBJECT:
        # objectFormat 2: unused (u16), aliasId (i16), formId (u32)
        # objectFormat 1: formId (u32), aliasId (i16), unused (u16)
        if objfmt == 2:
            r.u16()
            a = r.i16()
            f = r.u32()
            return ('obj', f, a)
        else:
            f = r.u32()
            a = r.i16()
            r.u16()
            return ('obj', f, a)
    if ptype == PT_STRING:
        return r.wstr()
    if ptype == PT_INT:
        return r.i32()
    if ptype == PT_FLOAT:
        return r.f32()
    if ptype == PT_BOOL:
        return r.u8()
    if ptype in (PT_ARRAY_OBJECT, PT_ARRAY_STRING, PT_ARRAY_INT,
                 PT_ARRAY_FLOAT, PT_ARRAY_BOOL):
        n = r.u32()
        base = ptype - 10
        return [_read_prop_value(r, base, objfmt) for _ in range(n)]
    raise ValueError('unknown property type %d' % ptype)


def _write_prop_value(w, ptype, objfmt, value):
    if ptype == PT_OBJECT:
        _, f, a = value
        if objfmt == 2:
            w.u16(0)
            w.i16(a)
            w.u32(f)
        else:
            w.u32(f)
            w.i16(a)
            w.u16(0)
        return
    if ptype == PT_STRING:
        w.wstr(value)
        return
    if ptype == PT_INT:
        w.i32(value)
        return
    if ptype == PT_FLOAT:
        w.f32(value)
        return
    if ptype == PT_BOOL:
        w.u8(value)
        return
    if ptype in (PT_ARRAY_OBJECT, PT_ARRAY_STRING, PT_ARRAY_INT,
                 PT_ARRAY_FLOAT, PT_ARRAY_BOOL):
        w.u32(len(value))
        base = ptype - 10
        for v in value:
            _write_prop_value(w, base, objfmt, v)
        return
    raise ValueError('unknown property type %d' % ptype)


class VMAD:
    def __init__(self, version, objfmt, scripts, tail=b''):
        self.version = version
        self.objfmt = objfmt
        self.scripts = scripts
        self.tail = tail          # fragments / alias data, preserved verbatim

    def script(self, name):
        low = name.lower()
        for s in self.scripts:
            if s.name.lower() == low:
                return s
        return None

    def __repr__(self):
        return '<VMAD v%d f%d %r tail=%d>' % (self.version, self.objfmt,
                                              self.scripts, len(self.tail))


def parse(data):
    r = Reader(data)
    version = r.i16()
    objfmt = r.i16()
    count = r.u16()
    scripts = []
    for _ in range(count):
        name = r.wstr()
        status = r.u8()
        np = r.u16()
        props = []
        for _ in range(np):
            pname = r.wstr()
            ptype = r.u8()
            pstatus = r.u8()
            val = _read_prop_value(r, ptype, objfmt)
            props.append(Property(pname, ptype, pstatus, val))
        scripts.append(Script(name, status, props))
    return VMAD(version, objfmt, scripts, data[r.o:])


def build(v):
    w = Writer()
    w.i16(v.version)
    w.i16(v.objfmt)
    w.u16(len(v.scripts))
    for s in v.scripts:
        w.wstr(s.name)
        w.u8(s.status)
        w.u16(len(s.props))
        for p in s.props:
            w.wstr(p.name)
            w.u8(p.ptype)
            w.u8(p.status)
            _write_prop_value(w, p.ptype, v.objfmt, p.value)
    w.raw(v.tail)
    return bytes(w.b)
