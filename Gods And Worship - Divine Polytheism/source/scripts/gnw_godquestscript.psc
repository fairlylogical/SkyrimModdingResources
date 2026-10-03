Scriptname GnW_GodQuestScript extends Quest Conditional

;--GLOBALS--
Bool property bIsCurrentGod Auto Conditional hidden
Bool property bIsPariah Auto Conditional hidden
Bool property bAllowCrafting Auto Conditional hidden
Bool property bCanMakeOffering Auto Conditional hidden
Bool property bCanUsePower Auto Conditional hidden
Bool property bPilgrimageQuestComplete Auto Conditional hidden
Int property affinityRank Auto Conditional hidden
Int property affinityPoints auto hidden
Actor property player auto hidden

;---MAIN---
GnW__ModManagerScript property modManagerScript Auto
String property _godName Auto
Int property _godIndex Auto

;---ABILITIES AND POWERS, GOD-SPECIFIC LISTS OF STUFF---
Formlist property GnW_LIST_GodAbilities auto ;listed by god index
Formlist property GnW_LIST_GodAltarSpells auto
Formlist property GnW_LIST_GodGuardianABs auto
Formlist property GnW_LIST_GodMeditateSpells auto
Formlist property GnW_LIST_GodPowers auto
Formlist property GnW_LIST_GodRankABs auto
Formlist property GnW_LIST_GodShrinePerks auto  
Formlist property GnW_LIST_GodAmulets auto
Formlist property GnW_LIST_GodRobes auto
Spell property GnW_POW_Meditate Auto
Spell property GnW_SPELL_RankUpFX auto
Spell property GnW_SPELL_RankDownFX auto

;---QUESTS---
Formlist property GnW_LIST_GodPilgrimageQuests Auto
Quest property GnW_TempleHomeQuest Auto

;---MESSAGES---
Formlist property GnW_LIST_GodShunnedMessages auto
Message property GnW_MSG_RankUpPleased auto
Message property GnW_MSG_RankDownDispleased auto
Message property GnW_MSG_RankDownNeglect auto
Formlist property GnW_LIST_RankUpMessages auto
Formlist property GnW_LIST_RankDownMessages auto
Message property GnW_MSG_RemoveGrace auto
Message property GnW_MSG_RemoveBoon auto
Message property GnW_MSG_RemoveGuardian auto
Formlist property GnW_LIST_GodAltarMessages auto
Message property GnW_MSG_ReactionLove1 auto
Message property GnW_MSG_ReactionLove2 auto
Message property GnW_MSG_ReactionHate1 auto
Message property GnW_MSG_ReactionHate2 auto
Message property GnW_MSG_PowerReady auto

;--AFFINITY POINTS FOR EACH THING--
;--Negative points for disapproval--
Int[] property AffinityPointThresholds auto hidden
int iPointsL4 = 28
int iPointsL3 = 16
int iPointsL2 = 8
int iPointsL1 = 3
int iPointsH4 = -28
int iPointsH3 = -16
int iPointsH2 = -8
int iPointsH1 = -3

int iPointsNeglect = -1
int iPointsPrayMeditate = 1
int iPointsOffering = 3
int iPointsPilgrimage = 16
int iPointsPrayOther = -8
int iPointsProselytize = 3
int iPointsProselytizeOther = -3

Int[] property HatedGodIndexes auto 
Int property iPointsCharity auto
Int property iPointsPickpocket auto
Int property iPointsStealing auto
Int property iPointsBrawl auto
Int property iPointsAssault auto
Int property iPointsMurder auto
Int property iPointsKillUndead auto
Int property iPointsKillDaedra auto
Int property iPointsKillWerebeast auto
Int property iPointsKillStrongCreatureAnimal auto
Int property iPointsKillStrongCreatureUndead auto
Int property iPointsCannibalism auto
Int property iPointsNecromancy auto
Int property iPointsVampireInfect auto
Int property iPointsVampireFeed auto
Int property iPointsVampireTrans auto
Int property iPointsVampireCure auto
Int property iPointsWerewolfInfect auto
Int property iPointsWerewolfFeed auto
Int property iPointsWerewolfTrans auto
Int property iPointsWerewolfCure auto
Int property iPointsMarriage auto
Int property iPointsMarriageBreakup auto
Int property iPointsAdopt auto
Int property iPointsPersuade auto
Int property iPointsBribe auto
Int property iPointsIntimidate auto
Int property iPointsUseQuestItem auto
Int property iPointsSoulTrapBlackSoul auto

