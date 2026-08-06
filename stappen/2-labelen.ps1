<#
Stap 2 — Label Studio starten om te annoteren.

Installeert Label Studio zo nodig en start hem met de juiste instellingen.
Eerste keer: volg de spiekbrief die verschijnt (project + interface + storage).
Elke ronde: Import -> data\labelstudio\tasks.json -> annoteren -> Export -> JSON.

Gebruik:  .\stappen\2-labelen.ps1     (stoppen: Ctrl+C)
#>

Set-Location "$PSScriptRoot\.."
& .\start.ps1 -Labelen
