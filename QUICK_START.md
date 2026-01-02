# Quick Start: Configurar Agendamento

## Método Mais Fácil (Recomendado)

1. **Abra o PowerShell como Administrador**
   - Clique com botão direito no ícone do PowerShell
   - Selecione "Executar como Administrador"

2. **Navegue até a pasta do projeto**
   ```powershell
   cd c:\Users\Sellbie\.gemini\antigravity\playground\ruby-aldrin
   ```

3. **Execute o script de configuração**
   ```powershell
   .\setup_schedule.ps1
   ```

4. **Pronto!** As tarefas foram criadas e executarão automaticamente:
   - Todos os dias às **12:00** (meio-dia - horário de Brasília)
   - Todos os dias às **18:00** (6 da tarde - horário de Brasília)

---

## Testar Agora

Para executar uma verificação manual imediatamente:

```powershell
Start-ScheduledTask -TaskName 'PriceMonitor_Morning'
```

Ou simplesmente:

```powershell
python price_monitor.py --once
```

---

## Ver Logs

```powershell
Get-Content price_monitor.log -Tail 20
```

---

## Remover Agendamento

Se quiser desabilitar o agendamento:

```powershell
Unregister-ScheduledTask -TaskName 'PriceMonitor_Morning' -Confirm:$false
Unregister-ScheduledTask -TaskName 'PriceMonitor_Evening' -Confirm:$false
```
