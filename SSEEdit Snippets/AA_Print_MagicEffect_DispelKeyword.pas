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
  Flag: integer;
begin
  Result := 0;
  Flag := GetNativeValue(ElementByPath(e, 'Magic Effect Data\DATA - Data\Flags'));
  AddMessage('Path at : ' +  IntToStr(Flag)) ;
  if (Flag and 256) <> 0 then
  begin
  // comment this out if you don't want those messages
  AddMessage('Path at : ' +  IntToStr(Flag));
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
