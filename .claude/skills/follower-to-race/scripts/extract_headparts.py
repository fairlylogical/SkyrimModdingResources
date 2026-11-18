"""Extract head-part shapes from a follower's FaceGen NIF into standalone SSE head-part NIFs.

usage: python extract_headparts.py <config.json>

config:
{
  "facegen": "<path to FaceGeom/<plugin>/<id>.nif>",
  "out_root": "<patch mod folder>",                 # files go to <out_root>/meshes/<out>
  "parts": [
    {"shape": "SH_Hair",  "out": "actors\\character\\X\\Patch\\hair\\Hair.nif"},                 # neutral: facegen (default)
    {"shape": "SH_Eyes",  "out": "...\\Eyes.nif",  "neutral": {"tri": "<path to base .tri>"}},
    {"shape": "SH_Lash",  "out": "...\\Lash.nif",  "neutral": "nearest"},
    {"shape": "SH_Head",  "out": "...\\head.nif",  "neutral": {"nif": "<standalone head nif>"},
     "diffuse": "textures\\...\\head_makeup.dds"}                                                  # optional texture override
  ],
  "delta_samples": ["SH_Eyes"]     # optional: tri-neutralised shapes whose sculpt offsets drive "nearest" (default: all tri parts)
}

neutral modes - FaceGen geometry has the NPC's sculpt (CK sliders) baked in:
  "facegen"   copy as-is. Right for parts with no .tri (hair): CK does not morph them.
  {"tri": p}  replace vertex positions with the .tri base vertices (same count/order required). Best for eyes/brows.
  "nearest"   subtract the sculpt offset of the nearest vertices of the tri-neutralised parts (lashes, AO layers
              that have no usable tri). Approximation that keeps them aligned with the neutral eyes.
  {"nif": p}  geometry, normals and skinning from a standalone neutral NIF with identical topology; UVs, shader and
              textures from FaceGen (they match the NPC's custom textures). Best for the face/head.
Everything is written as BSDynamicTriShape (required for RaceMenu/chargen morphs in SE).
"""
import json, math, os, struct, sys
sys.path.insert(0, os.path.dirname(__file__))
from tools import setup_pynifly
setup_pynifly()
from pynifly import NifFile, NODEID_NONE
from nifdefs import PynBufferTypes
from trihandler import TriFile

NONE_ID = 0xFFFFFFFF


def to_global(xf, v):
    r, t, s = xf.rotation, xf.translation, xf.scale
    return tuple(t[i] + s * sum(r[i][j] * v[j] for j in range(3)) for i in range(3))


def strip_shader(path):
    """pynifly always creates a shader; for shapes that had none it writes an Oblivion-era
    BSShaderPPLightingProperty, which SSE must not see. Drop that trailing block and null the ref."""
    d = bytearray(open(path, 'rb').read())
    p = d.index(b'\n') + 1 + 9
    nb_off = p; nb, = struct.unpack_from('<I', d, p); p += 8
    for _ in range(3):
        p += 1 + d[p]
    nt_off = p; nt, = struct.unpack_from('<H', d, p); p += 2
    types, toffs = [], []
    for _ in range(nt):
        toffs.append(p); l, = struct.unpack_from('<I', d, p); types.append(d[p + 4:p + 4 + l].decode()); p += 4 + l
    bt = list(struct.unpack_from('<%dH' % nb, d, p)); p += 2 * nb
    bs_off = p; bs = list(struct.unpack_from('<%dI' % nb, d, p)); p += 4 * nb
    ns, _ = struct.unpack_from('<II', d, p); p += 8
    for _ in range(ns):
        l, = struct.unpack_from('<I', d, p); p += 4 + l
    ng, = struct.unpack_from('<I', d, p); p += 4 + 4 * ng
    data0 = p
    names = [types[t] for t in bt]
    si = next(i for i, n in enumerate(names) if n in ('BSDynamicTriShape', 'BSTriShape'))
    q = data0 + sum(bs[:si]) + 4
    ne, = struct.unpack_from('<I', d, q); q += 4 + 4 * ne
    q += 4 + 4 + 12 + 36 + 4 + 4 + 16 + 4
    cut = struct.unpack_from('<i', d, q)[0]           # shader block index; it and everything after must be shader data
    shaderish = {'BSShaderPPLightingProperty', 'BSLightingShaderProperty', 'BSShaderTextureSet', 'NiAlphaProperty'}
    assert cut > si and all(n in shaderish for n in names[cut:]), names
    struct.pack_into('<i', d, q, -1)
    struct.pack_into('<i', d, q + 4, -1)              # alpha property ref too
    keep_types = sorted(set(bt[:cut]))
    remap = {old: new for new, old in enumerate(keep_types)}
    hdr = bytearray(d[:nt_off]) + struct.pack('<H', len(keep_types))
    for t in keep_types:
        hdr += struct.pack('<I', len(types[t])) + types[t].encode()
    hdr += struct.pack('<%dH' % cut, *[remap[t] for t in bt[:cut]]) + struct.pack('<%dI' % cut, *bs[:cut])
    hdr += d[bs_off + 4 * nb:data0]
    struct.pack_into('<I', hdr, nb_off, cut)
    b0 = data0 + sum(bs[:cut]); b1 = data0 + sum(bs)
    open(path, 'wb').write(bytes(hdr + d[data0:b0] + d[b1:]))


