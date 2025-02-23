<#
.SYNOPSIS
    Runs a monitoring session based on a configuration YAML file.

.DESCRIPTION
    This script reads a configuration YAML file that defines a test suite to execute. It schedules and runs the tests at specified intervals, collects the results, and stores them in the specified output path.

.PARAMETER TestSuiteFile
    The configuration YAML file with the test suite to execute.

.PARAMETER OutPath
    The root path where the collected measurements will be stored.

.EXAMPLE
    .\Run-MonitorSession.ps1 -TestSuiteFile "./schedules/config.yaml" -OutPath "./results"

.NOTES
    Author: Your Name
    Date: Today's Date
#>

param (    
    [Parameter(Mandatory=$true, HelpMessage="The configuration YAML file with the test suite to execute.")]
    [string]$TestSuiteFile,
    [Parameter(Mandatory=$true, HelpMessage="The root path where the collected measurements will be stored.")]
    [string]$OutPath
)

<#
.SYNOPSIS
    Converts repeat-every strings to seconds.

.DESCRIPTION
    This helper function converts strings representing time intervals (e.g., "1d", "1h30m") to total seconds.

.PARAMETER Interval
    The time interval string to convert.

.EXAMPLE
    Convert-RepeatInterval -Interval "1d6h"
#>
function Convert-RepeatInterval {
    param(
        [string]$Interval
    )

    # Pattern with optional groups for days, hours, minutes, and seconds.
    $pattern = '^(?:(?<days>\d+)d)?(?:(?<hours>\d+)h)?(?:(?<minutes>\d+)m)?(?:(?<seconds>\d+)s)?$'
    
    if ($Interval -match $pattern) {
        $days = if ($Matches['days']) { [int]$Matches['days'] } else { 0 }
        $hours = if ($Matches['hours']) { [int]$Matches['hours'] } else { 0 }
        $minutes = if ($Matches['minutes']) { [int]$Matches['minutes'] } else { 0 }
        $seconds = if ($Matches['seconds']) { [int]$Matches['seconds'] } else { 0 }
        
        # Calculate total seconds
        return ($days * 86400 + $hours * 3600 + $minutes * 60 + $seconds)
    }
    else {
        Write-Error "Invalid interval format: $Interval"
        return 0
    }
}

# Test if the input $TestSuiteFile exists
if (-not (Test-Path -Path $TestSuiteFile)) {
    Write-Error "The configuration file '$TestSuiteFile' does not exist."
    exit 1
}

$rootFolder = Split-Path -Path (Get-Location) -Parent

Write-Host "Root Folder: $rootFolder"
# Parse the configuration 
$testSuiteConfiguration = Get-Content -Path $TestSuiteFile -Raw | ConvertFrom-Yaml

# enumerate monitors:
$availableMonitors = $testSuiteConfiguration.monitors

# get all tests from the schedule:
$schedule = $testSuiteConfiguration.schedule


$scheduledTests = @()
$testId = 0;
# Collect test and create a schedule:
foreach ($test in $schedule)
{
    # Find the monitor that matches the test name
    $monitor = $availableMonitors | Where-Object { $_.name -eq $test.test }
    
    # Set the path to the executable folder based on the monitor's exec field.
    $testPath = $monitor.exec
    
    # Set the module name (used to import the Python function)
    $testModule = $monitor.module
    
    # Convert the repeat interval to seconds.
    $intervalSeconds = Convert-RepeatInterval $test.'repeat-every'

    # Iterate over each target defined in the test's targets array
    foreach ($target in $test.targets)
    {
        # Convert the target parameters to a compact JSON string
        $targetJson = $target | ConvertTo-Json -Compress
        
        # Build the Python command.
        # Here we embed the JSON inside single quotes so it can be passed as a string literal.
        $pythonCmd = "import json; from ${testModule} import run; inJson=$targetJson; outJson = run(inJson, 0); print(json.dumps(outJson));"
        
        $scheduledTests += @{
            ResultsFile = $OutPath + "/" + $test["write-to"] 
            PyCommand = $pythonCmd
            Configuration = $targetJson
            Interval = $intervalSeconds * 1000
            Location = "$rootFolder/$testPath"
            TestId = ++$testId
            TestName = $test.test
        }
    }
}

foreach($test in $scheduledTests)
{
    Write-Host "Scheduling test $($test.TestName).$($test.TestId):"
    Write-Host "  Interval: $($test.Interval/1000)s"
    Write-Host "  Configuration: $($test.Configuration)"
    Write-Host "  Location: $($test.Location)"
    Write-Host "  Result file: $($test.ResultsFile)"
    Write-Host ""

    $testCount +=1
    $timer = New-Object System.Timers.Timer
    $timer.Interval = $test.Interval  # Interval in milliseconds
    $timer.AutoReset = $true 
    $timer.Enabled = $true

    $objectEventArgs = @{
        InputObject = $timer
        EventName = 'Elapsed'
        SourceIdentifier = "Inventor.TimerEvent.$($test.TestName).$($test.TestId)"
        MessageData = $test
        Action = {    
            Write-Debug "Timer Event - executing test $($Event.TestName).$($Event.TestId)..."
            $pycommand = $Event.MessageData.PyCommand -replace '"', "'"
            $pypath = $Event.MessageData.Location
            $outfile = $Event.MessageData.ResultsFile
            $tempFile = [System.IO.Path]::GetTempFileName()
            Start-Process -FilePath python3 -ArgumentList "-c `"$pycommand`"" -WorkingDirectory $pypath -RedirectStandardOutput $tempFile -NoNewWindow -Wait
            Get-Content $tempFile | Add-Content -Path $outfile
            Remove-Item $tempFile

            Write-Debug "Test $($Event.TestName).$($Event.TestId) done." 
        }
    }
    # Execute the scheduled tests:
    $s = Register-ObjectEvent @objectEventArgs
    # Wait for a random time between 1 to 5 seconds to desynchronize the tests
    $randomDelay = Get-Random -Minimum 1 -Maximum 6
    Start-Sleep -Seconds $randomDelay
}
