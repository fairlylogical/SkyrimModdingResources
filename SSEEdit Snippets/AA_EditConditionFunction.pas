{
Apply on condition wrapper (ex : Constructible Object)
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
  Conditions, NewCondition: IInterface;
  i: integer;
begin
  Conditions := ElementByPath(e, 'Conditions');
  for i := 0 to Pred(ElementCount(Conditions)) do
   begin
   NewCondition := ElementByIndex(Conditions, i);
   if GetElementEditValues(NewCondition, 'CTDA\Function') = 'GetStageDone' then
   begin
     SetElementEditValues(NewCondition, 'CTDA\Function', 'GetQuestCompleted');
   end;
   AddMessage(IntToStr(i));
   end;
 
end;

// Called after processing
// You can remove it if script doesn't require finalization code
function Finalize: integer;
begin
  Result := 0;
end;

end.
