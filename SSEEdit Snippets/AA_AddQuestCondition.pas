unit AddGetStageDoneCondition;



function Initialize: integer;
begin

end;
// called for every record selected in xEdit
function Process(e: IInterface): integer;
var
  Quest: IInterface;
  Conditions, NewCondition: IInterface;
  StageNumber: string;
begin
  // Set the stage number for GetStageDone condition
  StageNumber := '0'; // Change this value as needed

  // Get the selected quest
  Quest := e;
  if not Assigned(Quest) then
  begin
    AddMessage('No quest selected, exiting script.');
    Result := 1;
    Exit;
  end;

  // Find or create the Conditions subrecord
  Conditions := ElementByPath(Quest, 'Conditions');
  if not Assigned(Conditions) then
    Conditions := Add(Quest, 'Conditions', True);

  if not Assigned(Conditions) then
  begin
    AddMessage('Failed to create Conditions, exiting script.');
    Result := 1;
    Exit;
  end;

  // Add a new condition
  NewCondition := ElementAssign(Conditions, HighInteger, nil, False);
  if not Assigned(NewCondition) then
  begin
    AddMessage('Failed to add new condition, exiting script.');
    Result := 1;
    Exit;
  end;

  // Set condition properties
  SetElementEditValues(NewCondition, 'CTDA\Type', 1);
  SetElementEditValues(NewCondition, 'CTDA\Function', 'GetStageDone');
  SetElementEditValues(NewCondition, 'CTDA\Run On', 'Subject');
  SetElementEditValues(NewCondition, 'CTDA\Comparison Value', 1);

  AddMessage('Condition added: GetStageDone ' + StageNumber);
  Result := 0;
end;
end.
