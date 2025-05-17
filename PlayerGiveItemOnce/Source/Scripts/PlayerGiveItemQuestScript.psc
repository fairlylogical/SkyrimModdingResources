Scriptname PlayerGiveItemQuestScript extends Quest  

Bool Property ItemsGiven = False Auto
FormList Property ItemsToGive Auto

Event OnInit()
    If !ItemsGiven && ItemsToGive
        int itemCount = ItemsToGive.GetSize()
        int i = 0
        While i < itemCount
            Form itemForm = ItemsToGive.GetAt(i)
            Game.GetPlayer().AddItem(itemForm, 1, true)
            i += 1
        EndWhile
        ItemsGiven = True
    EndIf
EndEvent