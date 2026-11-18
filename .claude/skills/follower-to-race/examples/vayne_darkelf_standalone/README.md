# Vayne (Velvet Darkness overhaul) -> standalone race cloned from vanilla DarkElfRace

Paths are the author's - adapt them. Run in order: `build_assets.py`, `build_plugin.py`, `verify_plugin.py`.

Why standalone: the follower plugin's own masters (`CSV_Vayne.esp`, `CS_Visions.esp`) weren't installed, so it
could not be a master of the patch. Records were read with `Plugin()` directly and absorbed.

What went wrong in game, in order, and the fix now in these scripts:
1. Eyes extracted ~120 units low: Expressive Facial Animation's `EyesFemale.tri` is in head-bone space. Eyes/lashes
   now use CVEO's neutral meshes (`{"nif": ...}`); AO uses `nearest` driven by them.
2. Naked body invisible, armor skin vanilla: skin ARMAs listed only the new race, but the race's Armor Race is
   DarkElfRace. They now keep DarkElfRace/DarkElfRaceVampire and add the new race.
3. Hair/eyes not in RaceMenu and not default: vanilla racial presets (RPRM/RPRF) were inherited from DarkElfRace.
   Removed. (Removing NAM8 was an earlier, wrong guess - kept out, harmless.)
4. Copied vanilla mouth carried a localized FULL id -> dropped. Playable parts got FULL names.
5. The user couldn't enter Vayne's skin tone (#364C59) in RaceMenu (no hex input). Added it as an extra female
   SkinTone preset "Vayne", first and default (`add_skin_tone_preset`); the five Dark Elf tones remain.

`dump_skintone.py` prints the race's SkinTone layers with each preset's colour.

`compare_*.py` diff this build against the working Blood Scion build - that diff found cause 3.
`build_plugin.py` keeps a retired FormID slot (removed nose piercing) so later ids never shift.
