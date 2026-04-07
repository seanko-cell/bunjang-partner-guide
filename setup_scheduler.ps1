$scriptPath = Join-Path $PSScriptRoot "check_api.py"
$action  = New-ScheduledTaskAction -Execute "python" -Argument "`"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "11:00AM"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask `
    -TaskName "Bunjang API Weekly Check" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Force

Write-Host ""
Write-Host "[OK] 매주 월요일 11:00 자동 실행 등록 완료" -ForegroundColor Green
Write-Host ""
Get-ScheduledTask -TaskName "Bunjang API Weekly Check" | Select-Object TaskName, State
