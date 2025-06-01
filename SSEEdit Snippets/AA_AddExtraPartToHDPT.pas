{
Apply to HDPT
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
  headPart, extraPart: IInterface;
begin
  Result := 0;
  
    AddMessage('Processing: ' + Name(e));
    
  if GetElementEditValues(e, 'DATA - Flags') = '11' then
  begin;
    extraPart := RecordByFormID(GetFile(e), $FE116DFA, True);
    AddMessage('Its a non extra part, editing with extra part ' + Name(extraPart) + ' of ' + GetFileName(e));
    ElementAssign(ElementByPath(e, 'HNAM'), HighInteger, extraPart, False);
  end;


  // processing code goes here

end;

// Called after processing
// You can remove it if script doesn't require finalization code
function Finalize: integer;
begin
  Result := 0;
end;

end.
