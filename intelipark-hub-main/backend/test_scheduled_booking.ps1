# Test scheduled booking creation
Write-Host "=== Testing Scheduled Booking ===" -ForegroundColor Cyan
Write-Host ""

# Calculate future time (2 hours from now)
$now = Get-Date
$startTime = $now.AddHours(2).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss") + "Z"
$endTime = $now.AddHours(4).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss") + "Z"

Write-Host "Start Time: $startTime" -ForegroundColor Yellow
Write-Host "End Time: $endTime" -ForegroundColor Yellow
Write-Host ""

# Create booking payload
$booking = @{
    slot_number = "SLOT_15"
    booking_type = "scheduled"
    start_time = $startTime
    end_time = $endTime
    user_name = "Test User"
    user_email = "test@example.com"
} | ConvertTo-Json

Write-Host "Creating scheduled booking..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/booking/create" -Method POST -ContentType "application/json" -Body $booking
    Write-Host "✅ Booking created successfully!" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "❌ Error creating booking:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "Checking SLOT_15 status..." -ForegroundColor Yellow
try {
    $slotResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/get_slots"
    $slot15 = $slotResponse.data.slots | Where-Object { $_.slot_number -eq "SLOT_15" }
    Write-Host "SLOT_15 Status: $($slot15.status)" -ForegroundColor $(if ($slot15.status -eq "RESERVED") { "Green" } else { "Red" })
    $slot15 | ConvertTo-Json -Depth 2
} catch {
    Write-Host "❌ Error checking slot:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
