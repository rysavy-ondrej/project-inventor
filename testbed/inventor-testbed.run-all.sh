#!/bin/bash
pwsh Run-MonitorSession.ps1 -TestSuiteFile schedules/network.ping.yaml -OutPath ./out/ &
PID1=$!
pwsh Run-MonitorSession.ps1 -TestSuiteFile schedules/webapp.http.yaml -OutPath ./out/
#PID2=$!

#wait $PID1
#wait $PID2

#echo "Tests terminated!"
