param([switch]$DryRun, [switch]$SkipKey, [switch]$SkipDependencies)
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
    if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Instale Node.js LTS 22+ de nodejs.org e reabra o terminal.' }
    & node -e 'const v=process.versions.node.split(".").map(Number);process.exit(v[0]>22||(v[0]===22&&v[1]>=19)?0:1)'
    if ($LASTEXITCODE) { throw 'Node.js 22.19+ necessario.' }
    $kitNative = Join-Path $env:USERPROFILE '.local\bin\claude.exe'
    if (-not (Test-Path -LiteralPath $kitNative)) {
        $kitInstaller = Join-Path ([IO.Path]::GetTempPath()) ('claude-install-' + [guid]::NewGuid() + '.ps1')
        Invoke-WebRequest 'https://claude.ai/install.ps1' -OutFile $kitInstaller
        try { & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $kitInstaller; if ($LASTEXITCODE) { throw 'Instalador oficial do Claude falhou.' } }
        finally { Remove-Item -LiteralPath $kitInstaller -Force }
    }
    if (-not (Get-Command omniroute.cmd -ErrorAction SilentlyContinue)) {
        & npm.cmd install -g omniroute@3.8.51
        if ($LASTEXITCODE) { throw 'Instalacao do OmniRoute falhou; configuracoes existentes preservadas.' }
    }
}
$kitArguments = @((Join-Path $kitRoot 'install.py'))
if ($DryRun) { $kitArguments += '--dry-run' }
if ($SkipKey) { $kitArguments += '--skip-key' }
& $kitPython @kitArguments
if ($LASTEXITCODE) { exit $LASTEXITCODE }
if (-not $DryRun) {
    & $kitPython (Join-Path $kitRoot 'scripts\configure_omniroute.py')
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
}