;---FACTIONS---
Formlist property GnW_LIST_GodAllyFactions auto
Faction property PlayerFaction Auto

;---RACES---
Race property DragonPriestRace auto
Race property DLC2AcolyteDragonPriestRace auto
Race property MammothRace auto
Race property GiantRace auto 
Race property WerewolfBeastRace auto
Race property DLC2WerebearBeastRace auto

;--KEYWORDS---
Keyword property ActorTypeUndead Auto
Keyword property ActorTypeDaedra Auto
Keyword property ActorTypeDragon auto
Keyword property GnW_K_IsStrongAnimal auto
Keyword property GnW_K_IsStrongUndead auto

;---MISC---
Formlist property GnW_LIST_GodOfferingLists auto
Bool property offerStolenItems Auto
Actor property fakeGodActor Auto
Bool property restrictSpecialShrineEffToOffering Auto
Enchantment property questItemEnchantment Auto

;---------LOCAL VARIABLES---------
;--TIMERS---
Float maxPariahTime = 72.0
Float maxNeglectTime = 24.0
Float maxPrayMeditateTime = 8.0
Float maxOfferingTime = 24.0
Float maxPowerTime = 8.0
Float timerPariah
Float timerNeglect
Float timerOffering
Float timerPower
Float timerPrayMeditate
Float timerDaily
Float prayMeditateNeglectOffset = 8.0

Float timeReactionCooldown = 60.0
Bool reactionHateOnCooldown
Bool reactionLoveOnCooldown

Perk perkShrine
Spell spRank
Spell spMeditateEff
Spell spBlessing
Spell spAbility
Spell spPower
Spell spGuardian
Message msgShunned
Message msgBlessing
Armor armorAmulet
Armor armorRobes
Faction minionAllyFaction
Formlist property offeringItemsList auto hidden
Quest pilgrimageQuest

Int dailyPointsCap
Int dailyPointsStealPickpocket
Int dailyPointsKillSpecial
Int dailyPointsUseQuestItem
Int dailyPointsCannibal
Int dailyPointsNecromancy
Int dailyPointsVampireFeed
Int dailyPointsWerewolfFeed

;---------------------------------------------------------------------------------------------------------------------------
;---------------------------------------------------------------------------------------------------------------------------
Function Init()
	player = Game.GetPlayer()

	affinityRank = 0
	affinityPoints = 0
	bIsPariah = false
	bAllowCrafting = false
	bCanMakeOffering = true
	bCanUsePower = true
	bPilgrimageQuestComplete = false
	timerPariah = 0.0
	timerNeglect = 0.0
	timerOffering = 0.0
	timerPower = 0.0
	timerPrayMeditate = 0.0
	timerDaily = 24.0

	AffinityPointThresholds = new Int[6]
	AffinityPointThresholds[0] = 0
	AffinityPointThresholds[1] = 10		;10
	AffinityPointThresholds[2] = 40		;30
	AffinityPointThresholds[3] = 90		;50
	AffinityPointThresholds[4] = 160		;70
	AffinityPointThresholds[5] = 250		;90

	dailyPointsCap = 8
	ResetDailyPointCaps()

	perkShrine = GnW_LIST_GodShrinePerks.GetAt(_godIndex) as Perk
	spRank = GnW_LIST_GodRankABs.GetAt(_godIndex) as Spell
	spMeditateEff = GnW_LIST_GodMeditateSpells.GetAt(_godIndex) as Spell
	spBlessing = GnW_LIST_GodAltarSpells.GetAt(_godIndex) as Spell
	spAbility = GnW_LIST_GodAbilities.GetAt(_godIndex) as Spell
	spPower = GnW_LIST_GodPowers.GetAt(_godIndex) as Spell
	spGuardian = GnW_LIST_GodGuardianABs.GetAt(_godIndex) as Spell
	msgBlessing = GnW_LIST_GodAltarMessages.GetAt(_godIndex) as Message
	msgShunned = GnW_LIST_GodShunnedMessages.GetAt(_godIndex) as Message
	armorAmulet = GnW_LIST_GodAmulets.GetAt(_godIndex) as Armor
	armorRobes = GnW_LIST_GodRobes.GetAt(_godIndex) as Armor
	minionAllyFaction = GnW_LIST_GodAllyFactions.GetAt(_godIndex) as Faction
	offeringItemsList = GnW_LIST_GodOfferingLists.GetAt(_godIndex) as Formlist
	pilgrimageQuest = GnW_LIST_GodPilgrimageQuests.GetAt(_godIndex) as Quest

	player.AddPerk(perkShrine)
	player.AddSpell(spRank, false)

