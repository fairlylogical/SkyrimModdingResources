unit UserScript;

var
  RingCount: Integer;

function Initialize: Integer;
begin
  RingCount := 0;
end;

function Process(e: IInterface): Integer;
var
  BipedFlags: Int64;
begin
  if Signature(e) <> 'ARMA' then
    Exit;

  // Try to get Biped Slot Flags
  if ElementExists(e, 'BOD2 - Biped Body Template\First Person Flags') then
    BipedFlags := GetElementNativeValues(e, 'BOD2 - Biped Body Template\First Person Flags')
  else if ElementExists(e, 'BODT - Biped Body Template\First Person Flags') then
    BipedFlags := GetElementNativeValues(e, 'BODT - Biped Body Template\First Person Flags')
  else
    Exit;

  // Check if the Armor Addon uses Slot 36 (Finger)
  if BipedFlags = 64 then begin
    Inc(RingCount);
    AddMessage('Ring found: ' + Name(e));
  end;
end;

function Finalize: Integer;
begin
  AddMessage('Total Rings Found: ' + IntToStr(RingCount));
end;

end.
