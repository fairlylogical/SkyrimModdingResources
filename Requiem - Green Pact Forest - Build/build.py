"""Builds the "Requiem - Green Pact Forest" patch mod from scratch.

  python build.py

Writes the plugin, compiles the two scripts, generates the KID config and
lays everything out as an MO2 mod folder.
"""
import json
import os
import shutil
import struct
import subprocess

from common import (COMPILER, FLAGS, HEADERS, MODS, REQUIEM, SKSE_SRC,
                    load_groups, tes4)
import vmad

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = 'Requiem - Green Pact Forest'
OUT = os.path.join(MODS, NAME)
MASTERS = ['Skyrim.esm', 'Requiem.esp']
OWN = len(MASTERS) << 24
REQ = MASTERS.index('Requiem.esp') << 24

PLAYER_REF = 0x00000014
REQ_FOLLOWS_GREEN_PACT = REQ | 0xAE3B6A

KYWD_FORBIDDEN = OWN | 0x800
MESG_FORBIDDEN = OWN | 0x801
FLST_HARVESTABLES = OWN | 0x802
PERK_FORBID = OWN | 0x803
QUST_MAIN = OWN | 0x804
NEXT_ID = 0x805

FN_GETGLOBALVALUE = 74
FN_ISINLIST = 372
ENTRY_ACTIVATE = 14
FUNC_ADD_ACTIVATE_CHOICE = 9
EPF_RUN_IMMEDIATELY = 1
EPF_REPLACE_DEFAULT = 2

FORM_VERSION = 44
ESL = 0x200


def zs(s):
    return s.encode('cp1252') + b'\x00'


def record(sig, formid, subs):
    return tes4.Record(sig, 0, formid, (0, 0, FORM_VERSION, 0),
                       [[s, d] for s, d in subs])


def group(sig, records):
    return tes4.Group(sig, 0, (0, 0, 0, 0), records)


def ctda(function, param1, value=1.0):
    # op 0 = "equal to", AND, run on subject
    return struct.pack('<B3sfHHIIIIi', 0, b'\x00\x00\x00', value, function, 0,
                       param1, 0, 0, 0, -1)


def obj_prop(name, formid):
    return vmad.Property(name, vmad.PT_OBJECT, 1, ('obj', formid, -1))


def perk_vmad():
    script = 'GPF_PRKF_ForbidHarvest'
    w = vmad.Writer()
    w.i8(2)                 # fragment data version
    w.wstr(script)          # fragment file
    w.u16(1)                # fragment count
    w.u16(0)                # fragment index (EPF3 refers to it)
    w.i16(0)
    w.i8(1)
    w.wstr(script)
    w.wstr('Fragment_0')
    props = [obj_prop('ForbiddenMessage', MESG_FORBIDDEN)]
    return vmad.build(vmad.VMAD(5, 2, [vmad.Script(script, 0, props)],
                                bytes(w.b)))


def quest_vmad():
    w = vmad.Writer()
    w.i8(2)                 # fragment data version
    w.u16(0)                # no stage fragments
    w.wstr('')
    w.u16(1)                # one alias with scripts
    w.u16(0)
    w.i16(0)                # alias id
    w.u32(QUST_MAIN)
    alias = vmad.VMAD(5, 2, [vmad.Script('GPF_PlayerAlias', 0, [
        obj_prop('GreenPactForbidden', KYWD_FORBIDDEN),
        obj_prop('ForbiddenHarvestables', FLST_HARVESTABLES),
        obj_prop('ForbidHarvestPerk', PERK_FORBID),
        obj_prop('FollowsGreenPact', REQ_FOLLOWS_GREEN_PACT),
    ])])
    w.raw(vmad.build(alias))
    return vmad.build(vmad.VMAD(5, 2, [], bytes(w.b)))