EndFunction

Function ResetGod()
	affinityRank = 0
	affinityPoints = 0
	bIsPariah = false
	bAllowCrafting = false
	bCanMakeOffering = true
	bCanUsePower = true
	bPilgrimageQuestComplete = false
	timerPariah = 0.0
	timerNeglect = 0.0
	timerOffering = 0.0
	timerPower = 0.0
	timerPrayMeditate = 0.0
	timerDaily = 24.0

	ResetDailyPointCaps()
	reactionLoveOnCooldown = false
	reactionHateOnCooldown = false

	player.DispelSpell(spMeditateEff) 	
	player.DispelSpell(spBlessing)
	player.DispelSpell(spPower)
	RemovePowersAndAbilities()
EndFunction

Function Shutdown()
	player.DispelSpell(spMeditateEff) 	
	player.DispelSpell(spBlessing)
	player.DispelSpell(spPower)

	player.RemovePerk(perkShrine)
	player.RemoveSpell(spRank)
	RemovePowersAndAbilities()
EndFunction

;---------------------------------------------------------------------------------------------------------------------------
;---CORE FUNCTIONS---
;---------------------------------------------------------------------------------------------------------------------------
Function Pray(bool gaveOffering=true)
	;Check for a secondary shrine effect
	If (!restrictSpecialShrineEffToOffering || gaveOffering)
		SetStage(10)
	EndIf

	If (!bIsCurrentGod)
		Return
	EndIf

	If (timerOffering <= 0.0 && gaveOffering)
		UpdateAffinity(iPointsOffering, true)
		timerOffering = maxOfferingTime
		timerPrayMeditate = maxPrayMeditateTime
		bCanMakeOffering = false
	Elseif (timerPrayMeditate <= 0.0)
		UpdateAffinity(iPointsPrayMeditate, true)
		timerPrayMeditate = maxPrayMeditateTime
	Endif

	;--refresh power--
	RefreshPower()

	;--offset neglect timer--
	If (gaveOffering)
		timerNeglect = maxNeglectTime
	Else
		timerNeglect += prayMeditateNeglectOffset 
		If (timerNeglect >  maxNeglectTime)
			timerNeglect = maxNeglectTime
		EndIf
	EndIf
EndFunction

;------------------------------------------------------
Function PrayWhileShunned()
	Int days = Math.Ceiling(timerPariah / 24.0)
	msgShunned.Show(days)
EndFunction

;------------------------------------------------------
Function Meditate()	
;	LogDebug("Meditate() - effect:" + spMeditateEff.GetName())

	player.DispelSpell(spBlessing)	;POLYTHEISM: the Divines' blessings no longer dispel each other, so replace this god's own shrine blessing by hand

	spMeditateEff.Cast(player, player)
	msgBlessing.Show()

	If (timerPrayMeditate <= 0.0)		
		UpdateAffinity(iPointsPrayMeditate)
		timerPrayMeditate = maxPrayMeditateTime
	EndIf

	;--refresh power--
	RefreshPower()

	;--offset neglect timer--
	timerNeglect += prayMeditateNeglectOffset 
	If (timerNeglect >  maxNeglectTime)
		timerNeglect = maxNeglectTime
	EndIf

;		LogDebug("Meditate() - end of function")
EndFunction

;------------------------------------------------------
Function DispelBlessings()
	;POLYTHEISM: called by the mod manager, which now decides which shrine/meditation blessings may coexist
	player.DispelSpell(spBlessing)
	player.DispelSpell(spMeditateEff)
EndFunction

Function GiveShrineBlessing()
	;POLYTHEISM: what activating the shrine does, minus Requiem's DispelAllSpells()
	spBlessing.Cast(player, player)
	msgBlessing.Show()
EndFunction

;------------------------------------------------------
Function UsedPower()
	bCanUsePower = false
	timerPower = maxPowerTime
EndFunction

