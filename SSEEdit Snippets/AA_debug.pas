{
  New script template, only shows processed records
  Assigning any nonzero value to Result will terminate script
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
  parentLoc: string;
begin
  Result := 0;
  parentLoc := 'ReachHoldLocation "the Reach" [LCTN:00016769]';
  if parentLoc = GetElementEditValues(e, 'PNAM - Parent Location') then
  begin
  AddMessage(BaseName(e)); 
  end ;
  // comment this out if you don't want those messages
  // processing code goes here

end;

// Called after processing
// You can remove it if script doesn't require finalization code
function Finalize: integer;
begin
  Result := 0;
end;

end.
