#Requires -Version 7.0

<#
.SYNOPSIS
    Reads result documents from the pipeline and appends them to a per-day file.

.DESCRIPTION
    A pipeline sink for the monitoring results emitted by Run-MonitorSession.ps1.
    Each result is a single-line JSON document; this script appends every line it
    receives to a file named '<BaseName>.<yyyy-MM-dd>.json' under -OutPath.

    The date stamp is evaluated for each record as it is written, so a new file is
    started automatically at midnight even for a long-running session.

.PARAMETER BaseName
    The base file name (without date or extension). The day stamp and the '.json'
    extension are appended automatically, e.g. 'network.ping' -> 'network.ping.2026-06-11.json'.

.PARAMETER OutPath
    The directory in which the per-day files are created. Defaults to the current
    directory. The directory is created if it does not exist.

.PARAMETER InputObject
    The result line(s) received from the pipeline. Typically the standard output
    of Run-MonitorSession.ps1.

.EXAMPLE
    # Append results to ./results/network.ping.<date>.json:
    .\Run-MonitorSession.ps1 -TestSuiteFile "./schedules/network.ping.yaml" |
        .\Out-FileByDay.ps1 -BaseName "network.ping" -OutPath "./results"
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $true, HelpMessage = "Base file name (without date or extension).")]
    [string]$BaseName,

    [Parameter(HelpMessage = "Directory where the per-day files are created.")]
    [string]$OutPath = ".",

    [Parameter(ValueFromPipeline = $true, HelpMessage = "Result line received from the pipeline.")]
    [string]$InputObject
)

begin {
    # Make sure the target directory exists before the first write.
    if (-not (Test-Path -LiteralPath $OutPath)) {
        Write-Verbose "Output folder '$OutPath' does not exist. Creating it..."
        New-Item -ItemType Directory -Path $OutPath -Force | Out-Null
    }
}

process {
    # Ignore blank lines that may appear between results.
    if ([string]::IsNullOrWhiteSpace($InputObject)) {
        return
    }

    # Re-evaluate the date for every record so the file rolls over at midnight.
    $date = (Get-Date).ToString("yyyy-MM-dd")
    $file = Join-Path -Path $OutPath -ChildPath "$BaseName.$date.json"

    Add-Content -LiteralPath $file -Value $InputObject
}
