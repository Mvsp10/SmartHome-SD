$projeto = $PSScriptRoot
$python = Join-Path $projeto '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { $python = Join-Path $projeto '..\.venv\Scripts\python.exe' }
if (-not (Test-Path $python)) { Write-Host 'Python virtual nao encontrado.' -ForegroundColor Red; exit 1 }
$comandos = @(
    'controladores\replica.py --id 1',
    'controladores\replica.py --id 2',
    'controladores\replica.py --id 3',
    'middleware\api.py',
    'sensores\temperatura.py'
)
foreach ($comando in $comandos) {
    $linha = "Set-Location '$projeto'; & '$python' $comando"
    Start-Process powershell.exe -ArgumentList @('-NoExit', '-Command', $linha)
    Start-Sleep -Milliseconds 900
}
Write-Host 'Etapa 3 iniciada. Aguarde alguns segundos e abra http://127.0.0.1:8000/estado'
