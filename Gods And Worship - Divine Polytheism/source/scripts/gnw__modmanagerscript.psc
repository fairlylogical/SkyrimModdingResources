Scriptname GnW__ModManagerScript extends Quest Conditional

Import Utility_ExtendedUtils

;---GOD INDEXES - should always be in this order when referenced!--
;0=Akatosh
;1=Arkay
;2=Dibella
;3=Julianos
;4=Kynareth
;5=Mara
;6=Stendarr
;7=Talos
;8=Zenithar
;9=Azura
;10=Boethiah
;11=ClavicusVile
;12=HermaMora
;13=Hircine
;14=Malacath
;15=MehrunesDagon
;16=Mephala
;17=Meridia
;18=MolagBal
;19=Namira
;20=Nocturnal
;21=Peryite
;22=Sanguine
;23=Sheogorath
;24=Vaermina

GlobalVariable property Survival_ModeEnabled auto

Int property GlobalCurrentGodIndex=-1 Auto Conditional hidden
Int property GlobalTempleHomeQuestStarted Auto Conditional hidden
bool property IsModReady auto conditional hidden
bool property IsVampireLord auto conditional hidden
bool property IsWerewolf auto conditional hidden
bool property IsCharityActive auto conditional hidden
Int property NPCKillsRegistered auto conditional hidden

;MCM options
bool property IsNeglectEnabled = true auto conditional hidden

GnW_GodQuestScript[] property godQuestScripts Auto
GnW__JoinTempleManagerScript property joinTempleManager auto
Formlist property GnW_LIST__QuestsToStart Auto

Spell[] property TestStatusSpells Auto
Spell[] property ShrineBlessings Auto
Idle property IdleSilentBow Auto

MiscObject property Gold001 Auto
Message property GnW_MSG__ModStatusUpdateFound Auto
Message property GnW_MSG__ModStatusUpdateDone Auto
Message property GnW_MSG_OfferingPrompt Auto
Message property GnW_MSG_OfferingPrompt_already Auto
Message property GnW_MSG_OfferingPrompt_choose Auto
Message property GnW_MSG_OfferingPrompt_joinTemple Auto
Message property GnW_MSG_OfferingPrompt_notEnoughGold auto
GlobalVariable property GnW_GLO__Debug auto
GlobalVariable property GnW_GLO__DevMode auto

Formlist property GnW_LIST_PlayerSpells auto
Formlist property GnW_LIST_PlayerPerks auto

ReferenceAlias property aliasCurrentGod Auto
ReferenceAlias property aliasCurrentGod_templeHome Auto
Actor[] property godActors Auto

Light property Torch01 auto

;---Local variables---
float gameTimeInterval = 1.0
float checkChargenDoneInterval = 5.0
float prevGameTime

bool survivalEnabled

Actor player
Float prevVersion
Bool doneUpdate18
Bool doneUpdate19
Bool doneUpdate21
Bool doneUpdate23
Bool doneUpdate25

;----------------------------------------------------------------------------------
;----------------------------------------------------------------------------------
Function StartMod()
	player = Game.GetPlayer()

	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].Start()
		i += 1
	EndWhile

	;--setup vanilla priests w/o needing to edit NPC records, for mod compatibility--
	AddPriestsToFactions()
	ChangePriestOutfits() 

	prevGameTime = Utility.GetCurrentGameTime()
	RegisterForSingleUpdateGameTime(gameTimeInterval)

	RegisterForSingleUpdate(checkChargenDoneInterval)
EndFunction

Function ShutdownMod()
	SwitchCurrentGod(-1)

	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].Stop()
		i += 1
	EndWhile

	StopQuests()
	RemovePlayerSpellsPerks()
	CheckSoundAdjust()

	IsModReady = false
EndFunction

;----------------------------------------------------------------------------------
Function CheckChargenDone()
	;Is the player in some sort of locked intro sequence, like the initial cart ride? If so, wait until that's done to start GnW.
	If (Game.IsMovementControlsEnabled() && Game.IsFightingControlsEnabled())
		UpdateMod()
		IsModReady = true

	Else
		RegisterForSingleUpdate(checkChargenDoneInterval)
	Endif
