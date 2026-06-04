Write-Host "=== Testing Occupied Slots ==="
Write-Host ""

Write-Host "1. Checking /api/get_slots for occupied slots:"
$response = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/get_slots
$data = $response.Content | ConvertFrom-Json
$occupiedSlots = $data.data.slots | Where-Object { $_.status -eq "OCCUPIED" }
Write-Host "Found $($occupiedSlots.Count) occupied slots:"
$occupiedSlots | ForEach-Object { Write-Host "  - $($_.slot_number): $($_.status)" }
Write-Host ""

Write-Host "2. Summary from backend:"
Write-Host "  Total: $($data.data.summary.total_slots)"
Write-Host "  Free: $($data.data.summary.free_slots)" 
Write-Host "  Occupied: $($data.data.summary.occupied_slots)"
Write-Host "  Reserved: $($data.data.summary.reserved_slots)"
Write-Host ""

Write-Host "3. Checking /api/slots for occupied slots:"
$response2 = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/slots
$data2 = $response2.Content | ConvertFrom-Json
$occupiedSlots2 = $data2 | Where-Object { $_.status -eq "OCCUPIED" }
Write-Host "Found $($occupiedSlots2.Count) occupied slots:"
$occupiedSlots2 | ForEach-Object { Write-Host "  - $($_.slot_label): $($_.status)" }
