{
Apply on FACT record
}
unit userscript;

// Called before processing
// You can remove it if script doesn't require initialization code
function Initialize: integer;
begin
  Result := 0;
end;

// called for every record selected in xEdit
function Process(e: IInterface): integer;
var
  targetFaction: IInterface;
  inputFactionEditorID: integer;
  inputFaction: IInterface;
  newRelation: IInterface;
begin
inputFactionEditorID := 931337; //druadach forsworn
  Result := 0;
  inputFaction := RecordByFormID(FileByLoadOrder(0), inputFactionEditorID, true);
  if not Assigned(inputFaction) then begin
    AddMessage('Input faction not found: ' + inputFactionEditorID);
    Result := 1;
    Exit;
  end;
  targetFaction := e;
  newRelation := Add(targetFaction, 'Relations', true);
  SetElementEditValues(newRelation, 'XNAM - Relation\Group Combat Reaction', 'Friend');
  SetElementEditValues(newRelation, 'XNAM - Relation\Faction', Name(inputFaction));

end;

// Called after processing
// You can remove it if script doesn't require finalization code
function Finalize: integer;
begin
  Result := 0;
end;

end.
