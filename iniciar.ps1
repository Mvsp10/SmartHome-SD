
# Pasta onde este script está salvo
$projeto = $PSScriptRoot

# Python do ambiente virtual
$python = Join-Path $projeto ".venv\Scripts\python.exe"

# Caso o ambiente virtual esteja na pasta externa
if (-not (Test-Path $python)) {
    $python = Join-Path $projeto "..\.venv\Scripts\python.exe"
}

if (-not (Test-Path $python)) {
    Write-Host "Ambiente virtual nao encontrado!" -ForegroundColor Red
    exit
}

# Componentes do sistema
$componentes = @(
    "monitor_mqtt.py",
    "atuadores\ventilador.py",
    "controladores\controlador.py",
    "sensores\temperatura.py"
)

foreach ($arquivo in $componentes) {
    $caminho = Join-Path $projeto $arquivo

    if (Test-Path $caminho) {
        Start-Process powershell.exe -ArgumentList @(
            "-NoExit",
            "-Command",
            "Set-Location '$projeto'; & '$python' '$caminho'"
        )

        Start-Sleep -Seconds 1
    }
    else {
        Write-Host "Arquivo nao encontrado: $arquivo" -ForegroundColor Yellow
    }
}

Write-Host "Componentes iniciados!" -ForegroundColor Green