;------------------------------------------------------
Function PilgrimageQuestComplete()
	bPilgrimageQuestComplete = true

	;If this is the first time completing the pilgrimage for any god, start the abandoned temple quest
	If (!GnW_TempleHomeQuest.IsRunning() && !GnW_TempleHomeQuest.IsCompleted() && modManagerScript.GlobalTempleHomeQuestStarted == 0)
		modManagerScript.GlobalTempleHomeQuestStarted = 1
		GnW_TempleHomeQuest.Start()
	EndIf
EndFunction

;---------------------------------------------------------------------------------------------------------------------------
;---HANDLE PLAYER ACTIONS---
;---------------------------------------------------------------------------------------------------------------------------
Function PrayOther(Int godIndex)
	;LogDebug("PrayOther - " + godIndex)
	If (HatedGodIndexes.Find(godIndex) > -1)
		UpdateAffinity(iPointsPrayOther)
	Endif
EndFunction

Function Proselytize()
	UpdateAffinity(iPointsProselytize)
EndFunction

Function ProselytizeOther(Int godIndex)
	If (HatedGodIndexes.Find(godIndex) > -1)
		UpdateAffinity(iPointsProselytizeOther)
	Endif
EndFunction

Function CompleteTempleErrand(Int points)
	UpdateAffinity(points)
EndFunction

Function GiveCharity()
	UpdateAffinity(iPointsCharity)
EndFunction

Function Pickpocket(Bool valuable)
	If (dailyPointsStealPickpocket < dailyPointsCap)
		UpdateAffinity(iPointsPickpocket)
		If  iPointsPickpocket > 0
			dailyPointsStealPickpocket += iPointsPickpocket
		EndIf
	EndIf
EndFunction

Function Steal(Bool valuable)
	If (dailyPointsStealPickpocket < dailyPointsCap)
		UpdateAffinity(iPointsStealing)
		If  iPointsStealing > 0
			dailyPointsStealPickpocket += iPointsStealing
		EndIf
	EndIf
EndFunction

Function Bribe()
	UpdateAffinity(iPointsBribe)
EndFunction

Function Intimidate()
	UpdateAffinity(iPointsIntimidate)
EndFunction

Function Presuade()
	UpdateAffinity(iPointsPersuade)
EndFunction

Function Brawl()
	UpdateAffinity(iPointsBrawl)
EndFunction

Function Assault(Actor victim)
	UpdateAffinity(iPointsAssault)
EndFunction

Function Murder(Actor victim)
	UpdateAffinity(iPointsMurder)
EndFunction

Function KillSpecial(Actor victim)
	Race victimRace = victim.GetRace()

	If (victim.HasKeyword(ActorTypeDragon) || victimRace == MammothRace || victimRace == GiantRace || victim.HasKeyword(GnW_K_IsStrongAnimal))
		UpdateAffinity(iPointsKillStrongCreatureAnimal)

	Elseif (victimRace == DragonPriestRace || victimRace == DLC2AcolyteDragonPriestRace || victim.HasKeyword(GnW_K_IsStrongUndead))
		UpdateAffinity(iPointsKillStrongCreatureUndead)

	Elseif (victim.HasKeyword(ActorTypeUndead))	
		If (dailyPointsKillSpecial < dailyPointsCap)
			UpdateAffinity(iPointsKillUndead)
			dailyPointsKillSpecial += iPointsKillUndead
		EndIf

	Elseif (victim.HasKeyword(ActorTypeDaedra))
		If (dailyPointsKillSpecial < dailyPointsCap)
			UpdateAffinity(iPointsKillDaedra)
			dailyPointsKillSpecial += iPointsKillDaedra
		EndIf

	Elseif (victimRace == werewolfBeastRace || victimRace == DLC2WerebearBeastRace)
		If (dailyPointsKillSpecial < dailyPointsCap)
			UpdateAffinity(iPointsKillWerebeast)
			dailyPointsKillSpecial += iPointsKillWerebeast
		EndIf

	EndIf
EndFunction

Function Cannibalism()
	If (dailyPointsCannibal < dailyPointsCap)
		UpdateAffinity(iPointsCannibalism)
		If  iPointsCannibalism > 0
			dailyPointsCannibal += iPointsCannibalism
		EndIf
	EndIf
EndFunction

Function Necromancy()
	If (dailyPointsNecromancy < dailyPointsCap)
		UpdateAffinity(iPointsNecromancy)
		If  iPointsNecromancy > 0
			dailyPointsNecromancy += iPointsNecromancy
		EndIf
	EndIf