EndFunction

Event OnUpdate()
	CheckChargenDone()
EndEvent

;----------------------------------------------------------------------------------
Function UpdateMod()	
	If (SKSE.GetVersionRelease() > 0)
	Else
		Debug.MessageBox("ERROR: Gods and Worship requires SKSE to function! Make sure you have SKSE installed correctly in order to use this mod!")
	EndIf

	If (prevVersion < 2.7)	;;KEEP NUMBER INCREMENTED - also update version # in message
		GnW_MSG__ModStatusUpdateFound.Show()

		Float oldVersion = prevVersion
		prevVersion = 2.7	;;KEEP NUMBER INCREMENTED

		StartQuests()
		AddPlayerSpellsPerks()
		PopulateLeveledLists()

		;;Changes for people updating to 1.8 on an existing save
		If (oldVersion > 0 && !doneUpdate18)
			doneUpdate18 = true

			ChangePriestOutfits()  
			
			godQuestScripts[0].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[1].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[2].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[3].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[4].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[5].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[6].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[7].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[8].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[9].iPointsSoulTrapBlackSoul = -16
			godQuestScripts[14].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[16].iPointsSoulTrapBlackSoul = 1
			godQuestScripts[17].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[18].iPointsSoulTrapBlackSoul = 1
			godQuestScripts[24].iPointsSoulTrapBlackSoul = 1

			godQuestScripts[15].HatedGodIndexes = new Int[3]
			godQuestScripts[15].HatedGodIndexes[0] = 0
			godQuestScripts[15].HatedGodIndexes[1] = 18
			godQuestScripts[15].HatedGodIndexes[2] = 20

			godQuestScripts[20].HatedGodIndexes = new Int[3]
			godQuestScripts[20].HatedGodIndexes[0] = 9
			godQuestScripts[20].HatedGodIndexes[1] = 15
			godQuestScripts[20].HatedGodIndexes[2] = 17

			godQuestScripts[19].ResetAbility()
			godQuestScripts[20].ResetAbility()
		EndIf

		If (oldVersion > 0 && !doneUpdate19)
			doneUpdate19 = true
			
			player.RemoveSpell(GnW_LIST_PlayerSpells.GetAt(0) as Spell)	
			If (!IsSkyUIInstalled())
				player.AddSpell(GnW_LIST_PlayerSpells.GetAt(0) as Spell, abVerbose = false) ;Refresh config spell, if not using skyui
			EndIf
		EndIf

		If (oldVersion > 0 && !doneUpdate21)
			doneUpdate21 = true

			godQuestScripts[8].iPointsKillStrongCreatureUndead = 3
		EndIf

		If (oldVersion > 0 && !doneUpdate23)
			doneUpdate23 = true

			Quest q = Quest.GetQuest("GnW_GodSanguineQuest")
			(q as GnW_SanguineAlcoholHandling).StoreOrigValues()
		EndIf

		If (oldVersion > 0 && !doneUpdate25)
			doneUpdate25 = true
			
			godQuestScripts[5].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[6].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[7].iPointsSoulTrapBlackSoul = -8
			godQuestScripts[8].iPointsSoulTrapBlackSoul = -8
		EndIf

		GnW_MSG__ModStatusUpdateDone.Show()
	EndIf
EndFunction

;----------------------------------------------------------------------------------
Function StartQuests()
	;--start quests here, to make sure they are initialized in the right order--
	Int i = 0
	While (i < GnW_LIST__QuestsToStart.GetSize())
		Quest q = GnW_LIST__QuestsToStart.GetAt(i) as Quest
		If (!q.IsRunning())
			q.Start()	
		EndIf
		i += 1
	EndWhile
EndFunction

Function StopQuests()
	Int i = 0
	While (i < GnW_LIST__QuestsToStart.GetSize())
		Quest q = GnW_LIST__QuestsToStart.GetAt(i) as Quest
		q.Stop()
		i += 1
	EndWhile
