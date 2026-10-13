"""Shared paths and a fast single-group loader for the big master files.

Machine-specific: adjust the paths below to your own setup. HEADERS must hold
.psc headers for the vanilla script types (the SKSE sources cover only some of
them) and the Papyrus flags file.
"""
import os, struct
import tes4

DATA = r'D:\SkyrimMod\wabbajack\Stock Game\Data'
MODS = r'D:\SkyrimMod\wabbajack\mods'
REQUIEM = os.path.join(MODS, 'Requiem - The Roleplaying Overhaul', 'Requiem.esp')
COMPILER = r'D:\SkyrimMod\wabbajack\Stock Game\Papyrus Compiler\PapyrusCompiler.exe'
SKSE_SRC = os.path.join(MODS, 'Skyrim Script Extender (SKSE64) - Scripts',
                        'Scripts', 'Source')
HEADERS = r'D:\SkyrimMod\tutos\lawbringer_thalmor_build\psc'
FLAGS = r'D:\SkyrimMod\tutos\lawbringer_thalmor_build\TESV_Papyrus_Flags.flg'


def load_groups(path, sigs):
    """Return {sig: [Record, ...]} reading only the named top-level groups."""
    sigs = {s.encode() if isinstance(s, str) else s for s in sigs}
    out = {s: [] for s in sigs}
    with open(path, 'rb') as f:
        hdr = f.read(24)
        _t, dsize = struct.unpack_from('<4sI', hdr)
        f.seek(24 + dsize)
        while True:
            h = f.read(24)
            if len(h) < 24:
                break
            _g, gsize, label, gtype = struct.unpack_from('<4sI4sI', h)
            if gtype == 0 and label in sigs:
                buf = h + f.read(gsize - 24)
                grp = tes4._read_nodes(buf, 0, len(buf))[0]
                stack = [grp]
                while stack:
                    g = stack.pop()
                    for it in g.items:
                        if isinstance(it, tes4.Group):
                            stack.append(it)
                        else:
                            out[label].append(it)
            else:
                f.seek(gsize - 24, 1)
    return out
