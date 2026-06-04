$response = Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/slots
$slots = $response.Content | ConvertFrom-Json
$slots | Where-Object { $_.slot_label -eq "SLOT_10" -or $_.slot_label -eq "SLOT_11" } | ConvertTo-Json -Depth 3