EndFunction

;----------------------------------------------------------------------------------
Function AddPlayerSpellsPerks()
	int i = 0
	While (i < GnW_LIST_PlayerSpells.GetSize())
		Spell sp = GnW_LIST_PlayerSpells.GetAt(i) as Spell
		If (i != 0 || !IsSkyUIInstalled())	;if config power, don't add if SkyUI is installed
			player.AddSpell(sp, false)
		EndIf
		i += 1
	EndWhile

	i = 0
	While (i < GnW_LIST_PlayerPerks.GetSize())
		Perk pk = GnW_LIST_PlayerPerks.GetAt(i) as Perk
		If (!player.HasPerk(pk))
			player.AddPerk(pk)
		EndIf
		i += 1
	EndWhile

EndFunction

Function RemovePlayerSpellsPerks()
	int i = 0
	While (i < TestStatusSpells.Length)
		player.RemoveSpell(TestStatusSpells[i])
		i += 1
	EndWhile

	i = 0
	While (i < GnW_LIST_PlayerSpells.GetSize())
		Spell sp = GnW_LIST_PlayerSpells.GetAt(i) as Spell
		player.RemoveSpell(sp)
		i += 1
	EndWhile

	i = 0
	While (i < GnW_LIST_PlayerPerks.GetSize())
		Perk pk = GnW_LIST_PlayerPerks.GetAt(i) as Perk
		player.RemovePerk(pk)
		i += 1
	EndWhile

EndFunction

;----------------------------------------------------------------------------------------------------------------------------------------
;----------------------------------------------------------------------------------------------------------------------------------------
;--SETUP PRIESTS--
;----------------------------------------------------------------------------------------------------------------------------------------
Faction property GnW_FACT_NPCPriesthood auto
Faction[] property NPCPriestFactions auto
Actor[] property NPCPriests Auto
Outfit[] property NPCPriestOutfits Auto

Function ChangePriestOutfits()
	int	i = 0
	While (i < NPCPriests.Length && i < NPCPriestOutfits.Length)
		Actor priest = NPCPriests[i]
		Outfit newOutfit = NPCPriestOutfits[i]
		If (newOutfit != none)
			priest.SetOutfit(newOutfit)
		EndIf

		i += 1
	EndWhile
EndFunction

Function AddPriestsToFactions()	;Add vanilla NPC priests to the faction that marks them as "unrecruitable". Mods can add this faction to their priests manually.
	int	i = 0
	While (i < NPCPriests.Length)
		Actor priest = NPCPriests[i]

		If (!priest.IsInFaction(GnW_FACT_NPCPriesthood))
			priest.AddToFaction(GnW_FACT_NPCPriesthood)
		EndIf	

		If (NPCPriestFactions[i] != none && !priest.IsInFaction(NPCPriestFactions[i]))			;factions for individual gods, to determine loyalty
			priest.AddToFaction(NPCPriestFactions[i])
		EndIf	
	
		i += 1
	EndWhile
EndFunction

;----------------------------------------------------------------------------------------------------------------------------------------
;----------------------------------------------------------------------------------------------------------------------------------------
;--POPULATE LEVELED LISTS--
;----------------------------------------------------------------------------------------------------------------------------------------
Formlist property listBookLItemTargets auto
Formlist property listBookListSources auto

Function PopulateLeveledLists()
	Int testCount

	Int i = 0
	While (i < listBookLItemTargets.GetSize() && i < listBookListSources.GetSize())
		LeveledItem targetLItem = listBookLItemTargets.GetAt(i) as LeveledItem
		Formlist sourceList = listBookListSources.GetAt(i) as Formlist

		targetLItem.Revert()  

		Int j = 0
		While (j < sourceList.GetSize())
			Book b = sourceList.GetAt(j) as Book
			If (b)
				targetLItem.AddForm(b, 1, 1)
				testCount += 1
			EndIf

			j += 1
		EndWhile

		i += 1
	EndWhile

	ShowDebugMessage(testCount + " lorebooks added to leveled lists")
EndFunction

