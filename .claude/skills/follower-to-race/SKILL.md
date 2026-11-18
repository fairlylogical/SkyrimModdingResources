---
name: follower-to-race
description: Convert a Skyrim Special Edition follower/NPC replacer's custom head assets (hair, eyes, head/face, brows, lashes, FaceGen makeup, body skin) into assets a player race can use in RaceMenu - either by patching an existing custom race or by creating a new playable race cloned from a vanilla one. Use this whenever the user wants a follower's or NPC overhaul's (Serana, Lydia, any custom follower) hair, eyes, face or makeup on their player character or on a custom race, says a follower's hair/eyes "don't show up in RaceMenu", wants to "make a race out of a follower", or wants a patch between a follower replacer and a custom race mod - even if they don't mention FaceGen, head parts or plugins.
---

# Follower head assets -> player race

Followers look right in game because the Creation Kit bakes their whole head into one **FaceGen** mesh
(`meshes/actors/character/FaceGenData/FaceGeom/<origin plugin>/<FormID>.nif`) plus a **tint** texture.
Players don't use FaceGen: RaceMenu builds the head at runtime from separate **head-part (HDPT)** records,
each pointing at its own standalone mesh and limited to races in its **valid-races FormList**. Follower mods
often ship standalone meshes that are missing, placeholders, or never set up, because the author only needed FaceGen.
So the job is: recover real standalone meshes from FaceGen, then write a patch plugin that lets the race use them.

`references/engine-notes.md` explains the record and shader details behind every step - read it when
something behaves unexpectedly or a case doesn't fit the defaults below.

## Requirements

- Python 3 with `numpy` and `Pillow`; the Blender **PyNifly** add-on installed (scripts find it under
  `%APPDATA%\Blender Foundation\Blender\*\scripts\addons\io_scene_nifly`, or set `PYNIFLY_DIR`).
- `texconv.exe` for the makeup step (ships with Cathedral Assets Optimizer; pass `--texconv` or set `TEXCONV`).
- Loose files. If the follower's meshes/textures are in a BSA, extract them first (e.g. BAE).

Scripts live in `scripts/` next to this file. `examples/` holds the complete configs from a real conversion
(Serana -> SC_DAI Morrigan race, and the same follower as a new Nord-based race) - copy and adapt them. Write configs and helper scripts with the Write tool rather than
shell heredocs: Git Bash on Windows mangles backslashes in heredocs, which silently breaks Windows paths.
Run Python with `-I`.

## Workflow

### 1. Clarify the target
Ask (if not obvious) which follower/plugin, and whether to **(A)** patch an existing custom race (e.g. a race
mod the user already uses) or **(B)** create a new playable race (cloned from a vanilla race, usually the follower's
own race - `NordRace` for Serana). Put output in a new mod folder (MO2: `<instance>\mods\<Name> Patch`),
never inside the source mods.

### 2. Reconnaissance
```
python -I scripts/inspect_follower.py --plugin "<follower.esp>" --mod-dir "<follower mod folder>"
       [--npc <EDID>] [--race-plugin "<race.esp>" --race <RaceEDID>] [--data "<game Data>"]
```
It prints the NPC's head parts (with HNAM extra parts), each part's model/tri and whether they exist,
whether each standalone mesh matches the FaceGen shape's topology (flags placeholders), tri vertex counts vs
FaceGen, the FaceGen shapes (names, vertex counts, shader presence), the FaceGen tint path, and - for a target
race - its default head parts and tint layers. Also check the MO2 profiles: the patch needs the follower mod and
the race mod enabled together.

Read the output and decide, per head part:
- **Mesh source.** If the standalone mesh is missing or `DOES NOT match FaceGen`, extract from FaceGen.
  If it matches (often head and brows), it can be reused - but check its textures: authors often leave
  vanilla or other-mod texture paths in it because FaceGen carried the real ones.
