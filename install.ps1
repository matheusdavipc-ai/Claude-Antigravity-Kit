param([switch]$DryRun, [switch]$SkipDependencies)
$ErrorActionPreference = 'Stop'
$kitRoot = $PSScriptRoot
$kitPython = $null
foreach ($kitCandidate in @('python', 'python3')) {
    $kitCommand = Get-Command $kitCandidate -ErrorAction SilentlyContinue
    if ($kitCommand) {
        & $kitCommand.Source -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) { $kitPython = $kitCommand.Source; break }
    }
}
if (-not $kitPython) {
    $kitPyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($kitPyLauncher) {
        $kitPython = (& $kitPyLauncher.Source -3 -c 'import sys; print(sys.executable)')
        & $kitPython -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)'
        if ($LASTEXITCODE -ne 0) { $kitPython = $null }
    }
}
if (-not $kitPython) { throw 'Instale Python 3.12+ de python.org (incluindo PATH) e execute novamente. A IA pode instalar essa dependencia antes de continuar.' }
if (-not $DryRun -and -not $SkipDependencies) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Instale Git for Windows de git-scm.com e reabra o terminal.' }
    $kitNative = Join-Path $env:USERPROFILE '.local\bin\claude.exe'
    if (-not (Test-Path -LiteralPath $kitNative)) {
        $kitInstaller = Join-Path ([IO.Path]::GetTempPath()) ('claude-install-' + [guid]::NewGuid() + '.ps1')
        Invoke-WebRequest 'https://claude.ai/install.ps1' -OutFile $kitInstaller
        try { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $kitInstaller; if ($LASTEXITCODE) { throw 'Instalador oficial do Claude falhou.' } }
        finally { Remove-Item -LiteralPath $kitInstaller -Force }
    }
}
$kitArguments = @((Join-Path $kitRoot 'install.py'))
if ($DryRun) { $kitArguments += '--dry-run' }
& $kitPython @kitArguments
if ($LASTEXITCODE) { exit $LASTEXITCODE }
