{
  Output meshes used in selected records
}
unit UserScript;

var
  slModels: TStringList;

function Initialize: integer;
begin
  // list of models, ignore duplicated ones
  slModels := TStringList.Create;
  slModels.Sorted := True;
  slModels.Duplicates := dupIgnore;
end;

function Process(e: IInterface): integer;
var
  BipedFlags: IInterface;
  FlagsValue, i, cnt: Int64;
  ModelPath: string;
begin
  // Ensure the selected record is ARMA (Armor)
  if Signature(e) <> 'ARMA' then
  begin
    AddMessage('ERROR: ' + Name(e) + ' is not an Armor (ARMO) record!');
    Exit;
  end;

  // Get the Biped Body Template field
  BipedFlags := ElementByPath(e, 'BOD2 - Biped Body Template\First Person Flags');
  if not Assigned(BipedFlags) then
  begin
    AddMessage('ERROR: ' + Name(e) + ' has no Biped Body Template!');
    Exit;
  end;

  // Get the integer value of the flags
  FlagsValue := GetNativeValue(BipedFlags);
  ModelPath := GetNativeValue(ElementByPath(e, 'Male Biped Model\MOD2 - Model FileName'));
  if FlagsValue = 64 then
  begin
    AddMessage(ModelPath);
  end;
end;

function Finalize: integer;
begin
  AddMessage(slModels.Text);
  slModels.Free;
end;

end.