- **Neutral pose.** FaceGen geometry has the NPC's sculpt baked in; a player part must be neutral or it
  misaligns with the player's face:
  - parts with no `.tri` (hair, most hats/extras) -> `facegen` (CK doesn't morph them, already neutral)
  - eyes/brows/etc. whose `.tri` vertex count matches -> `{"tri": path}` (tri base = neutral)
  - small parts without a usable tri (lashes, AO/shadow layers) -> `nearest` (borrows the eyes' offsets)
  - the face itself -> `{"nif": standalone head}` when a neutral head with identical topology exists; it keeps
    FaceGen's UVs/shader/textures (the custom face textures were painted for those UVs)
- **Record fixes.** `drop_tri` when the tri file is missing or its vertex count differs from the mesh (a mismatched
  tri can corrupt morphs); `drop_tnam` when the part's texture set points at missing files (the extracted mesh
  already carries FaceGen's correct textures); `playable` for main parts the user should pick (hair, eyes, brows, face).
  FaceGen shape names can differ from HDPT EditorIDs (e.g. `SH_SeranaEyeAO2` vs `SH_Serana_EyesAO2`) - map them by hand.

### 3. Extract meshes
Write a config (schema at the top of `scripts/extract_headparts.py`) and run
`python -I scripts/extract_headparts.py extract.json`. Put meshes under a new subfolder of the follower's
mesh path (e.g. `actors\character\<follower folder>\<Race>Patch\...`) so they never overwrite the follower's files.
The script writes SE-ready `BSDynamicTriShape` NIFs and re-verifies each against FaceGen (topology, UVs,
textures, shader flags, alpha, partitions, bones). Eye shifts of ~1 unit and hair shifts of 0 are normal; a
`FAILED` line is not - fix it before continuing.

### 4. Makeup (optional, usually wanted)
RaceMenu can't reproduce hand-painted FaceGen makeup unless the race has matching tint-mask layers (many custom
races have only SkinTone - inspect prints the count). Bake it into the head diffuse instead:
```
python -I scripts/bake_makeup.py --tint "<FaceTint dds>" --diffuse "<head diffuse dds>"
       --out "<patch>\textures\...\head_makeup.dds" --preview "<png>"
```
Then point the head part at it with `"diffuse"` in the extract config (re-run that part). Look at the preview
image before moving on. Defaults strip the NPC's base complexion so RaceMenu's skin tone still works; use
`--keep-skin-tone` to bake it too and `--strength` to tone makeup down. If the follower's installer offered several
makeup variants, they're usually alternate FaceTint files - bake the one the user installed (compare hashes) or ask.

### 5. Build the plugin
Write a config (schema at the top of `scripts/build_patch.py`) and run `python -I scripts/build_patch.py patch.json`.
It produces an ESL-flagged ESP that:
- overrides the listed head parts (HNAM extras are pulled in automatically) with new model paths, flags and fixes;
- points their valid-races lists at **new** FormLists = original contents + target race (editing vanilla lists
  would conflict with other race mods);
- sets the race's default head parts by type (`race_defaults`) - **required for the face**: RaceMenu has no head-mesh
  picker, so the head always comes from the race defaults. Hair/eyes/brows become pickable anyway; making them
  defaults is optional;
- optionally adds the race to the follower's skin armor addons (`skin_arma`);
- for a new race: clones the source race, renames it, sets Playable, sets Armor Race to the clone source (vanilla
  armor works without extra mods) and writes a Race Compatibility SKSE json (proxies for dialogue/vampirism/
  vanilla head parts).

Dump the result to sanity-check if anything looks off (the reconnaissance helpers in `esp_lib.py` parse plugins).

### 6. Tell the user how to apply it
- Enable the follower mod, the race mod and the patch; the patch must load after both (and after anything else
  that edits that race).
- Existing characters keep their saved head: in RaceMenu (`showracemenu`) switch to another race and back to
  reload race defaults - this resets sliders, so suggest saving a RaceMenu preset first. Then pick the follower's
  hair/eyes/brows from the lists.
- NPCs of that race need FaceGen regenerated in the CK to show the new parts; players don't.
- Mention honest caveats: hair was fitted to the follower's head and may clip on very different head shapes;
  `nearest`-neutralised parts are approximations; baked makeup can't be removed in RaceMenu.

## Output summary to give the user
List the new mod folder, what each part became (extracted / reused / fixed), what the plugin changes,
load-order and in-game steps, and anything not verified in game. Keep the configs in the patch's source
folder or the user's chosen location if they may want to rebuild (e.g. after switching makeup variant).