def build_plugin():
    keyword = record(b'KYWD', KYWD_FORBIDDEN, [
        (b'EDID', zs('GreenPactForbidden')),
        (b'CNAM', struct.pack('<I', 0)),
    ])
    message = record(b'MESG', MESG_FORBIDDEN, [
        (b'EDID', zs('GPF_Message_Forbidden')),
        (b'DESC', zs('The Green Pact forbids you to harm the forest.')),
        (b'INAM', struct.pack('<I', 0)),
        (b'DNAM', struct.pack('<I', 0)),     # not a message box
        (b'TNAM', struct.pack('<I', 2)),
    ])
    formlist = record(b'FLST', FLST_HARVESTABLES, [
        (b'EDID', zs('GPF_ForbiddenHarvestables')),
    ])
    perk = record(b'PERK', PERK_FORBID, [
        (b'EDID', zs('GPF_Perk_ForbidHarvest')),
        (b'VMAD', perk_vmad()),
        (b'FULL', zs('Green Pact: Do Not Harm the Forest')),
        (b'DESC', zs('')),
        (b'DATA', bytes([0, 0, 1, 0, 1])),   # 1 rank, not playable, hidden
        (b'PRKE', bytes([2, 0, 0])),         # entry point, rank 0, priority 0
        (b'DATA', bytes([ENTRY_ACTIVATE, FUNC_ADD_ACTIVATE_CHOICE, 2])),
        (b'PRKC', b'\x00'),                  # perk owner
        (b'CTDA', ctda(FN_GETGLOBALVALUE, REQ_FOLLOWS_GREEN_PACT)),
        (b'PRKC', b'\x01'),                  # activated object
        (b'CTDA', ctda(FN_ISINLIST, FLST_HARVESTABLES)),
        (b'EPFT', b'\x04'),
        (b'EPF3', struct.pack('<HH',
                              EPF_RUN_IMMEDIATELY | EPF_REPLACE_DEFAULT, 0)),
        (b'PRKF', b''),
    ])
    quest = record(b'QUST', QUST_MAIN, [
        (b'EDID', zs('GPF_Quest')),
        (b'VMAD', quest_vmad()),
        (b'FULL', zs('Green Pact: Do Not Harm the Forest')),
        # start game enabled, run once - same bytes as Requiem's own
        # player-alias quests
        (b'DNAM', bytes.fromhex('110100ff0000000000000000')),
        (b'NEXT', b''),
        (b'ANAM', struct.pack('<I', 1)),
        (b'ALST', struct.pack('<I', 0)),
        (b'ALID', zs('Player')),
        (b'FNAM', struct.pack('<I', 0)),
        (b'ALFR', struct.pack('<I', PLAYER_REF)),
        (b'VTCK', struct.pack('<I', 0)),
        (b'ALED', b''),
    ])

    plugin = tes4.Plugin()
    plugin.nodes = [group(b'KYWD', [keyword]), group(b'QUST', [quest]),
                    group(b'FLST', [formlist]), group(b'PERK', [perk]),
                    group(b'MESG', [message])]
    head = [[b'HEDR', struct.pack('<fII', 1.7, plugin.count_records(), NEXT_ID)],
            [b'CNAM', zs('Green Pact Forest')],
            [b'SNAM', zs('Bosmer who follow the Green Pact cannot harvest '
                         'anything that yields an item with the '
                         'GreenPactForbidden keyword.')]]
    for m in MASTERS:
        head.append([b'MAST', zs(m)])
        head.append([b'DATA', struct.pack('<Q', 0)])
    plugin.tes4 = tes4.Record(b'TES4', ESL, 0, (0, 0, FORM_VERSION, 0), head)
    return plugin


def check_assumptions():
    """The two things taken from Requiem.esp rather than from this build."""
    g = load_groups(REQUIEM, ['GLOB', 'FLST', 'PERK', 'MGEF', 'SPEL'])
    own = None
    for r in g[b'GLOB']:
        if r.editor_id == 'REQ_GV_FollowsGreenPact':
            own = r.formid
    assert (own is not None
            and own & 0xFFFFFF == REQ_FOLLOWS_GREEN_PACT & 0xFFFFFF), own
    lists = {r.formid for r in g[b'FLST']}
    hits = 0
    for sig in (b'PERK', b'MGEF', b'SPEL'):
        for r in g[sig]:
            for d in r.get_all('CTDA'):
                fn, p1 = struct.unpack_from('<H', d, 8)[0], tes4.u32(d, 12)
                if fn == FN_ISINLIST and p1 >> 24 == own >> 24:
                    assert p1 in lists, hex(p1)
                    hits += 1
    assert hits, 'no IsInList condition found to check the function index'