;----------------------------------------------------------------------------------
;----------------------------------------------------------------------------------
Keyword property GnW_K_AkatoshStopTime Auto
Keyword property GnW_K_VaerminaDreamStride auto
SoundCategory property sndCatAmbMusic Auto
SoundCategory property sndCatVoices Auto
SoundCategory property sndCatFootsteps Auto

Function CheckSoundAdjust()
	If (player.HasMagicEffectWithKeyword(GnW_K_AkatoshStopTime) || player.HasMagicEffectWithKeyword(GnW_K_VaerminaDreamStride ))
		sndCatAmbMusic.Mute()
		sndCatFootsteps.Mute()
		If (player.HasMagicEffectWithKeyword(GnW_K_AkatoshStopTime))
			sndCatVoices.Mute()
		EndIf
	Else
		sndCatAmbMusic.UnMute()
		sndCatVoices.UnMute()
		sndCatFootsteps.UnMute()
	EndIf
EndFunction

;----------------------------------------------------------------------------------------------------------------------------------------
;----------------------------------------------------------------------------------------------------------------------------------------
;--HANDLE PLAYER ACTIONS--
;----------------------------------------------------------------------------------------------------------------------------------------
Function ShowOfferingPrompt(ObjectReference shrine, int godIndex, bool showSpecialPrompt=false, int templeIndex = -1)
;	ShowDebugMessage("SHOW OFFERING PROMPT FOR " + godIndex)

	bool exit
	bool madeOffering
	bool prayed
	Int choice 		

	survivalEnabled = false
	If (Survival_ModeEnabled)
		survivalEnabled = Survival_ModeEnabled.GetValueInt() == 1		
	EndIf

	godQuestScripts[godIndex].fakeGodActor.RemoveAllItems()	
	
	;--Trying to join a temple--
	If (showSpecialPrompt)  
		;ShowDebugMessage("SHOW SPECIAL OFFERING PROMPT FOR " + godIndex + ", temple=" + templeIndex)
		;handle checking for the correct quest stage inside the perk!

		choice = ShowOfferingMenu(GnW_MSG_OfferingPrompt_joinTemple, godIndex, hasPrayOption = false)

		madeOffering = true
		If (choice == 3)
			exit = true
		EndIf
		
	;--Normal praying--
	Else		
		If (GlobalCurrentGodIndex != godIndex)
			choice = ShowOfferingMenu(GnW_MSG_OfferingPrompt_choose, godIndex)
		ElseIf (godQuestScripts[godIndex].bCanMakeOffering)
			choice = ShowOfferingMenu(GnW_MSG_OfferingPrompt, godIndex)
		Else 
			 choice = ShowOfferingMenu(GnW_MSG_OfferingPrompt_already, godIndex)
		EndIf

		madeOffering = choice <= 2
		prayed = choice == 3 || choice == 4

		If (choice == 5)
			exit = true
		EndIf
	Endif

	;--Noped out--
	If (exit)
		Return
	EndIf

	;--Update god quest, get blessing--
	If (!survivalEnabled || prayed || madeOffering)
		Pray(godIndex, madeOffering)
		shrine.Activate(Game.GetPlayer())
	EndIf

	;--Join temple, if attempting to--
	If (templeIndex > -1)
		joinTempleManager.JoinTemple(templeIndex)	
	EndIf

	;--Show bow--
	If (madeOffering)		
		PlayOfferingBow()
	EndIf

EndFunction

Function ChooseGodRemote(ObjectReference shrine, int godIndex)
	Pray(godIndex, true)
	shrine.Activate(Game.GetPlayer())
	PlayOfferingBow()
EndFunction

