Scriptname GnW_StoryEventKillActorScript extends Quest  

Actor property PlayerRef auto
GnW__ModManagerScript property modManagerScript Auto
GnW_GodQuestScript property stendarrQuestScript Auto
Faction property DLC2dunFrostmoonWerewolvesFaction auto
Faction property DLC2TribalWerebearFaction auto
Faction property WerewolfFaction auto
Keyword property Vampire auto
Keyword property ActorTypeDaedra auto
GlobalVariable property GnW_GLO_AbilityStendarr_numKills auto

Event OnStoryKillActor(ObjectReference akVictim, ObjectReference akKiller, Location akLocation, int aiCrimeStatus, int aiRelationshipRank)
	Actor victim = akVictim as Actor
	If (victim && akKiller == PlayerRef)
		If  (aiCrimeStatus == 0)		;Kill
			;Triggered by killing undead, daedra, and werebeasts - check SM node for conditions
			modManagerScript.KillSpecial(victim)
			
			If (modManagerScript.GlobalCurrentGodIndex == 6 && stendarrQuestScript.affinityRank >= 2 && GnW_GLO_AbilityStendarr_numKills.GetValueInt() < 50)
				If (!victim.IsCommandedActor() && (victim.HasKeyword(ActorTypeDaedra) || victim.HasKeyword(vampire) || \
					victim.IsInFaction(WerewolfFaction) || victim.IsInFaction(DLC2dunFrostmoonWerewolvesFaction) || victim.IsInFaction(DLC2TribalWerebearFaction)))
						Int kills = GnW_GLO_AbilityStendarr_numKills.GetValueInt() + 1
						GnW_GLO_AbilityStendarr_numKills.SetValueInt(kills)
						PlayerRef.SetAV("Energy", kills)
						;Debug.Trace("Stendarr Ability: Increasing special kill global - " + PlayerRef.GetAV("Energy")  )
				EndIf
			EndIf
		EndIf
	EndIf

	Stop()
EndEvent


