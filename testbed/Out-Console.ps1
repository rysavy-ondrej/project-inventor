#Requires -Version 7.0

<#
.SYNOPSIS
    Reads result documents from the pipeline and prints them to the host console.

.DESCRIPTION
    A pipeline sink for the monitoring results emitted by Run-MonitorSession.ps1.
    Each result is a single-line JSON document; this script writes every line it
    receives to the host console as it arrives.

.PARAMETER InputObject
    The result line(s) received from the pipeline. Typically the standard output
    of Run-MonitorSession.ps1.

.EXAMPLE
    # Stream results to the console:
    .\Run-MonitorSession.ps1 -TestSuiteFile "./schedules/network.ping.yaml" | .\Out-Console.ps1
#>

[CmdletBinding()]
param (
    [Parameter(ValueFromPipeline = $true, HelpMessage = "Result line received from the pipeline.")]
    [string]$InputObject
)

process {
    # Ignore blank lines that may appear between results.
    if (-not [string]::IsNullOrWhiteSpace($InputObject)) {
        Write-Host $InputObject
    }
}