Function PlayOfferingBow()
	;--Lock controls, force 3rd person--
	Bool wasInFirstPerson = Game.GetCameraState() == 0
	Game.DisablePlayerControls(abMovement = true, abFighting = true, abCamSwitch = true)
	Game.ForceThirdPerson()
	player.SetGhost(true)

	;--Put away weapons/torches--
	Bool waitForSheathe = player.IsWeaponDrawn()
	player.SheatheWeapon()
	If (player.GetEquippedItemType(0) == 11 || player.GetEquippedItemType(1) == 11)	;torch
		player.UnequipItem(Torch01) 
	EndIf
	If (waitForSheathe)
		Utility.Wait(1.75)
	EndIf

	;--Show idle--
	Debug.SendAnimationEvent(player, "IdleSilentBow")
	Utility.Wait(3)
	Debug.SendAnimationEvent(player, "IdleStop")

	;--Re-enable controls, reset camera--
	If (wasInFirstPerson)
		Game.ForceFirstPerson()
	EndIf
	Game.EnablePlayerControls()
	player.SetGhost(false)
EndFunction

Int Function ShowOfferingMenu(Message menu, int godIndex, bool hasPrayOption = true)
	bool madeOffering
	bool paidToPray
	int choice
	int lastChoice = 3

	If (!hasPrayOption)
		lastChoice = 2
	EndIf	

	While (!madeOffering && !paidToPray &&  choice <= lastChoice)
		choice = menu.Show()

		If (choice == 0)
			godQuestScripts[godIndex].fakeGodActor.ShowGiftMenu(true, godQuestScripts[godIndex].offeringItemsList, godQuestScripts[godIndex].offerStolenItems)
			If (godQuestScripts[godIndex].fakeGodActor.GetNumItems() > 0)
				madeOffering = true
				godQuestScripts[godIndex].fakeGodActor.RemoveAllItems()
			EndIf

		Elseif (choice == 1 || choice == 2)
			int value = 50
			If (survivalEnabled) 
				value = 100
			EndIf

			If (player.GetItemCount(Gold001) >= value)
				player.RemoveItem(Gold001, value)
				madeOffering = true
			Else
				GnW_MSG_OfferingPrompt_notEnoughGold.Show()
			EndIf

		Elseif (hasPrayOption && choice == 3) ;paying to pray in survival mode
			If (player.GetItemCount(Gold001) >= 25)
				player.RemoveItem(Gold001, 25)
				paidToPray = true
			Else
				GnW_MSG_OfferingPrompt_notEnoughGold.Show()
			EndIf

		EndIf
	EndWhile

	Return choice
EndFunction

Function Pray(Int godIndex, bool madeOffering=true)
	;Check for completion of main quest
;	If (madeOffering && questMain.GetStageDone(20) && !questMain.GetStageDone(200))
;		questMain.SetStage(100)
;	Endif
	
	If (madeOffering && GlobalCurrentGodIndex != godIndex)
		SwitchCurrentGod(godIndex)
	Endif

	godQuestScripts[godIndex].Pray(madeOffering)

	int i = 0
	While (i < godQuestScripts.Length)
		If (i != godIndex)
			godQuestScripts[i].PrayOther(godIndex)
		Endif
		i += 1
	EndWhile
EndFunction

Function Meditate()
	godQuestScripts[GlobalCurrentGodIndex].Meditate()
EndFunction

Function PrayWhileShunned(Int godIndex)
	ShowDebugMessage("Trying to pray while shunned")
	godQuestScripts[godIndex].PrayWhileShunned()
EndFunction

Function Proselytize(Int godIndex)
	ShowDebugMessage("PROSELYTIZE")
	godQuestScripts[godIndex].Proselytize()

	int i = 0
	While (i < godQuestScripts.Length)
		If (i != godIndex)
			godQuestScripts[i].ProselytizeOther(GlobalCurrentGodIndex)
		Endif
		i += 1
	EndWhile
EndFunction

