"""Bake a skinned head-part shape's own transform into its vertices (shape transform and overall skin transform
become identity; per-bone skin-to-bone is recomputed so the skinned result is unchanged).

Why: Skyrim's head-part assembly misplaces head parts whose BSTriShape has a non-zero transform, even when the
skin data compensates for it mathematically (e.g. LDD/CVEO lash meshes: local verts + a +120 shape translation).
Parts with an identity shape transform (all FaceGen-extracted parts, vanilla brows) render where expected.

usage: python normalize_headpart.py <in.nif> <out.nif>
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from tools import setup_pynifly
setup_pynifly()
from pynifly import NifFile, NODEID_NONE
from nifdefs import PynBufferTypes, TransformBuf


def M4(x):
    m = np.eye(4)
    m[:3, :3] = np.array([[x.rotation[i][j] for j in range(3)] for i in range(3)]) * x.scale
    m[:3, 3] = np.array(x.translation[:])
    return m


def to_buf(m):
    b = TransformBuf()
    s = float(np.cbrt(abs(np.linalg.det(m[:3, :3]))))
    r = m[:3, :3] / s
    for i in range(3):
        for j in range(3):
            b.rotation[i][j] = float(r[i][j])
        b.translation[i] = float(m[i, 3])
    b.scale = s
    return b


def normalize(src, dst):
    old = NifFile(src).shapes[0]
    T = M4(old.transform)
    v = np.c_[np.array(old.verts), np.ones(len(old.verts))] @ T.T
    verts = [tuple(p[:3]) for p in v]
    R = T[:3, :3] / np.cbrt(abs(np.linalg.det(T[:3, :3])))
    normals = [tuple(R @ np.array(n)) for n in old.normals] if old.normals else None

    nif = NifFile(); nif.initialize('SKYRIMSE', dst, 'NiNode', 'Scene Root')
    props = old.properties.copy()
    props.nameID = props.conrollerID = props.collisionID = NODEID_NONE
    props.skinInstanceID = props.shaderPropertyID = props.alphaPropertyID = NODEID_NONE
    ns = nif.createShapeFromData(old.name, verts, old.tris, [(x, 1 - y) for x, y in old.uvs], normals,
                                 props=props, use_type=PynBufferTypes.BSDynamicTriShapeBufType)
    if old.colors:
        ns.set_colors(old.colors)
    ns.transform = to_buf(np.eye(4))
    ns.set_global_to_skin(to_buf(np.eye(4)))
    Tinv = np.linalg.inv(T)
    for bn in old.bone_weights:
        ns.add_bone(bn, old.file.nodes[bn].global_transform)
    for bn, w in old.bone_weights.items():
        ns.set_skin_to_bone_xform(bn, to_buf(M4(old.get_shape_skin_to_bone(bn)) @ Tinv))   # STB' v' = STB v
        ns.setShapeWeights(bn, w)
    ns.set_partitions(old.partitions, [old.partitions[i].id for i in old.partition_tris])
    ns.shader_name = old.shader_name
    ns.shader.properties.bufType = old.shader.properties.bufType
    old.shader.properties.copyto(ns.shader.properties)
    ns.save_shader_attributes()
    if old.has_alpha_property:
        ns.has_alpha_property = True
        ns.alpha_property.properties.flags = old.alpha_property.properties.flags
        ns.alpha_property.properties.threshold = old.alpha_property.properties.threshold
        ns.save_alpha_property()
    for k, t in old.textures.items():
        if t:
            ns.set_texture(k, t)
    nif.save()

    # verify: skinned positions (bone * STB * v) unchanged, transforms now identity
    new = NifFile(dst).shapes[0]
    def skinned(s):
        out = np.zeros((len(s.verts), 3)); ws = np.zeros(len(s.verts))
        vv = np.c_[np.array(s.verts), np.ones(len(s.verts))]
        for bn, wl in s.bone_weights.items():
            p = vv @ (M4(s.file.nodes[bn].global_transform) @ M4(s.get_shape_skin_to_bone(bn))).T
            for i, w in wl:
                out[i] += w * p[i, :3]; ws[i] += w
        return out / np.maximum(ws, 1e-9)[:, None]
    d = np.abs(skinned(old) - skinned(new)).max()
    same = new.tris == old.tris and max(max(abs(a - b) for a, b in zip(u, x)) for u, x in zip(new.uvs, old.uvs)) < 1e-4
    print('%s: skinned-position change %.5f | topology/UVs same %s | shape xf t=%s | textures %s' % (
        os.path.basename(dst), d, same, np.round(new.transform.translation[:], 4), {k: x for k, x in new.textures.items() if x}))
    return d < 1e-3 and same


if __name__ == '__main__':
    sys.exit(0 if normalize(sys.argv[1], sys.argv[2]) else 1)