EndFunction

Function BecomeVampire(Bool thruShrine = false)
	If (!thruShrine)
		UpdateAffinity(iPointsVampireInfect)
	EndIf
EndFunction

Function VampireFeed()
	If (dailyPointsVampireFeed < dailyPointsCap)
		UpdateAffinity(iPointsVampireFeed)
		If  iPointsVampireFeed > 0
			dailyPointsVampireFeed += iPointsVampireFeed
		EndIf
	EndIf
EndFunction

Function VampireLordTransform()
	UpdateAffinity(iPointsVampireTrans)
EndFunction

Function VampireCure()
	UpdateAffinity(iPointsVampireCure)
EndFunction

Function BecomeWerewolf(Bool thruShrine = false)
	If (!thruShrine)
		UpdateAffinity(iPointsWerewolfInfect)
	EndIf
EndFunction

Function WerewolfFeed()
	If (dailyPointsWerewolfFeed < dailyPointsCap)
		UpdateAffinity(iPointsWerewolfFeed)
		If  iPointsWerewolfFeed > 0
			dailyPointsWerewolfFeed += iPointsWerewolfFeed
		EndIf
	EndIf
EndFunction

Function WerewolfTransform()
	UpdateAffinity(iPointsWerewolfTrans)
EndFunction

Function WerewolfCure()
	UpdateAffinity(iPointsWerewolfCure)
EndFunction

Function QuestEvent(Int iPoints)
	UpdateAffinity(iPoints)
EndFunction

Function Marriage()
	UpdateAffinity(iPointsMarriage)
EndFunction

Function MarriageBreakup()
	UpdateAffinity(iPointsMarriageBreakup)
EndFunction

Function Adopt()
	UpdateAffinity(iPointsAdopt)
EndFunction

Function UseQuestItem(Enchantment ench)
	If (ench == questItemEnchantment)
		If (dailyPointsUseQuestItem < dailyPointsCap)
			UpdateAffinity(iPointsUseQuestItem)
			dailyPointsUseQuestItem += iPointsUseQuestItem
		EndIf
	EndIf
EndFunction

Function SoulTrapBlackSoul(int count)
	UpdateAffinity(iPointsSoulTrapBlackSoul * count)
EndFunction

;---------------------------------------------------------------------------------------------------------------------------
;---JUGGLE AFFINITY--
;---------------------------------------------------------------------------------------------------------------------------
Function UpdateAffinity(int points, bool isPray=false, bool isNeglect=false)
	If (points == 0)
		Return
	EndIf

	If (!bIsCurrentGod && points > 0)			;Don't gain affinity while this god is not active
		Return
	Endif
	If (bIsPariah)				
		If (points < 0)							;angered god while already a pariah, so reset the pariah timer
		;	ResetPariahState()
		EndIf
		Return
	EndIf

	If (points == iPointsH4 && !bIsPariah) 			;U dun fucked up, go directly to pariah, do not pass go, do not collect $200
		points = -9999
	Elseif (points == iPointsH3 && !bIsPariah) 		;drop at least 1 rank
		Int extraPoints = affinityPoints - AffinityPointThresholds[affinityRank]
		Int pointsToDock = (extraPoints + 1) * -1

		If (pointsToDock < points)
			points = pointsToDock
		EndIf
	EndIf

	;--Update points--
	affinityPoints += points

	If (affinityPoints < 0 && (isNeglect || !bIsCurrentGod))		;Dont' drop to pariah state while this god is not active OR if neglect
		affinityPoints = 0
	EndIf

