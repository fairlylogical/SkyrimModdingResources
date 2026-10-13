Scriptname GPF_PlayerAlias extends ReferenceAlias
{Keeps the list of harvestables that the Green Pact forbids up to date.

The perk that blocks the harvest can only test the activated object against a
form list, so this script fills that list on every game load: every plant
whose yield carries the GreenPactForbidden keyword, plus every activator and
piece of furniture that carries it directly.}

Keyword Property GreenPactForbidden Auto
FormList Property ForbiddenHarvestables Auto
Perk Property ForbidHarvestPerk Auto
GlobalVariable Property FollowsGreenPact Auto

; SKSE form types
Int Property kActivator = 24 AutoReadOnly
Int Property kTree = 38 AutoReadOnly
Int Property kFlora = 39 AutoReadOnly
Int Property kFurniture = 40 AutoReadOnly

Event OnInit()
	Setup()
EndEvent

Event OnPlayerLoadGame()
	Setup()
EndEvent

Function Setup()
	Actor player = Game.GetPlayer()
	If !player.HasPerk(ForbidHarvestPerk)
		player.AddPerk(ForbidHarvestPerk)
	EndIf
	RebuildList()
	Float pact = -1.0
	If FollowsGreenPact
		pact = FollowsGreenPact.GetValue()
	EndIf
	Debug.Trace("[GreenPactForest] " + ForbiddenHarvestables.GetSize() + " harvestables forbidden, perk present: " + player.HasPerk(ForbidHarvestPerk) + ", follows the Green Pact: " + pact)
EndFunction

; Keyword distribution can change between sessions, so entries that are no
; longer forbidden are dropped one by one instead of emptying the list first:
; that would leave everything harvestable until the scan is done.
Function RebuildList()
	Int i = ForbiddenHarvestables.GetSize()
	While i > 0
		i -= 1
		Form listed = ForbiddenHarvestables.GetAt(i)
		If !IsForbidden(listed)
			ForbiddenHarvestables.RemoveAddedForm(listed)
		EndIf
	EndWhile

	Keyword[] marked = new Keyword[1]
	marked[0] = GreenPactForbidden
	AddForbidden(PO3_SKSEFunctions.GetAllForms(kTree))
	AddForbidden(PO3_SKSEFunctions.GetAllForms(kFlora))
	AddForbidden(PO3_SKSEFunctions.GetAllForms(kActivator, marked))
	AddForbidden(PO3_SKSEFunctions.GetAllForms(kFurniture, marked))
EndFunction

Function AddForbidden(Form[] akForms)
	Int i = akForms.Length
	While i > 0
		i -= 1
		If IsForbidden(akForms[i]) && !ForbiddenHarvestables.HasForm(akForms[i])
			ForbiddenHarvestables.AddForm(akForms[i])
		EndIf
	EndWhile
EndFunction

; Only harvestables and other activators count, so that a forbidden item lying
; around loose can still be picked up.
Bool Function IsForbidden(Form akBase)
	Form produce
	If akBase as TreeObject
		produce = (akBase as TreeObject).GetIngredient()
	ElseIf akBase as Flora
		produce = (akBase as Flora).GetIngredient()
	ElseIf !(akBase as Activator)
		Return False
	EndIf
	Return akBase.HasKeyword(GreenPactForbidden) || YieldsForbidden(produce, 0)
EndFunction

; Requiem replaces most harvest yields with leveled lists, so look inside them.
Bool Function YieldsForbidden(Form akItem, Int aiDepth)
	If !akItem
		Return False
	EndIf
	LeveledItem list = akItem as LeveledItem
	If !list
		Return akItem.HasKeyword(GreenPactForbidden)
	EndIf
	If aiDepth >= 4
		Return False
	EndIf
	Int i = list.GetNumForms()
	While i > 0
		i -= 1
		If YieldsForbidden(list.GetNthForm(i), aiDepth + 1)
			Return True
		EndIf
	EndWhile
	Return False
EndFunction
