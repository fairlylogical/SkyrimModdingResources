---
name: follower-to-race
description: Convert a Skyrim Special Edition follower/NPC replacer's custom head assets (hair, eyes, head/face, brows, lashes, FaceGen makeup, body skin) into assets a player race can use in RaceMenu - by patching an existing custom race, creating a new playable race cloned from a vanilla one, or building a fully standalone race mod (own copies of every asset, optional gameplay from e.g. Requiem's races). Also covers body-skin swaps without seams and fixing head parts that look displaced after RaceMenu sculpt/preset reloads. Use this whenever the user wants a follower's or NPC overhaul's (Serana, Lydia, any custom follower) hair, eyes, face or makeup on their player character or on a custom race, says a follower's hair/eyes "don't show up in RaceMenu", wants to "make a race out of a follower", or wants a patch between a follower replacer and a custom race mod - even if they don't mention FaceGen, head parts or plugins.
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
(Serana -> SC_DAI Morrigan race, and the same follower as a new Nord-based race) - copy and adapt them.
`examples/blood_scion_standalone/` is the full standalone build (mode C: Morrigan race body + Requiem Breton
gameplay + Serana's head, Skyrim.esm + Requiem.esp masters only), plus the script that writes a RaceMenu preset
equivalent to importing the follower's FaceGen NIF. Their paths are the author's - adapt them. Write configs and helper scripts with the Write tool rather than
shell heredocs: Git Bash on Windows mangles backslashes in heredocs, which silently breaks Windows paths.
Run Python with `-I`.

## Workflow

### 1. Clarify the target
Ask (if not obvious) which follower/plugin, and whether to **(A)** patch an existing custom race (e.g. a race
mod the user already uses), **(B)** create a new playable race (cloned from a vanilla race, usually the follower's
own race - `NordRace` for Serana), or **(C)** build a standalone mod that needs neither the follower nor the race
mod (step 5b). Put output in a new mod folder (MO2: `<instance>\mods\<Name> Patch`),
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
  - eyes/brows/etc. whose `.tri` vertex count matches -> `{"tri": path}` (tri base = neutral) - but some tris
    (the head's, Expressive Facial Animation's `EyesFemale.tri`) are in head-bone space; extraction now fails any
    part shifted >= 25 units. For LDD/CVEO eyes and lashes use `{"nif": <CVEO neutral mesh>}` instead
  - small parts without a usable tri (lashes, AO/shadow layers) -> `nearest` (borrows the eyes' offsets)
  - the face itself -> `{"nif": standalone head}` when a neutral head with identical topology exists; it keeps
    FaceGen's UVs/shader/textures (the custom face textures were painted for those UVs)
- **Record fixes.** `drop_tri` when the tri file is missing or its vertex count differs from the mesh (a mismatched
  tri can corrupt morphs); `drop_tnam` when the part's texture set points at missing files (the extracted mesh
  already carries FaceGen's correct textures); `playable` for main parts the user should pick (hair, eyes, brows, face).
  FaceGen shape names can differ from HDPT EditorIDs (e.g. `SH_SeranaEyeAO2` vs `SH_Serana_EyesAO2`) - map them by hand.
- **One tri file per part.** If two parts share a tri path (typically upper + lower lashes both on vanilla
  `EyesFemale.tri`), copy the tri once per part into the patch and point each part at its own copy (`"tri"` option in
  `build_patch.py`, which warns about shared tris). RaceMenu stores sculpt per *tri path*: with a shared tri the
  user's sculpt/import looks right until they save, then both parts get the same offsets on reload.

### 3. Extract meshes
Write a config (schema at the top of `scripts/extract_headparts.py`) and run
`python -I scripts/extract_headparts.py extract.json`. Put meshes under a new subfolder of the follower's
mesh path (e.g. `actors\character\<follower folder>\<Race>Patch\...`) so they never overwrite the follower's files.
The script writes SE-ready `BSDynamicTriShape` NIFs and re-verifies each against FaceGen (topology, UVs,
textures, shader flags, alpha, partitions, bones). Eye shifts of ~1 unit and hair shifts of 0 are normal; a
`FAILED` line is not - fix it before continuing. Extracted meshes keep the FaceGen shape names on purpose: RaceMenu's
"import from NIF" matches the follower's FaceGen file to the character's parts by those names, which is how users
reproduce the follower's exact face on top of the neutral parts.

Prefer the follower's own parts over substitutes from other mods. Offline geometry checks can look alarming
(Serana's FaceGen lashes appear displaced when transformed outside the game) yet render correctly in game; swapping
them for another mod's lashes cost several broken iterations. Change a part only on in-game evidence.

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
- optionally adds the follower's **skin tone** (`skin_tone`: the NPC's QNAM, which `inspect_follower.py` prints as hex,
  or an explicit `hex`) as an **extra** preset of the race's SkinTone tint layer, first in the list and by default the
  race's default tone. The race's own presets stay. Offer this whenever the follower's tone matters: RaceMenu has no
  hex entry, so a preset is the only way for the player to get the exact colour. Baked makeup excludes complexion
  (step 4), so without it the face falls back to whatever tone the player picks;
- for a new race: clones the source race, renames it, sets Playable, sets Armor Race to the clone source (vanilla
  armor works without extra mods), **drops the racial presets** (RPRM/RPRF) and writes a Race Compatibility SKSE
  json (proxies for dialogue/vampirism/vanilla head parts).

New-race pitfalls, each of which cost an in-game round trip (details in `references/engine-notes.md`):
- **Racial presets.** Vanilla races carry preset NPCs (RPRM/RPRF). Chargen applies one to new characters, so they got
  vanilla eyes/hair and RaceMenu never offered the follower's parts. Strip them from any clone of a vanilla race.
- **Skin addons vs Armor Race.** The engine matches skin ARMAs against the race's *Armor Race*. When that is the
  clone source, the skin ARMAs must keep the source race (and its vampire race) in their additional races, plus the
  new race. With the new race alone the naked body was invisible and armor skin fell back to vanilla textures.
- **Name the playable parts** (FULL "<Follower> Hair/Eyes/Brows/Head") so they can be found in RaceMenu's long lists.
- **Localized strings.** Records copied from `Skyrim.esm` (vanilla mouth, race FULL/DESC) carry string-table IDs;
  in a non-localized plugin they show as junk. Replace or drop FULL/DESC on every copied vanilla record.
- When something works in one build and not another, **diff the plugins record by record** against the working one
  (`examples/vayne_darkelf_standalone/compare_*.py`) before theorising - two guesses here were wrong.

Dump the result to sanity-check if anything looks off (the reconnaissance helpers in `esp_lib.py` parse plugins).
The game locks plugins while it runs: if writing fails with "Permission denied", ask the user to close Skyrim
(never kill it), and don't leave the running game's plugin pointing at files you've deleted.

### 5b. Standalone variant (no dependency on the follower or race mods)
When the user wants a self-contained mod, absorb records instead of overriding them:
- `PatchWriter.redirect[gid] = new_local_fid` maps records from non-master plugins (the follower's head parts, a
  custom race, its skin ARMO/ARMA/TXST) to new records in the patch; `remap_subs` then rewrites every reference.
  Redirect references you are about to drop to 0 and remove them after remapping. Allocate FormIDs in a fixed order
  and never reorder later - users' saves reference them.
- Copy assets into the new mod's own folder and point meshes at it: `extract_headparts.py` `"texture_remap"`
  rewrites texture prefixes; `scripts/retexture_nif.py` rewrites paths in an existing NIF; copy tris, skeletons and
  textures, then verify every path in the plugin resolves inside the mod (see `examples/` and the Blood Scion build).
- `examples/vayne_darkelf_standalone/` is a standalone race cloned from a **vanilla** race (DarkElfRace) whose source
  follower plugin couldn't be a master (its own masters weren't installed): absorbs head parts, skin ARMO/ARMA/TXST,
  and a vanilla mouth copy; `verify_plugin.py` checks every FormID and path.
- If the follower plugin has **missing masters** (check them against the user's mod folders), never make it a master
  of the patch - go standalone and read it with `Plugin()` directly (no master resolution needed).
- Gameplay from another race (e.g. "Breton abilities"): read the race record from the plugin that **wins** in the
  user's load order (scan the active MO2 profile; with Requiem that is `Requiem.esp`, which replaces abilities,
  keywords, stats and attack data) and copy SPLO/KWDA/stat fields of DATA/ATKD/VNAM/QNAM; keep cosmetic data.
  Add a Race Compatibility SKSE json proxying that race so perk/dialogue conditions treat the new race as it.
- Renaming later: regenerate from scratch only if no profile/save uses the old plugin name yet.

### 5c. Body skin from another texture mod
If the user wants e.g. BnP body textures, ship them as a **separate MO2 mod** that overrides the race's skin texture
paths (copy, don't reference the texture mod's vanilla paths - another skin mod may win there). Measure seams before
editing anything: pair boundary vertices of head/body (neck) and hands/body (wrists) by 3D position, sample every map
(diffuse, `_sk`, `_msn`, `_s`) at their UVs and compare with the follower's own body as a baseline. Many follower
bodies are edits of BnP that leave the neck untouched, so raw BnP is often already seamless. Only if not, blend a
correction in with a soft mask near the seam, the way follower authors' mask PSDs do.

### 6. Tell the user how to apply it
- Enable the follower mod, the race mod and the patch; the patch must load after both (and after anything else
  that edits that race).
- Existing characters keep their saved head: in RaceMenu (`showracemenu`) switch to another race and back to
  reload race defaults - this resets sliders, so suggest saving a RaceMenu preset first. Then pick the follower's
  hair/eyes/brows from the lists.
- NPCs of that race need FaceGen regenerated in the CK to show the new parts; players don't.
- To reproduce the follower's exact face: RaceMenu sculpt → import the follower's FaceGen NIF (matches the extracted
  parts by shape name), then save a preset. Save and **reload** once to confirm nothing moves.
- If a part looks displaced in game, ask for a screenshot and read the user's preset
  (`SKSE\Plugins\CharGen\Presets\*.jslot`, `morphs.sculpt[].host`) before touching meshes: duplicate hosts or stale
  entries keyed to a tri path the part now uses explain most "wrong position" reports. Fix with per-part tris and,
  if needed, write a corrected *copy* of the preset (never overwrite the user's original).
- Mention honest caveats: hair was fitted to the follower's head and may clip on very different head shapes;
  `nearest`-neutralised parts are approximations; baked makeup can't be removed in RaceMenu.

## Output summary to give the user
List the new mod folder, what each part became (extracted / reused / fixed), what the plugin changes,
load-order and in-game steps, and anything not verified in game. Keep the configs in the patch's source
folder or the user's chosen location if they may want to rebuild (e.g. after switching makeup variant).
