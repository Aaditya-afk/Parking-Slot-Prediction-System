$response = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/get_slots
$data = $response.Content | ConvertFrom-Json
$data.data.slots | Where-Object { $_.slot_number -eq "SLOT_10" -or $_.slot_number -eq "SLOT_11" } | ConvertTo-Json -Depth 3