;	If (affinityPoints > AffinityPointThresholds[5] + 8)
;		affinityPoints = AffinityPointThresholds[5] + 8	;Prevent overflow of points - make it easy to lose rank 5
;	EndIf
	LogDebug("UpdateAffinity() - points=" + points + ", affinityPoints=" + affinityPoints)

	;;---Show reaction and rank up or down as necessary--- 
	If (points  > 0)
		If (!isPray && !reactionLoveOnCooldown)  	;;show reaction
			reactionLoveOnCooldown = true
			reactionHateOnCooldown = false
			RegisterForSingleUpdate(timeReactionCooldown)

			If (points >= 16)
				GnW_MSG_ReactionLove2.Show()
			Else
				GnW_MSG_ReactionLove1.Show()
			EndIf
		EndIf

		Int rank = 0
		While (rank < AffinityPointThresholds.Length)
			If (affinityPoints >= AffinityPointThresholds[rank] && affinityRank < rank)
				RankUp()
			EndIf
			rank += 1;
		EndWhile
		
	Elseif (points < 0)
		If (!isNeglect && bIsCurrentGod && !reactionHateOnCooldown)		;;show reaction
			reactionHateOnCooldown = true
			reactionLoveOnCooldown = false
			RegisterForSingleUpdate(timeReactionCooldown)

			If (points <= -16)
				GnW_MSG_ReactionHate2.Show()
			Else
				GnW_MSG_ReactionHate1.Show()
			EndIf
		EndIf

		Bool didRankDown
		Int prevRank = affinityRank
		Int rank = 5
		While (rank >= 0)
			If (affinityPoints < AffinityPointThresholds[rank] && affinityRank >= rank)
				RankDown(isNeglect)
				didRankDown = true
			EndIf
			rank -= 1;
		EndWhile

		If (didRankDown && bIsCurrentGod) ;show messaging/FX if this god is active
			If (isNeglect)
				GnW_MSG_RankDownNeglect.Show()
			Else
				GnW_MSG_RankDownDispleased.Show()
			EndIf

			If (affinityRank > -1)
				(GnW_LIST_RankDownMessages.GetAt(affinityRank) as Message).Show()
			EndIf

			If (prevRank == 4 && affinityRank < 4)
				GnW_MSG_RemoveGuardian.Show()
			Elseif (prevRank == 3 && affinityRank < 3)
				GnW_MSG_RemoveBoon.Show()
			Elseif (prevRank == 2 && affinityRank < 2)
				GnW_MSG_RemoveGrace.Show()
			EndIf
		
			GnW_SPELL_RankDownFX.Cast(player, player)
		EndIf

	EndIf
	
EndFunction

;---------------------------------------------------------------------------------------------------------------------------
Function RankUp()
	affinityRank += 1

	If (affinityRank == 0)
		ExitPariahState()
	Elseif (affinityRank == 1)
		timerNeglect = maxNeglectTime	
	Elseif (affinityRank == 5)
		;start pilgrimage quest, if not already running and not previously completed
		If (!pilgrimageQuest.IsRunning() && !bPilgrimageQuestComplete)
			LogDebug("Trying to start pilgrimage quest")
			pilgrimageQuest.Start()
		EndIf
	EndIf

	UpdatePowersAndAbilities()

	LogDebug("Reached rank " + affinityRank)

	If (affinityRank > 0)
		GnW_MSG_RankUpPleased.Show()
		Int temp = affinityRank - 1
		(GnW_LIST_RankUpMessages.GetAt(temp) as Message).Show()
		GnW_SPELL_RankUpFX.Cast(player, player)
	EndIf
EndFunction

Function RankDown(bool isNeglect)
	Int prevRank = affinityRank
	affinityRank -= 1

	If (isNeglect && affinityRank == -1 && prevRank == 0)	;don't become pariah based only on neglect
		affinityRank = 0
		Return
	EndIf

	If (!bIsCurrentGod && affinityRank == -1 && prevRank == 0) ;shouldn't get here at all, but if so, keep this from happening
		affinityRank = 0
		Return
	EndIf
	
	If (affinityRank < -1)
		affinityRank = -1
		If (!bIsPariah)
			EnterPariahState()
		EndIf
		LogDebug("ERROR: Called RankDown while at rank -1")
	Elseif (affinityRank == -1)
		EnterPariahState()
	EndIf

	UpdatePowersAndAbilities()

	LogDebug("Fell to rank " + affinityRank)
EndFunction

;---------------------------------------------------------------------------------------------------------------------------
;--HANDLE PARIAH STATE---
;---------------------------------------------------------------------------------------------------------------------------
Function EnterPariahState()
	bIsPariah = true
	timerPariah = maxPariahTime
	timerNeglect = 0.0
	modManagerScript.RemoveGod(_godIndex)	;POLYTHEISM: was SwitchCurrentGod(-1), which dropped every god

	If (pilgrimageQuest.IsRunning())		;Fail pilgrimage quest, if running
		pilgrimageQuest.SetStage(500)
	EndIf

	player.DispelSpell(spMeditateEff) 	;remove blessing effects when you become a pariah
	player.DispelSpell(spBlessing)

	PrayWhileShunned()

	GnW_SPELL_RankDownFX.Cast(player, player)
