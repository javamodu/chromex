param(
    [switch]$Canli,
    [switch]$Chrome
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$policyGate = Join-Path $repo 'policy-gate'
$wba = Join-Path $repo 'windows-browser-automation'
$claude = Join-Path $repo 'claude-code-automation'

function Invoke-GateStep {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string[]]$Command
    )
    Write-Host ''
    Write-Host ('=== ' + $Name + ' ===') -ForegroundColor Cyan
    Push-Location $WorkingDirectory
    try {
        $arguments = $Command[1..($Command.Count - 1)]
        & $Command[0] @arguments
        if ($LASTEXITCODE -ne 0) {
            throw ($Name + ' exit=' + $LASTEXITCODE)
        }
    }
    finally {
        Pop-Location
    }
    Write-Host ('OK: ' + $Name) -ForegroundColor Green
}

try {
    Invoke-GateStep 'policy-gate testleri' $policyGate @(
        'python', '-m', 'unittest', 'discover', '-s', 'tests', '-v'
    )
    Invoke-GateStep 'wba testleri' $wba @(
        'python', '-m', 'unittest', 'discover', '-s', 'tests', '-v'
    )
    Invoke-GateStep 'claude testleri' $claude @(
        'python', '-m', 'unittest', 'discover', '-s', 'tests', '-v'
    )
    Invoke-GateStep 'audit bridge' $claude @(
        'python', 'audit_bridge.py', 'verify'
    )
    Invoke-GateStep 'CLI yardimi' $wba @(
        'python', '-m', 'orchestrator.cli', '--help'
    )
    Invoke-GateStep 'MCP smoke' $wba @(
        'python', 'scripts\mcp_smoke.py'
    )
    Invoke-GateStep 'uretim kontrolu' $wba @(
        'python', 'scripts\production_check.py'
    )
    Invoke-GateStep 'audit dogrulama' $wba @(
        'python', '-m', 'orchestrator.cli', 'audit-dogrula'
    )
    $jobPath = Join-Path $env:TEMP 'chromex-gecis-kapisi-job.json'
    @{
        komut = 'son-kayitlar'
        args = @('--limit', '3')
        seviye = 'READ'
        zaman_asimi = 60
    } | ConvertTo-Json | Set-Content -Path $jobPath -Encoding UTF8
    Invoke-GateStep 'zamanlayici' $wba @(
        'python', '-m', 'orchestrator.cli', 'zamanla', '--dosya', $jobPath
    )
    Remove-Item -Path $jobPath -ErrorAction SilentlyContinue
    Invoke-GateStep 'model default' $claude @(
        'python', 'model_manager.py', 'default'
    )
    Invoke-GateStep 'model free' $claude @(
        'python', 'model_manager.py', 'free'
    )
    if ($Canli) {
        Invoke-GateStep 'canli model' $claude @(
            'python', 'model_manager.py', 'sor',
            'Tek cumle: Faz 2 gecis kapisi hazir mi?'
        )
    }
    if ($Chrome) {
        Write-Host ''
        Write-Host '=== Chrome CDP ===' -ForegroundColor Cyan
        $startScript = Join-Path $wba 'scripts\start-chrome-automation.ps1'
        $stopScript = Join-Path $wba 'scripts\stop-chrome-automation.ps1'
        & $startScript
        if ($LASTEXITCODE -ne 0) { throw 'Chrome baslatma hatasi' }
        Start-Sleep -Seconds 2
        & $stopScript
        if ($LASTEXITCODE -ne 0) { throw 'Chrome kapatma hatasi' }
        Write-Host 'OK: Chrome CDP' -ForegroundColor Green
    }
    Write-Host ''
    Write-Host 'FAZ2_GECIS_KAPISI_OK' -ForegroundColor Green
}
catch {
    Write-Host ''
    Write-Host ('FAZ2_GECIS_KAPISI_FAIL: ' + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
