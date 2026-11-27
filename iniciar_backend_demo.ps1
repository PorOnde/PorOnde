$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Ambiente virtual .venv nao encontrado.' }
# PORONDE_MODO=real selects Supabase rather than the legacy SQLite demonstration.
# PORONDE_AMBIENTE=demonstracao isolates simulated community data in Supabase.
$env:PORONDE_MODO = 'real'
$env:PORONDE_AMBIENTE = 'demonstracao'
& $python -m uvicorn api:app --host 127.0.0.1 --port 8000 --no-access-log
