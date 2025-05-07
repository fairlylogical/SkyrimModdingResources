{
  Apply on script wrapper (ex : magic effect)
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
  QuestRewardDict: THashedStringList;
  Key, Value: string;
  MagicEffect, Scripts, FirstScript, Properties, NewProperty: IInterface;
  i: Integer;
begin
  QuestRewardDict := THashedStringList.Create;
  QuestRewardDict.Add('DA01Reward1=00063B27'); //azure star
  QuestRewardDict.Add('DA01Reward2=00063B29'); //black star
  QuestRewardDict.Add('DA09Reward1=0004E4EE'); //dawnbreaker
  QuestRewardDict.Add('DA08Reward1=0004A38F'); //ebonyblade
  QuestRewardDict.Add('DA02Reward1=00052794'); //ebonymail
  QuestRewardDict.Add('DA10Reward1=000233E3'); //molag mace
  QuestRewardDict.Add('DA03Reward1=000D2846'); //clavicule mask
  QuestRewardDict.Add('DA07Reward1=000240D2'); //mehrunes razor
  QuestRewardDict.Add('DA04Reward1=0001A332'); //oghnum
  QuestRewardDict.Add('DA05Reward1=0002AC60'); //ring of hircine
  QuestRewardDict.Add('DA05Reward2=0002AC61'); //savior hide
  QuestRewardDict.Add('DA11Reward1=0002C37B'); //ring of namira
  QuestRewardDict.Add('DA14Reward1=0001CB36'); //sanguine rose
  QuestRewardDict.Add('DA16Reward1=00035066'); //skull of corruption
  QuestRewardDict.Add('DA13Reward1=00045F96'); //spell breaker
  QuestRewardDict.Add('DA06Reward1=0002ACD2'); //volendrung
  QuestRewardDict.Add('DA15Reward1=0002AC6F'); //wabbajack

  // Get the selected Magic Effect
  MagicEffect := e;
  if not Assigned(MagicEffect) then
  begin
    AddMessage('No Magic Effect selected, exiting script.');
    Result := 1;
    Exit;
  end;

  // Locate the 'VMAD - Virtual Machine Adapter' section where scripts are stored
  Scripts := ElementByPath(MagicEffect, 'VMAD - Virtual Machine Adapter\Scripts');
  if not Assigned(Scripts) then
  begin
    AddMessage('No scripts found on this Magic Effect, exiting.');
    Result := 1;
    Exit;
  end;

  // Get the first script
  FirstScript := ElementByIndex(Scripts, 0);
  if not Assigned(FirstScript) then
  begin
    AddMessage('No scripts attached to the Magic Effect, exiting.');
    Result := 1;
    Exit;
  end;

  // Find or create the Properties subrecord
  Properties := ElementByPath(FirstScript, 'Properties');
  if not Assigned(Properties) then
    Properties := Add(FirstScript, 'Properties', True);

  if not Assigned(Properties) then
  begin
    AddMessage('Failed to create Properties, exiting script.');
    Result := 1;
    Exit;
  end;

      // Iterate through the list
    for i := 0 to QuestRewardDict.Count - 1 do
    begin
      NewProperty := ElementAssign(Properties, HighInteger, nil, False);
      Key := QuestRewardDict.Names[i];   // Get key (left part before '=')
      Value := QuestRewardDict.ValueFromIndex[i]; // Get value (right part after '=')
          // Set property values
    SetElementEditValues(NewProperty, 'propertyName', Key); // Property Name
    SetElementEditValues(NewProperty, 'Type', 'Object'); // Property Type: Object
    SetElementEditValues(NewProperty, 'Value\Object Union\Object v2\FormID', Value); // FormID Reference

    AddMessage('Property "' + Key + '" added with value ' + Value);
    end;

  Result := 0;
end;

// Called after processing
// You can remove it if script doesn't require finalization code
function Finalize: integer;
begin
  Result := 0;
end;

end.
