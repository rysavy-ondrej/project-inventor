#!/bin/bash
pwsh Run-MonitorSession.ps1 -TestSuiteFile schedules/network.ping.yaml -OutPath ./out/ &
pwsh Run-MonitorSession.ps1 -TestSuiteFile schedules/network.smtp.yaml -OutPath ./out/ &
pwsh Run-MonitorSession.ps1 -TestSuiteFile schedules/security.ssh.yaml -OutPath ./out/ &
pwsh Run-MonitorSession.ps1 -TestSuiteFile schedules/network.imap.yaml -OutPath ./out/ &
pwsh Run-MonitorSession.ps1 -TestSuiteFile schedules/network.dns.yaml -OutPath ./out/ &
PID1=$!
pwsh Run-MonitorSession.ps1 -TestSuiteFile schedules/webapp.http.yaml -OutPath ./out/
#PID2=$!

#wait $PID1
#wait $PID2

#echo "Tests terminated!"