Function CompleteTempleErrand(Int points, Int templeIndex)
	If (GlobalCurrentGodIndex ==  -1)
		return
	EndIf

	If (templeIndex == joinTempleManager.indexDivines && GlobalCurrentGodIndex < 9)
		godQuestScripts[GlobalCurrentGodIndex].UpdateAffinity(points)

	ElseIf (templeIndex == joinTempleManager.indexDibella && GlobalCurrentGodIndex == 2)
		godQuestScripts[GlobalCurrentGodIndex].UpdateAffinity(points)

	ElseIf (templeIndex == joinTempleManager.indexKynareth && GlobalCurrentGodIndex == 4)
		godQuestScripts[GlobalCurrentGodIndex].UpdateAffinity(points)

	ElseIf (templeIndex == joinTempleManager.indexMara && GlobalCurrentGodIndex == 5)
		godQuestScripts[GlobalCurrentGodIndex].UpdateAffinity(points)

	ElseIf (templeIndex == joinTempleManager.indexTalos && GlobalCurrentGodIndex == 7)
		godQuestScripts[GlobalCurrentGodIndex].UpdateAffinity(points)

	ElseIf (templeIndex == joinTempleManager.indexReclamations && (GlobalCurrentGodIndex == 9 || GlobalCurrentGodIndex == 10 || GlobalCurrentGodIndex == 16))
		godQuestScripts[GlobalCurrentGodIndex].UpdateAffinity(points)

	EndIf
EndFunction

Function GiveCharity()
	ShowDebugMessage("CHARITY")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].GiveCharity()
		i += 1
	EndWhile
EndFunction

Function Pickpocket(Bool valuable)
	ShowDebugMessage("PICKPOCKET")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].Pickpocket(valuable)
		i += 1
	EndWhile
EndFunction

Function Steal(Bool valuable)
	ShowDebugMessage("STEAL")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].Steal(valuable)
		i += 1
	EndWhile
EndFunction

Function Bribe()
	ShowDebugMessage("BRIBE")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].Bribe()
		i += 1
	EndWhile
EndFunction

Function Intimidate()
	ShowDebugMessage("INTIMIDATE")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].Intimidate()
		i += 1
	EndWhile
EndFunction

Function Persuade()
	ShowDebugMessage("PRESUADE")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].Presuade()
		i += 1
	EndWhile
EndFunction

Function Brawl()
	ShowDebugMessage("BRAWL")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].Brawl()
		i += 1
	EndWhile
EndFunction

Function Assault(Actor victim)
	ShowDebugMessage("ASSAULT")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].Assault(victim)
		i += 1
	EndWhile
EndFunction

Function Murder(Actor victim)
	ShowDebugMessage("MURDER")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].Murder(victim)
		i += 1
	EndWhile
EndFunction

Function KillSpecial(Actor victim)
	ShowDebugMessage("KILLED UNDEAD/DAEDRA/WEREBEAST")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].KillSpecial(victim)
		i += 1
	EndWhile
EndFunction

Function Cannibalism()
	ShowDebugMessage("CANNIBALISM")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].Cannibalism()
		i += 1
	EndWhile
EndFunction

Function Necromancy()
	ShowDebugMessage("NECROMANCY")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].Necromancy()
		i += 1
	EndWhile
EndFunction

Function DaedraSummon()
	ShowDebugMessage("DAEDRA SUMMON")
	(godQuestScripts[6] as GnW_GodStendarrQuestScript).DaedraSummon()	;only applies to Stendarr
EndFunction

Bool property becameVampireThruShrine auto hidden
Function BecomeVampire()
	ShowDebugMessage("BECAME VAMPIRE")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].BecomeVampire(becameVampireThruShrine)
		i += 1
	EndWhile

	becameVampireThruShrine = false
EndFunction

Function VampireFeed()
	ShowDebugMessage("VAMPIRE FEED")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].VampireFeed()
		i += 1
	EndWhile
EndFunction

Function VampireLordTransform()
	ShowDebugMessage("VAMPIRE TRANSFORM")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].VampireLordTransform()
		i += 1
	EndWhile
EndFunction

Function VampireCure()
	ShowDebugMessage("CURED VAMPIRISM")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].VampireCure()
		i += 1
	EndWhile
EndFunction

Bool property becameWerewolfThruShrine auto hidden
Function BecomeWerewolf()
	ShowDebugMessage("BECAME WEREWOLF, thru shrine = " + becameWerewolfThruShrine)
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].BecomeWerewolf(becameWerewolfThruShrine)
		i += 1
	EndWhile

	becameWerewolfThruShrine = false
