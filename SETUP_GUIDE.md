# Configuração de Agendamento - Monitor de Preços

## ⚡ Método Rápido (Linha de Comando)

Abra o **PowerShell como Administrador** e execute os seguintes comandos:

```powershell
# Navegar até a pasta do projeto
cd c:\Users\Sellbie\.gemini\antigravity\playground\ruby-aldrin

# Obter o caminho do Python
$pythonPath = (Get-Command python).Source
$scriptPath = "c:\Users\Sellbie\.gemini\antigravity\playground\ruby-aldrin\price_monitor.py"

# Criar tarefa do meio-dia (12:00 = horário de Brasília)
$action1 = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`" --once" -WorkingDirectory "c:\Users\Sellbie\.gemini\antigravity\playground\ruby-aldrin"
$trigger1 = New-ScheduledTaskTrigger -Daily -At "12:00"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "PriceMonitor_Morning" -Action $action1 -Trigger $trigger1 -Settings $settings -Force

# Criar tarefa vespertina (18:00 = horário de Brasília)
$action2 = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptPath`" --once" -WorkingDirectory "c:\Users\Sellbie\.gemini\antigravity\playground\ruby-aldrin"
$trigger2 = New-ScheduledTaskTrigger -Daily -At "18:00"
Register-ScheduledTask -TaskName "PriceMonitor_Evening" -Action $action2 -Trigger $trigger2 -Settings $settings -Force

Write-Host "✓ Tarefas criadas com sucesso!" -ForegroundColor Green
```

---

## 📋 Método Manual (Interface Gráfica)

### Passo 1: Abrir o Agendador de Tarefas

1. Pressione `Win + R`
2. Digite `taskschd.msc`
3. Pressione Enter

### Passo 2: Criar Tarefa do Meio-Dia (12:00 Brasília)

1. No painel direito, clique em **"Create Task"** (Criar Tarefa)
2. Na aba **General**:
   - Nome: `PriceMonitor_Noon`
   - Descrição: `Monitor de preços - execução ao meio-dia (12:00 horário de Brasília)`
   - Marque: ☑ "Run whether user is logged on or not"
   - Marque: ☑ "Run with highest privileges"

3. Na aba **Triggers**:
   - Clique em **New...**
   - Begin the task: `On a schedule`
   - Settings: `Daily`
   - Start: Escolha a data de hoje
   - Start time: `12:00:00` (12:00 - meio-dia)
   - Marque: ☑ "Enabled"
   - Clique em **OK**

4. Na aba **Actions**:
   - Clique em **New...**
   - Action: `Start a program`
   - Program/script: `python`
   - Add arguments: `"c:\Users\Sellbie\.gemini\antigravity\playground\ruby-aldrin\price_monitor.py" --once`
   - Start in: `c:\Users\Sellbie\.gemini\antigravity\playground\ruby-aldrin`
   - Clique em **OK**

5. Na aba **Settings**:
   - Marque: ☑ "Allow task to be run on demand"
   - Marque: ☑ "Run task as soon as possible after a scheduled start is missed"
   - Marque: ☑ "If the task fails, restart every: 1 minute" (Attempt to restart up to: 3 times)
   - Desmarque: ☐ "Stop the task if it runs longer than"

6. Clique em **OK** para salvar

### Passo 3: Criar Tarefa Vespertina (18:00 Brasília)

Repita o Passo 2 com as seguintes alterações:
- Nome: `PriceMonitor_Evening`
- Descrição: `Monitor de preços - execução vespertina (18:00 horário de Brasília)`
- Start time: `18:00:00` (18:00 - 6 da tarde)

---

## ✅ Verificar se as Tarefas Foram Criadas

```powershell
Get-ScheduledTask -TaskName "PriceMonitor_*" | Format-Table TaskName, State, LastRunTime, NextRunTime
```

---

## 🧪 Testar as Tarefas

### Executar manualmente:
```powershell
Start-ScheduledTask -TaskName "PriceMonitor_Morning"
```

### Verificar o resultado:
```powershell
Get-Content c:\Users\Sellbie\.gemini\antigravity\playground\ruby-aldrin\price_monitor.log -Tail 30
```

---

## 🗑️ Remover as Tarefas (se necessário)

```powershell
Unregister-ScheduledTask -TaskName "PriceMonitor_Morning" -Confirm:$false
Unregister-ScheduledTask -TaskName "PriceMonitor_Evening" -Confirm:$false
```

---

## 📊 Horários de Execução

| Horário de Brasília | Descrição | Tarefa |
|---------------------|-----------|--------|
| 12:00 (meio-dia)    | Execução do meio-dia | Noon |
| 18:00 (6 da tarde)  | Execução vespertina  | Evening |

> **Nota**: Horários configurados para o fuso horário de Brasília (UTC-3).

---

## 🔍 Solução de Problemas

### Problema: "Python não é reconhecido"

Verifique se o Python está no PATH:
```powershell
python --version
```

Se não funcionar, use o caminho completo do Python:
```powershell
C:\Users\Sellbie\AppData\Local\Programs\Python\Python311\python.exe
```

### Problema: Tarefa não executa

1. Verifique os logs do Event Viewer:
   - Event Viewer → Windows Logs → Application
   - Procure por erros relacionados a "Task Scheduler"

2. Verifique se o script funciona manualmente:
   ```powershell
   cd c:\Users\Sellbie\.gemini\antigravity\playground\ruby-aldrin
   python price_monitor.py --once
   ```

3. Verifique as permissões da tarefa:
   - Abra o Task Scheduler
   - Clique com o botão direito na tarefa
   - Properties → General → "Run with highest privileges"

### Problema: Email não enviado

Verifique o arquivo de log:
```powershell
Get-Content price_monitor.log -Tail 50 | Select-String "email|smtp|notif"
```

---

## 📝 Logs

Os logs são salvos em:
```
c:\Users\Sellbie\.gemini\antigravity\playground\ruby-aldrin\price_monitor.log
```

Para monitorar em tempo real:
```powershell
Get-Content price_monitor.log -Wait -Tail 10
```
