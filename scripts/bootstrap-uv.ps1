param(
    [switch]$NoInstall
)

$ErrorActionPreference = "Stop"

$existingUv = Get-Command uv -ErrorAction SilentlyContinue
if ($existingUv) {
    [PSCustomObject]@{
        ok = $true
        uv_available = $true
        uv_path = $existingUv.Source
        installed = $false
        restart_shell_recommended = $false
    } | ConvertTo-Json -Depth 4
    exit 0
}

if ($NoInstall) {
    [PSCustomObject]@{
        ok = $false
        uv_available = $false
        error_code = "UV_UNAVAILABLE"
        error_message = "uv is required for the mainline docrt runtime."
        bootstrap_command = "winget install --id astral-sh.uv -e"
    } | ConvertTo-Json -Depth 4
    exit 2
}

$winget = Get-Command winget -ErrorAction SilentlyContinue
if (-not $winget) {
    [PSCustomObject]@{
        ok = $false
        uv_available = $false
        error_code = "UV_BOOTSTRAP_FAILED"
        error_message = "uv is missing and winget is unavailable."
        bootstrap_command = "winget install --id astral-sh.uv -e"
    } | ConvertTo-Json -Depth 4
    exit 3
}

& $winget.Source install --id astral-sh.uv -e --accept-package-agreements
$code = $LASTEXITCODE
if ($code -ne 0) {
    [PSCustomObject]@{
        ok = $false
        uv_available = $false
        error_code = "UV_BOOTSTRAP_FAILED"
        error_message = "winget failed to install uv."
        returncode = $code
    } | ConvertTo-Json -Depth 4
    exit $code
}

$refreshedUv = Get-Command uv -ErrorAction SilentlyContinue
[PSCustomObject]@{
    ok = $true
    uv_available = [bool]$refreshedUv
    uv_path = if ($refreshedUv) { $refreshedUv.Source } else { $null }
    installed = $true
    restart_shell_recommended = -not [bool]$refreshedUv
} | ConvertTo-Json -Depth 4
