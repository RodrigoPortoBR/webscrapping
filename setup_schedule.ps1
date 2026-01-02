# Script PowerShell para configurar tarefas agendadas do Monitor de Preços
# Executa o monitor as 06h, 12h, 18h e 00h horario de Brasilia (se o PC estiver ligado)

Write-Host "Configurando Monitor de Precos (Local)..."

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERRO: Execute como Administrador" -ForegroundColor Red
    exit 1
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "price_monitor.py"
$pythonPath = (Get-Command python).Source

# Nome base da tarefa
$taskBaseName = "PriceMonitor"

# Horarios de execucao
$schedules = @("06:00", "12:00", "18:00", "00:00")

# Configurar settings gerais
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$pythonScript`" --once" -WorkingDirectory $scriptDir
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U

foreach ($time in $schedules) {
    $suffix = $time.Replace(":", "")
    $taskName = "${taskBaseName}_${suffix}"
    
    # Remover tarefa antiga se existir
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    
    # Criar nova trigger
    $trigger = New-ScheduledTaskTrigger -Daily -At $time
    
    # Registrar tarefa
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
    Write-Host "Tarefa $taskName configurada para $time" -ForegroundColor Cyan
}

Write-Host "Concluido! Tarefas agendadas localmente." -ForegroundColor Green
Write-Host "NOTA: O computador precisa estar ligado para estas tarefas executarem." -ForegroundColor Yellow
Read-Host "Pressione Enter para sair"