def compile_scripts(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    imports = ';'.join([os.path.join(HERE, 'source'), os.path.join(HERE, 'psc'),
                        HEADERS, SKSE_SRC])
    r = subprocess.run([COMPILER, os.path.join(HERE, 'source'), '-i=' + imports,
                        '-o=' + out_dir,
                        '-f=' + FLAGS,
                        '-all'], capture_output=True, text=True)
    print(r.stdout + r.stderr)
    for s in ('GPF_PlayerAlias', 'GPF_PRKF_ForbidHarvest'):
        assert os.path.isfile(os.path.join(out_dir, s + '.pex')), s


# --- KID config ---------------------------------------------------------------
# (switched on, heading, EditorIDs) - None stands for the Hearthfire planters
SECTIONS = [
    (True, 'Wild plants', [
        'CanisRoot01', 'CreepClusterRoot', 'deathBell', 'DragonsTongue',
        'HangingMoss', 'JazBay', 'JuniperBerries', 'Lavender',
        'MountainFlower01Blue', 'MountainFlower01Purple', 'MountainFlower01Red',
        'Nightshade', 'Snowberry', 'SpikyGrass01', 'Thistle01', 'TundraCotton',
        'DLC1MountainFlower01Yellow', 'DLC01GlowPlant01Ingredient',
        'DLC2AshCreepCluster', 'DLC2HangingMoss', 'DLC2Scathecraw01',
        'DLC2SpikyGrassAsh01', 'DLC2TramaRoot01',
        'ccBGS_RootRotScaleIngredient', 'ccBGS_RootScreamingMawIngredient',
        'ccBGS_RootThornHookIngredient']),
    (True, 'Crops', [
        'Wheat', 'REQ_Food_Vegan_Cabbage', 'REQ_Food_Vegan_Gourd',
        'REQ_Food_Vegan_LeekRaw', 'REQ_Food_Vegan_PotatoRaw',
        'REQ_Food_Vegan_AshYam']),
    (False, 'Nirnroot. Vanilla nirnroot is an activator rather than a plant, so\n'
            '; the activators are marked directly; the ingredients cover mods that\n'
            '; turn it into a regular plant.\n'
            '; Switching these on blocks "A Return To Your Roots".', [
        'Nirnroot', 'NirnrootRed', 'TreeFloraNirnroot01',
        'TreeFloraNirnrootRed01']),
    (False, 'Fungi and lichen', [
        'Mushroom01', 'Mushroom02', 'Mushroom03', 'Mushroom04', 'Mushroom05',
        'Mushroom06', 'GlowingMushroom', 'MoraTapinellaBits',
        'ScalyPholiotaBits', 'SwampFungalPod01', 'GiantLichen',
        'DLC1FoodSoulHusk']),
    (False, 'Plants somebody else already cut and hung up to dry', [
        'ElvesEar', 'FrostMirriam', 'Garlic']),
    (False, 'Hearthfire planters (they yield a token, not the plant itself)',
     None),
    (True, 'Chopping wood', [
        'WoodChoppingBlock', 'WoodChoppingBlockSnow',
        'DLC2WoodChoppingBlockAsh', 'WoodChoppingBlockCOPY0000']),
    (False, 'Canticle bark. The Dawnguard main quest needs it.', [
        'DLC1CanticleBarkFake']),
]

KID_HEADER = """\
; Requiem - Green Pact Forest
;
; A Bosmer who follows the Green Pact cannot harvest anything that yields an
; item carrying the GreenPactForbidden keyword. This file decides which items
; those are.
;
;   Keyword = GreenPactForbidden|<type>|<item>
;
; <type> is Ingredient, Potion (food) or Misc Item for whatever the plant
; yields. A harvestable can also be marked directly with Flora, Activator or
; Furniture; that is the only way for things that yield nothing by themselves.
; <item> is 0xFormID~Plugin.esp, or an EditorID.
;
; Lines starting with ; are switched off. Remove the ; to switch them on.
"""


def write_kid(path):
    # kid_items.json maps the EditorIDs used above to KID type, plugin and id
    with open(os.path.join(HERE, 'kid_items.json')) as f:
        items_by_edid = json.load(f)
    lines = [KID_HEADER]
    for enabled, title, items in SECTIONS:
        lines.append('; --- %s ---' % title)
        for edid in (items_by_edid['_planters'] if items is None else items):
            item = items_by_edid[edid]
            entry = 'Keyword = GreenPactForbidden|%s|%s~%s' % (
                item['type'], item['id'], item['plugin'])
            lines.append('; ' + edid)
            lines.append(entry if enabled else ';' + entry)
        lines.append('')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines))


def main():
    check_assumptions()
    os.makedirs(OUT, exist_ok=True)
    plugin = build_plugin()
    esp = os.path.join(OUT, NAME + '.esp')
    plugin.save(esp)
    assert tes4.Plugin(esp).to_bytes() == plugin.to_bytes()
    compile_scripts(os.path.join(OUT, 'Scripts'))
    src = os.path.join(OUT, 'Source', 'Scripts')
    os.makedirs(src, exist_ok=True)
    for f in os.listdir(os.path.join(HERE, 'source')):
        shutil.copy2(os.path.join(HERE, 'source', f), src)
    write_kid(os.path.join(OUT, NAME + '_KID.ini'))
    print('built', OUT)


if __name__ == '__main__':
    main()