EndFunction

Function ResetPariahState()
	timerPariah = maxPariahTime

	LogDebug("Resetting pariah state")
EndFunction

Function ExitPariahState()
	bIsPariah = false
	affinityPoints = 0
	;TODO: show "x welcomes you back to the fold" message

	LogDebug("Exiting pariah state")
EndFunction

;---------------------------------------------------------------------------------------------------------------------------
;--TIMERS---
;---------------------------------------------------------------------------------------------------------------------------
Function UpdateGameTime(float timeElapsed)		;Call into this from the mod manager - only the mod manager registers for updates
	If (timerDaily > 0.0)
		timerDaily -= timeElapsed;
		If (timerDaily <= 0.0)
			timerDaily = 24.0
			ResetDailyPointCaps()
		;	LogDebug("Reset daily point caps")
		EndIf
	EndIf

	If (timerPariah > 0.0)
		timerPariah -= timeElapsed;
		If (timerPariah <= 0.0)
			timerPariah = 0.0
			RankUp()
		EndIf
	EndIf

	If (timerNeglect > 0.0 && bIsCurrentGod && !bIsPariah) 	;neglect suspended when not current god
		timerNeglect -= timeElapsed;
		If (timerNeglect <= 0.0)
			LogDebug("Neglect timer expired")
			timerNeglect = maxNeglectTime
			UpdateAffinity(iPointsNeglect, isNeglect=true)
		EndIf
	EndIf

	If (timerOffering > 0.0 && bIsCurrentGod)
		timerOffering -= timeElapsed
		If (timerOffering <= 0.0)
			LogDebug("Offering timer expired")
			timerOffering = 0.0
			bCanMakeOffering = true
		EndIf
	EndIf

	If (timerPrayMeditate > 0.0 && bIsCurrentGod)
		timerPrayMeditate -= timeElapsed
		If (timerPrayMeditate <= 0.0)
			LogDebug("Pray/Meditate timer expired")
			timerPrayMeditate = 0.0
		EndIf
	EndIf

	If (timerPower > 0.0 && bIsCurrentGod)
		timerPower -= timeElapsed
		If (timerPower <= 0.0)
			RefreshPower()
		EndIf
	EndIf
EndFunction

;------------------------------------------------------
Event OnUpdate()
	reactionHateOnCooldown = false
	reactionLoveOnCooldown = false
EndEvent

;---------------------------------------------------------------------------------------------------------------------------
;--Helper Functions---
;---------------------------------------------------------------------------------------------------------------------------
Function SetCurrentGod(bool val)
	If (val == true && bIsCurrentGod == false) ;Switching to this god from another
		bIsCurrentGod = val
		reactionLoveOnCooldown = false
		reactionHateOnCooldown = false
		UpdatePowersAndAbilities()
		
;		LogDebug("SetCurrentGod() - " + _godName + " is current god")
		
	Elseif (val == false && bIsCurrentGod == true) 	;switching to another god from this one
		bIsCurrentGod = val
		RemovePowersAndAbilities()

;		LogDebug("SetCurrentGod() - " + _godName + " is NOT current god")
	EndIf
EndFunction

;------------------------------------------------------
Function UpdatePowersAndAbilities()
	If (!bIsCurrentGod)
		Return
	Endif

	If (affinityRank == -1)
		bAllowCrafting = false
		player.RemoveSpell(GnW_POW_Meditate)
		player.RemoveSpell(spAbility)
		player.RemoveSpell(spPower)
		player.RemoveSpell(spGuardian)
		MakeMinionsFriendly(false)

	Elseif (affinityRank == 0)
		bAllowCrafting = false
		player.AddSpell(GnW_POW_Meditate)
		player.RemoveSpell(spAbility)
		player.RemoveSpell(spPower)
		player.RemoveSpell(spGuardian)
		MakeMinionsFriendly(false)

	Elseif (affinityRank == 1)
		bAllowCrafting = true
		player.AddSpell(GnW_POW_Meditate)
		player.RemoveSpell(spAbility)
		player.RemoveSpell(spPower)
		player.RemoveSpell(spGuardian)
		MakeMinionsFriendly(false)

	Elseif (affinityRank == 2)
		bAllowCrafting = true
		player.AddSpell(GnW_POW_Meditate)
		player.AddSpell(spAbility)
		player.RemoveSpell(spPower)
		player.RemoveSpell(spGuardian)
		MakeMinionsFriendly(false)

	Elseif (affinityRank == 3)
		bAllowCrafting = true
		player.AddSpell(GnW_POW_Meditate)
		player.AddSpell(spAbility)
		player.AddSpell(spPower)
		player.RemoveSpell(spGuardian)
		MakeMinionsFriendly(true)

	Elseif (affinityRank == 4)
		bAllowCrafting = true
		player.AddSpell(GnW_POW_Meditate)
		player.AddSpell(spAbility)
		player.AddSpell(spPower)
		player.AddSpell(spGuardian)
		MakeMinionsFriendly(true)

	Elseif (affinityRank == 5)
		bAllowCrafting = true
		player.AddSpell(GnW_POW_Meditate)
		player.AddSpell(spAbility)
		player.AddSpell(spPower)
		player.AddSpell(spGuardian)
		MakeMinionsFriendly(true)

	EndIf

