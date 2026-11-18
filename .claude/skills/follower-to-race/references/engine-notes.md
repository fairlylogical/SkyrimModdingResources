# Engine notes (Skyrim SE head parts, races, FaceGen)

## Contents
1. HDPT records
2. RACE head data
3. FaceGen files
4. Neutralising sculpted geometry
5. Face tint / makeup math
6. NIF writing pitfalls (pynifly)
7. Plugin writing details
8. Worked example (Serana -> SC_DAI Morrigan race)

## 1. HDPT records
Subrecords: EDID, FULL, MODL (mesh, relative to `meshes\`), MODT, DATA (u8 flags), PNAM (type), HNAM* (extra parts),
NAM0/NAM1 pairs (NAM0=0 race morph, 1 tri, 2 chargen morph; NAM1 path), TNAM (TXST texture override), CNAM (color), RNAM (valid-races FLST).
- DATA flags: 0x01 Playable, 0x02 Male, 0x04 Female, 0x08 Is Extra Part, 0x10 Use Solid Tint.
- PNAM type: 0 Misc, 1 Face, 2 Eyes, 3 Hair, 4 Facial Hair, 5 Scar, 6 Eyebrows.
- Record header flag 0x04 on HDPT = Non-Playable. RaceMenu lists only playable parts of the right sex whose RNAM list
  contains the race - so clear 0x04 and set DATA 0x01.
- Extra parts (HNAM) follow their parent; they don't need Playable, but give them the same RNAM so they load for the race.
- TNAM overrides the mesh's textures at runtime. FaceGen ignores it (textures are baked into the FaceGen NIF), so
  follower authors often leave broken TNAMs. Dropping TNAM makes the mesh's own textures apply.
- A tri file whose vertex count differs from the mesh is unsafe; a missing tri only loses morphs. Drop NAM0/NAM1 in both cases.

## 2. RACE head data
Layout after the body data: `NAM0`, `MNAM`, (`INDX`, `HEAD`)*, MPAI/MPAV morph presets, RPRM presets, AHCM, FTSM, DFTM,
TINI/TINT/TINP/TIND/TINC/TINV/TIRS tint layers..., then `NAM0`, `FNAM` and the same for female. `HEAD` entries are the
race's **default** parts. RaceMenu has pickers for hair, eyes, brows, facial hair, scars - but not for the Face part,
so the head mesh always comes from these defaults (a player's chosen parts are saved per character; switching race
in RaceMenu reloads the defaults).
- RACE DATA flags (u32 at offset 32): 0x1 Playable.
- RACE RNAM = Armor Race (armor addons are looked up for this race), NAM8 = Morph Race.
  **Strip racial presets (RPRM/RPRF) when cloning a vanilla race.** They are vanilla preset NPCs; chargen applies
  one to new characters, giving them vanilla eyes/hair, and Vayne's own hair/eyes never appeared in RaceMenu even
  though her HDPT records matched the working Blood Scion ones (whose source race had no presets). An earlier guess
  blamed the Morph Race (NAM8) - Blood Scion has NAM8 and works, so that was not it. Diff against a known-working
  race before guessing.
  **Consequence for skin ARMAs:** if the new race's Armor Race is the clone source (e.g. DarkElfRace), the race's own
  skin ARMAs must list that source race too (keep the follower's original additional races, then add the new race).
  Listing only the new race made the naked body invisible and armor skin fell back to vanilla textures (Vayne, 2026-11).
- Tint layers: if a race only has SkinTone, no RaceMenu preset can reproduce makeup/lipstick/eyeliner.
- Race Compatibility SKSE (RCS) json in `SKSE\Plugins\RCS\*.json` proxies a custom race to vanilla races for
  dialogue/vampirism/armor and (`"headPart": "Human"`) vanilla head-part lists. Races are named by EditorID.

## 3. FaceGen files
- Mesh: `meshes\actors\character\FaceGenData\FaceGeom\<plugin that DEFINES the NPC>\<8-hex object id>.nif`
  (for an NPC replacer like Serana it's `Dawnguard.esm`, not the replacer plugin).
- Tint: same path under `textures\...\FaceTint\...dds`.
- Shapes are named after the HDPT EditorIDs (usually), are BSDynamicTriShape, skinned to `NPC Head [Head]`
  (+ `NPC Spine2 [Spn2]` for head/hair). Shapes without a shader are invisible helpers (e.g. LDD eye lens dummies).
- FaceGen carries the NPC's custom textures; standalone meshes often don't.

## 4. Neutralising sculpted geometry
CK applies the NPC's chargen sliders (tri morphs) to every part that has a tri, then bakes. To get a neutral part:
- `.tri` base vertices are the neutral mesh in the same local space/order as the FaceGen shape (verify counts).
  The head's tri is in head-bone-local space (offset by the head bone ~ (0,-1.55,120.3)) - for the face use a
  standalone neutral NIF instead.
- Parts without a tri: hair is not morphed by CK - copy as-is. Lashes/AO layers that were morphed via a tri
  whose topology you can't use: subtract the offset of the nearest neutralised eye vertices (inverse-distance
  weighted, k=4). Their shift should come out ~equal to the eyes' shift; if not, inspect.

- **Expressive Facial Animation's `EyesFemale.tri` is in head-bone space too** (base verts ~120 units below FaceGen
  eyes). Using it as `{"tri"}` neutral put the eyes at the neck (Vayne, 2026-11). For LDD/CVEO eyes use
  `{"nif": CVEO LDD_FemaleEyes.nif}` / `LDDLashes\A\LDD_FemaleLashes.nif` instead (same topology as FaceGen); nif-mode
  parts can now serve as `delta_samples` for `nearest`. extract_headparts fails any part shifted >= 25 units.
- **Give every head part its own tri path - RaceMenu sculpt is keyed by tri path.** Presets
  (`SKSE\Plugins\CharGen\Presets\*.jslot`, `morphs.sculpt[].host`) and saves store sculpt per *tri file path* + vertex
  index, not per head part. Serana's upper and lower lashes both used vanilla `EyesFemale.tri`: RaceMenu's
  "import from FaceGen NIF" placed them perfectly, but on save both parts' sculpt collapsed into one host entry
  (the jslot showed two identical `EyesFemale.tri` entries), so after reload both lids got the same offsets and the
  lashes floated off the eyes. Fix: copy the tri per part (`EyelashesLower.tri`, `EyelashesUpper.tri`, ...) and point
  each HDPT's NAM1 at its own copy. Any shared tri among parts on the same character is a bug waiting for a sculpt.
  When a part looks displaced in game, read the user's jslot first and look for duplicate hosts.
- **Keep FaceGen shape names on extracted meshes.** RaceMenu's import matches source FaceGen shapes to the
  character's parts by name; extracted meshes that keep `SH_<Follower>_*` names import cleanly.
- **Don't trust "static" geometry checks over in-game evidence for FaceGen parts.** Serana's FaceGen lash shapes look
  displaced when their vertices are transformed offline (most vertices several units inside the head), yet imported
  onto the extracted lashes they render correctly in game. A detour replacing them with CVEO/LDD lash meshes cost
  several iterations (chargen tri folding them behind the cornea, offsets from stale sculpt). Prefer the follower's
  own parts; if a part looks wrong in game, ask for a screenshot and the jslot before re-engineering the mesh.
- Useful leftovers from that detour: `scripts/retexture_nif.py` (rewrite NIF texture paths) and
  `scripts/normalize_headpart.py` (bake a non-identity shape transform into vertices, recomputing skin-to-bone).
  LDD/CVEO lashes use vanilla eye vertex order; LDD meshes park unused vertices hundreds of units away.

## 5. Face tint / makeup math
SE FaceGen shader (Community Shaders Lighting.hlsl, GetFacegenBaseColor):
`out = (b*b + 2*t*b*(1-b)) * detail` with `detail ≈ 1` by default; t = 0.5 is identity.
Bake: normalise t so its median (base complexion) maps to 0.5 (`t' = 0.5*t/median`), then `b' = b*b + 2*t'*b*(1-b)`.
Textures are sampled as raw (non-sRGB) values, so no gamma conversion. Keep the diffuse's alpha.
texconv: pass Windows-style paths (backslashes); forward-slash inputs make it build broken output paths.

## 6. NIF writing pitfalls (pynifly)
- `shape.partition_tris` returns **indices** into `shape.partitions`, while `set_partitions(parts, trilist)` wants
  partition **IDs** - map with `[parts[i].id for i in partition_tris]`, otherwise every triangle gets a bogus
  partition (hundreds of SBP_32 entries).
- pynifly inverts V on write: pass `(u, 1-v)`.
- `createShapeFromData` always creates a shader. For source shapes with no shader, remove the trailing
  shader/texture-set blocks and null the shape's shader/alpha refs (`strip_shader`). Copying an empty shader's
  properties produces a `BSShaderPPLightingProperty` (Oblivion-era) which SE must not load.
- Force `BSDynamicTriShape` for head parts: SE chargen morphs need it (standalone heads shipped as BSTriShape won't
  take RaceMenu sliders).
- pynifly NIF reads fail with Windows error 0xe06d7363 on malformed files - a quick validity check after writing.

## 7. Plugin writing details
- FormID high byte = index into that plugin's master list; the plugin's own records use index len(masters).
  Copying a record into a patch requires remapping every FormID field (`esp_lib.FORMID_FIELDS`), not just the record id.
- ESL flag = TES4 flag 0x200; new records take object ids from 0x800 (HEDR next id).
- Override records keep their original FormID (remapped); load order decides the winner, so the patch must load last
  among plugins touching those records.

## 8. Worked example: Serana (Evigheden) -> SC_DAI Morrigan race
- Hair meshes referenced by the HDPTs weren't shipped at all; eyes HDPTs all pointed to one 176-vert placeholder with
  another mod's textures. Head/brows standalone meshes matched FaceGen topology but head textures were vanilla.
- Eyes/AO/caruncula/lens dummies: `tri` (LDD tris matched). Lashes + AO2: `nearest`. Hair (5 shapes): `facegen`.
  Head: `nif` from the standalone femalehead.nif + baked-makeup diffuse.
- Scalp tri missing and AO2's tri had 478 verts vs 176 -> `drop_tri`. Eye TNAM pointed at a missing normal map -> `drop_tnam`.
- Morrigan race had one tint layer -> Coldharbour makeup baked (FaceTint 2048² upscaled to the 4096² diffuse, BC7).
- First attempt missed `race_defaults`: hair/eyes worked via RaceMenu, the face stayed Morrigan's until the race's
  female Face default was replaced.