EndFunction

Function WerewolfFeed()
	ShowDebugMessage("WEREWOLF FEED")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].WerewolfFeed()
		i += 1
	EndWhile
EndFunction

Function WerewolfTransform()
	ShowDebugMessage("WEREWOLF TRANSFORM")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].WerewolfTransform()
		i += 1
	EndWhile
EndFunction

Function WerewolfCure()
	ShowDebugMessage("CURED WEREWOLFISM")
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].WerewolfCure()
		i += 1
	EndWhile
EndFunction

Function Marriage()
	ShowDebugMessage("MARRIAGE")
  	int i = 0
  	While (i < godQuestScripts.Length)
    		godQuestScripts[i].Marriage()
    		i += 1
  	EndWhile
EndFunction

Function MarriageBreakup()
	ShowDebugMessage("MARRIAGE BREAKUP")
  	int i = 0
  	While (i < godQuestScripts.Length)
    		godQuestScripts[i].MarriageBreakup()
    		i += 1
  	EndWhile
EndFunction

Function Adopt()
	ShowDebugMessage("ADOPT")
  	int i = 0
  	While (i < godQuestScripts.Length)
    		godQuestScripts[i].Adopt()
    		i += 1
  	EndWhile
EndFunction

Function UseQuestItem(Enchantment ench)
	ShowDebugMessage("USE QUEST ITEM")
	int i = 0
	While (i < godQuestScripts.Length)
    		godQuestScripts[i].UseQuestItem(ench)
    		i += 1
  	EndWhile
EndFunction

Function SoulTrapBlackSoul(Int count)
	ShowDebugMessage("SOUL TRAP BLACK SOUL, count = " + count)
	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].SoulTrapBlackSoul(count)
		i += 1
	EndWhile
EndFunction

;----------------------------------------------------------------------------------
;--Events---
;----------------------------------------------------------------------------------
Event OnUpdateGameTime()
	;--Calculate hours elasped--
	Float curGameTime = Utility.GetCurrentGameTime()
	Int hours = ((curGameTime - prevGameTime) *24.0) As Int
	prevGameTime = curGameTime
	
	If (hours == 0)
		hours = 1
	EndIf
	;Debug.Notification("Hours passed since last update: " + hours)

	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].UpdateGameTime(hours)
		i += 1
	EndWhile

	RegisterForSingleUpdateGameTime(gameTimeInterval)
EndEvent

;----------------------------------------------------------------------------------
;---Helper Functions---
;----------------------------------------------------------------------------------
Function SwitchCurrentGod(int godIndex)
	;Send -1 when removing your chosen god (entering pariah state)
	GlobalCurrentGodIndex = godIndex

	int i = 0
	While (i < godQuestScripts.Length)
		godQuestScripts[i].SetCurrentGod(false)
		i += 1
	EndWhile

	If (godIndex != -1)
		godQuestScripts[godIndex].SetCurrentGod(true)
		aliasCurrentGod.ForceRefTo(godActors[godIndex])
		aliasCurrentGod_templeHome.ForceRefTo(godActors[godIndex])
	Elseif (godIndex == -1)
		aliasCurrentGod.Clear()
		aliasCurrentGod_templeHome.Clear()
		i = 0
		While (i < ShrineBlessings.Length)
			player.DispelSpell(ShrineBlessings[i])
			i += 1
		EndWhile
	EndIf

	ShowDebugMessage("Switched god to: " + GlobalCurrentGodIndex)
EndFunction

Int Function GetRankForCurrentGod()
	If (GlobalCurrentGodIndex == -1)
		Return -1
	EndIf

	Return godQuestScripts[GlobalCurrentGodIndex].affinityRank
EndFunction

Function ShowDebugMessage(string msg)
	bool showDebug = GnW_GLO__Debug.GetValue() as Bool
	If (showDebug)
		Debug.Trace("[ModManager] " + msg)
	EndIf
EndFunction

Bool Function IsSkyUIInstalled()
	Return Game.IsPluginInstalled("SkyUI_SE.esp")
EndFunction
