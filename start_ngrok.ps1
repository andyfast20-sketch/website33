# Start ngrok for port 5004
Write-Host "Starting ngrok tunnel on port 5004..."

# Find ngrok executable
$ngrokExe = (Get-Command ngrok -ErrorAction SilentlyContinue).Source

if (-not $ngrokExe) {
    Write-Error "ngrok not found in PATH"
    exit 1
}

Write-Host "Found ngrok at: $ngrokExe"

# Start ngrok in background
Start-Process -FilePath cmd.exe -ArgumentList "/c", "start", "ngrok", "http", "5004" -WindowStyle Hidden

Write-Host "Waiting for ngrok to start..."
Start-Sleep -Seconds 5

# Get tunnel URL
try {
    $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels"
    $publicUrl = $response.tunnels[0].public_url
    Write-Host "`n✅ ngrok started successfully!"
    Write-Host "Public URL: $publicUrl"
    Write-Host "`nUpdate your Vonage webhooks to: $publicUrl/webhooks/answer"
} catch {
    Write-Error "Failed to get ngrok status: $_"
}
