$projeto = $PSScriptRoot
$python = Join-Path $projeto '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { $python = Join-Path $projeto '..\.venv\Scripts\python.exe' }
if (-not (Test-Path $python)) { Write-Host 'Ambiente virtual nao encontrado'; exit 1 }
$comandos = @('controladores\replica.py --id 1', 'controladores\replica.py --id 2', 'controladores\replica.py --id 3', 'middleware\api.py', 'atuadores\ventilador_confiavel.py', 'sensores\temperatura.py')
foreach ($comando in $comandos) {
    $linha = "Set-Location '$projeto'; & '$python' $comando"
    Start-Process powershell.exe -ArgumentList @('-NoExit', '-Command', $linha)
    Start-Sleep -Milliseconds 900
}
Write-Host 'Etapa 4 iniciada. API: http://127.0.0.1:8000/docs'