def main(cfg):
    fg = NifFile(cfg['facegen'])
    sh = {s.name: s for s in fg.shapes}
    parts = cfg['parts']
    missing = [p['shape'] for p in parts if p['shape'] not in sh]
    if missing:
        sys.exit('shapes not in FaceGen: %s\navailable: %s' % (missing, list(sh)))

    neutral = {}
    for p in parts:
        n = p.get('neutral', 'facegen')
        if isinstance(n, dict) and 'tri' in n:
            base = TriFile.from_file(n['tri']).vertices
            if len(base) != len(sh[p['shape']].verts):
                sys.exit('%s: tri has %d verts, FaceGen shape %d - use "nearest" or "facegen" instead'
                         % (p['shape'], len(base), len(sh[p['shape']].verts)))
            neutral[p['shape']] = [tuple(v) for v in base]

    samples = []
    for name in cfg.get('delta_samples') or list(neutral):
        s = sh[name]
        for fv, nv in zip(s.verts, neutral[name]):
            samples.append((to_global(s.transform, fv), tuple(a - b for a, b in zip(fv, nv))))

    def unmorph(shape, k=4):
        if not samples:
            sys.exit('"nearest" needs at least one tri-neutralised part (delta_samples)')
        out = []
        for v in shape.verts:
            g = to_global(shape.transform, v)
            best = sorted(samples, key=lambda q: (g[0] - q[0][0]) ** 2 + (g[1] - q[0][1]) ** 2 + (g[2] - q[0][2]) ** 2)[:k]
            ws = [1.0 / (math.dist(g, q[0]) + 1e-3) for q in best]
            d = [sum(w * q[1][i] for w, q in zip(ws, best)) / sum(ws) for i in range(3)]
            out.append(tuple(v[i] - d[i] for i in range(3)))
        return out

    ok = True
    for p in parts:
        fgs = sh[p['shape']]
        n = p.get('neutral', 'facegen')
        geo = fgs                                     # source of skin / normals / transform
        if n == 'facegen':
            verts = [tuple(v) for v in fgs.verts]
        elif n == 'nearest':
            verts = unmorph(fgs)
        elif 'tri' in n:
            verts = neutral[p['shape']]
        elif 'nif' in n:
            src = NifFile(n['nif'])
            geo = next((s for s in src.shapes if s.name == n.get('shape')), src.shapes[0])
            if geo.tris != fgs.tris or len(geo.verts) != len(fgs.verts):
                sys.exit('%s: %s has different topology than the FaceGen shape' % (p['shape'], n['nif']))
            verts = [tuple(v) for v in geo.verts]
        else:
            sys.exit('bad neutral mode %r' % n)

        dst = os.path.join(cfg['out_root'], 'meshes', p['out'])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        nif = NifFile(); nif.initialize('SKYRIMSE', dst, 'NiNode', 'Scene Root')
        props = fgs.properties.copy()
        props.nameID = props.conrollerID = props.collisionID = NODEID_NONE
        props.skinInstanceID = props.shaderPropertyID = props.alphaPropertyID = NODEID_NONE
        # pynifly inverts V on write; feed it 1-v so the file matches the source
        ns = nif.createShapeFromData(p['shape'], verts, fgs.tris, [(x, 1 - y) for x, y in fgs.uvs], geo.normals,
                                     props=props, use_type=PynBufferTypes.BSDynamicTriShapeBufType)
        if fgs.colors:
            ns.set_colors(fgs.colors)
        ns.transform = geo.transform.copy()
        ns.set_global_to_skin(geo.global_to_skin)
        for bn in geo.bone_weights:
            ns.add_bone(bn, geo.file.nodes[bn].global_transform)
        for bn, w in geo.bone_weights.items():
            ns.set_skin_to_bone_xform(bn, geo.get_shape_skin_to_bone(bn))
            ns.setShapeWeights(bn, w)
        # partition_tris holds indices into the partition list; set_partitions wants partition IDs
        ns.set_partitions(geo.partitions, [geo.partitions[i].id for i in geo.partition_tris])
        has_shader = fgs.properties.shaderPropertyID != NONE_ID
        if has_shader:
            ns.shader_name = fgs.shader_name
            ns.shader.properties.bufType = fgs.shader.properties.bufType
            fgs.shader.properties.copyto(ns.shader.properties)
            ns.save_shader_attributes()
            if fgs.has_alpha_property:
                ns.has_alpha_property = True
                ns.alpha_property.properties.flags = fgs.alpha_property.properties.flags
                ns.alpha_property.properties.threshold = fgs.alpha_property.properties.threshold
                ns.save_alpha_property()
            for k, t in fgs.textures.items():
                if t:
                    ns.set_texture(k, t)
            if p.get('diffuse'):
                ns.set_texture('Diffuse', p['diffuse'])
        nif.save()
        if not has_shader:
            strip_shader(dst)

        # ---- verify by reloading
        s = NifFile(dst).shapes[0]
        uvd = max(max(abs(a - b) for a, b in zip(u, w)) for u, w in zip(s.uvs, fgs.uvs))
        exp_tex = {k: v.lower() for k, v in fgs.textures.items() if v} if has_shader else {}
        if p.get('diffuse') and has_shader:
            exp_tex['Diffuse'] = p['diffuse'].lower()
        checks = {
            'tris': s.tris == fgs.tris,
            'uvs': uvd < 1e-3,
            'textures': {k: v.lower() for k, v in s.textures.items() if v} == exp_tex,
            'partitions': [q.id for q in s.partitions] == [q.id for q in geo.partitions],
            'bones': sorted(s.bone_weights) == sorted(geo.bone_weights),
            'shader': (s.properties.shaderPropertyID != NONE_ID) == has_shader,
            'alpha': s.has_alpha_property == (fgs.has_alpha_property and has_shader),
        }
        if has_shader:
            checks['shader_flags'] = (s.shader.properties.Shader_Type, s.shader.properties.Shader_Flags_1, s.shader.properties.Shader_Flags_2) == \
                                     (fgs.shader.properties.Shader_Type, fgs.shader.properties.Shader_Flags_1, fgs.shader.properties.Shader_Flags_2)
        shift = max(max(abs(a - b) for a, b in zip(u, w)) for u, w in zip(s.verts, fgs.verts))
        bad = [k for k, v in checks.items() if not v]
        ok &= not bad
        print('%-28s -> %-40s %-8s shift-from-FaceGen=%.3f %s' % (p['shape'], os.path.basename(dst),
              n if isinstance(n, str) else list(n)[0], shift, 'OK' if not bad else 'FAILED %s' % bad))
    print('all parts verified' if ok else 'SOME PARTS FAILED VERIFICATION')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(json.load(open(sys.argv[1], encoding='utf-8')))