;	LogDebug("UpdatePowersAbilities() for rank=" + affinityRank)
EndFunction

;------------------------------------------------------
Function RemovePowersAndAbilities()
	player.RemoveSpell(spAbility)
	player.RemoveSpell(spPower)
	player.RemoveSpell(spGuardian)
	player.RemoveSpell(GnW_POW_Meditate)
	MakeMinionsFriendly(false)

;	LogDebug("RemovePowersAbilities()")
EndFunction

Function ResetAbility()
	If (player.HasSpell(spAbility))
		player.RemoveSpell(spAbility)
		player.AddSpell(spAbility)
	EndIf
EndFunction

;------------------------------------------------------
Function RefreshPower()
	If (player.HasSpell(spPower))
		bCanUsePower = true
		timerPower = 0.0

		If (_godIndex == 8)
			If (((self as Quest) as GnW_PowerZenitharRefreshQuestScript).GnW_GLO_PowerZenithar_itemsCopied.GetValueInt() < 3)
				GnW_MSG_PowerReady.Show()
			EndIf
		Else
			GnW_MSG_PowerReady.Show()
		EndIf
	EndIf
EndFunction

;------------------------------------------------------
Function MakeMinionsFriendly(bool makeFriendly)
	If (makeFriendly)
		player.AddToFaction(minionAllyFaction)
	Else
		player.RemoveFromFaction(minionAllyFaction)
	EndIf
EndFunction

;------------------------------------------------------
Function ResetDailyPointCaps()
	dailyPointsStealPickpocket = 0
	dailyPointsKillSpecial = 0
	dailyPointsUseQuestItem = 0
	dailyPointsCannibal = 0
	dailyPointsNecromancy = 0
	dailyPointsVampireFeed = 0
	dailyPointsWerewolfFeed = 0
EndFunction

;------------------------------------------------------
String Function GetName()
	Return _godName
EndFunction

;---------------------------------------------------------------------------------------------------------------------------
;--TESTING ONLY--
;---------------------------------------------------------------------------------------------------------------------------
GlobalVariable property GnW_GLO__Debug auto	 ;;turn on/off debug messages
Message property GnW_MSG__AffinityStatus auto

Function ShowStatus()
	StatusMenu()
EndFunction

Function StatusMenu()
	int choice = GnW_MSG__AffinityStatus.Show(_godIndex, affinityRank, affinityPoints, timerPrayMeditate, timerOffering, timerNeglect, timerPariah, timerPower)
	If (choice == 0)
		Return
	Elseif (choice == 1)
		UpdateAffinity(50)
		StatusMenu()
	Elseif (choice == 2)
		UpdateAffinity(10)
		StatusMenu()
	Elseif (choice == 3)
		UpdateAffinity(-10)
		StatusMenu()
	Elseif (choice == 4)
		UpdateAffinity(-50)
		StatusMenu()
	Elseif (choice == 5)
		ResetGod()
		StatusMenu()
	EndIf
EndFunction

Function ShowDebugMessage(string msg)
	bool showDebug = GnW_GLO__Debug.GetValue() as Bool
	If (showDebug)
		Debug.Notification(msg)
	EndIf
EndFunction

Function LogDebug(string msg)
	Debug.Trace("[GodQuestScript #" + _godIndex + "] " + msg)
EndFunction

