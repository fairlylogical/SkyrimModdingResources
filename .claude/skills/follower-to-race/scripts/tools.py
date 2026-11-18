"""Shared helpers: locate pynifly (from the Blender PyNifly add-on) and texconv."""
import glob, os, shutil, sys


def setup_pynifly():
    """Put the PyNifly add-on on sys.path and load NiflyDLL. Returns the add-on directory.
    Override with env var PYNIFLY_DIR if it lives somewhere unusual."""
    cands = []
    if os.environ.get('PYNIFLY_DIR'):
        cands.append(os.environ['PYNIFLY_DIR'])
    appdata = os.environ.get('APPDATA', '')
    cands += sorted(glob.glob(os.path.join(appdata, 'Blender Foundation', 'Blender', '*', 'scripts', 'addons', 'io_scene_nifly')),
                    key=lambda p: [int(x) if x.isdigit() else 0 for x in p.split(os.sep)[-4].split('.')], reverse=True)
    for d in cands:
        if os.path.exists(os.path.join(d, 'NiflyDLL.dll')) and os.path.exists(os.path.join(d, 'pynifly.py')):
            sys.path.insert(0, d)
            import logging
            logging.basicConfig(level=logging.WARNING)
            logging.getLogger().setLevel(logging.WARNING)
            logging.getLogger('pynifly').setLevel(logging.WARNING)
            from pynifly import NifFile
            NifFile.Load(os.path.join(d, 'NiflyDLL.dll'))
            return d
    sys.exit('PyNifly not found. Install the Blender PyNifly add-on or set PYNIFLY_DIR to its io_scene_nifly folder.')


def find_texconv(explicit=None):
    """texconv.exe (DirectXTex). Ships with Cathedral Assets Optimizer, among others."""
    if explicit and os.path.exists(explicit):
        return explicit
    if os.environ.get('TEXCONV') and os.path.exists(os.environ['TEXCONV']):
        return os.environ['TEXCONV']
    p = shutil.which('texconv') or shutil.which('texconv.exe')
    if p:
        return p
    for pat in [r'D:\SkyrimMod\*\Tools\texconv.exe', r'C:\Modding\**\texconv.exe', r'D:\Modding\**\texconv.exe']:
        hits = sorted(glob.glob(pat, recursive=True), reverse=True)
        if hits:
            return hits[0]
    sys.exit('texconv.exe not found. Pass --texconv or set TEXCONV.')


class LooseFiles:
    """Case-insensitive index of loose files under one or more mod roots (folders containing meshes/, textures/)."""
    def __init__(self, roots):
        self.idx = {}
        for r in roots:
            for dp, _, fs in os.walk(r):
                for f in fs:
                    full = os.path.join(dp, f)
                    rel = os.path.relpath(full, r).replace('/', '\\').lower()
                    self.idx.setdefault(rel, full)   # first root wins

    def find(self, rel, prefix=''):
        """rel as stored in plugins (e.g. 'actors\\character\\x.nif'); prefix 'meshes' or 'textures'."""
        if not rel:
            return None
        rel = rel.replace('/', '\\').lower()
        if prefix and not rel.startswith(prefix + '\\'):
            rel = prefix + '\\' + rel
        return self.idx.get(rel)
