#Requires -Version 7.0

<#
.SYNOPSIS
    Runs a monitoring session based on a configuration YAML file.

.DESCRIPTION
    This script reads a configuration YAML file that defines a test suite to execute. It schedules and runs the tests at specified intervals, collects the results, and stores them in the specified output path.

.NOTES
    Prerequisites:
      - PowerShell 7.0 or newer (pwsh).
      - The 'powershell-yaml' module (Install-Module powershell-yaml).

    Each result is written to standard output as a single compact JSON document
    (one object per line) via Write-Output, so results can be piped or
    redirected by the caller as needed.

    Informational and debug progress messages are written to the verbose stream,
    so they are shown only when the script is run with the -Verbose switch. This
    keeps standard output clean for result consumers when -Verbose is not used.

.PARAMETER TestSuiteFile
    The configuration YAML file with the test suite to execute.

.PARAMETER PythonPath
    Path to the Python interpreter used to run the monitor modules. When not
    provided, the script first looks for a project virtual environment at
    '<script folder>/../venv/bin/python3', and otherwise falls back to 'python3'
    on the system PATH.

.EXAMPLE
    .\Run-MonitorSession.ps1 -TestSuiteFile "./schedules/config.yaml"

.EXAMPLE
    # Redirect the result stream to a file:
    .\Run-MonitorSession.ps1 -TestSuiteFile "./schedules/config.yaml" > results.json

.EXAMPLE
    # Show informational/debug progress output:
    .\Run-MonitorSession.ps1 -TestSuiteFile "./schedules/config.yaml" -Verbose

#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $true, HelpMessage = "The configuration YAML file with the test suite to execute.")]
    [string]$TestSuiteFile,

    [Parameter(HelpMessage = "Path to the Python interpreter. Defaults to the project venv, then python3 on PATH.")]
    [string]$PythonPath
)

#------------------------------------------------------------------------------
# Verify prerequisites: PowerShell 7+ and the 'powershell-yaml' module.
# If either is missing, report the requirement and stop.
#------------------------------------------------------------------------------
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Error "This script requires PowerShell 7.0 or newer. Detected version: $($PSVersionTable.PSVersion). Install PowerShell 7+ (pwsh) and run the script again."
    exit 1
}

if (-not (Get-Module -ListAvailable -Name 'powershell-yaml')) {
    Write-Error "This script requires the 'powershell-yaml' module, which is not installed. Install it with: Install-Module -Name powershell-yaml -Scope CurrentUser"
    exit 1
}

Import-Module -Name 'powershell-yaml' -ErrorAction Stop

#------------------------------------------------------------------------------
# Resolve the Python interpreter used to run the monitor modules.
#   1. -PythonPath, when supplied.
#   2. The project virtual environment: <script folder>/../venv/bin/python3.
#   3. 'python3' from the system PATH.
#------------------------------------------------------------------------------
if (-not [string]::IsNullOrWhiteSpace($PythonPath)) {
    if (-not (Test-Path -Path $PythonPath)) {
        Write-Error "The specified Python interpreter '$PythonPath' does not exist."
        exit 1
    }
    $PythonExe = $PythonPath
}
else {
    $venvPython = Join-Path -Path $PSScriptRoot -ChildPath '../venv/bin/python3'
    if (Test-Path -Path $venvPython) {
        $PythonExe = (Resolve-Path -Path $venvPython).Path
    }
    else {
        $systemPython = Get-Command -Name 'python3' -ErrorAction SilentlyContinue
        if ($systemPython) {
            $PythonExe = $systemPython.Source
        }
        else {
            Write-Error "No Python interpreter found. Provide one with -PythonPath, create a virtual environment at '$venvPython', or install 'python3' on the system PATH."
            exit 1
        }
    }
}

Write-Verbose "Using Python interpreter: $PythonExe"

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

#------------------------------------------------------------------------------
# Test if the input $TestSuiteFile exists
if (-not (Test-Path -Path $TestSuiteFile)) {
    Write-Error "The configuration file '$TestSuiteFile' does not exist."
    exit 1
}

try {

    # Anchor the module root to the script's location (its parent holds src/ and
    # venv/), so the job's WorkingDirectory is correct regardless of the caller's
    # current directory.
    $rootFolder = Split-Path -Path $PSScriptRoot -Parent

    Write-Verbose "Root Folder: $rootFolder"
    # Parse the configuration
    $testSuiteConfiguration = Get-Content -Path $TestSuiteFile -Raw | ConvertFrom-Yaml

    # enumerate monitors:
    $availableMonitors = $testSuiteConfiguration.monitors

    # get all tests from the schedule:
    $schedule = $testSuiteConfiguration.schedule

    Write-Verbose "Enumerating configured tests"
    $jobs = @()
    $testId = 0;
    # Collect test and create a schedule:
    foreach ($test in $schedule) {
        # Find the monitor that matches the test name
        $monitor = $availableMonitors | Where-Object { $_.name -eq $test.test }

        # Set the path to the executable folder based on the monitor's exec field.
        $testPath = $monitor.exec

        # Set the module name (used to import the Python function)
        $testModule = $monitor.module

        # Convert the repeat interval to seconds.
        $intervalSeconds = Convert-RepeatInterval $test.'repeat-every'

        # Iterate over each target defined in the test's targets array
        foreach ($target in $test.targets) {
            # Convert the target parameters to a compact JSON string
            $targetJson = $target | ConvertTo-Json -Depth 100 -Compress

            # Build the Python command.
            # Here we embed the JSON inside single quotes so it can be passed as a string literal.
            $pythonCmd = "import json; from ${testModule} import run; inJson=$targetJson; outJson = run(inJson, 0); print(json.dumps(outJson));"

            $randomDelay = Get-Random -Minimum 1 -Maximum $intervalSeconds

            $jobs += @{
                PythonCmd      = $pythonCmd
                Configuration  = $targetJson
                Interval       = $intervalSeconds
                Location       = "$rootFolder/$testPath"
                Id             = ++$testId
                Name           = $test.test
                LastRun        = (Get-Date).AddSeconds($randomDelay)
                JobObject      = $null
                OmitProperties = $test["omit-fields"]
                HashProperties = $test["hash-fields"]
            }
        }
    }

    $md5 = New-Object -TypeName System.Security.Cryptography.MD5CryptoServiceProvider
    $utf8 = New-Object -TypeName System.Text.UTF8Encoding

    Write-Verbose "Found $($jobs.Count) tests."
    Write-Verbose "Running test execution loop..."
    while ($true) {
        $now = Get-Date
        Write-Verbose "Checking jobs to run [$now]..."
        foreach ($job in $jobs) {

            # Check if the job is due to run.
            if (($now - $job.LastRun).TotalSeconds -ge $job.Interval -and $null -eq $job.JobObject) {
                Write-Verbose "  Launching $($job.Name).$($job.Id), seconds since last run: $(($now - $job.LastRun).TotalSeconds), expected $($job.Interval)"

                # Start the external Python script.
                $job.JobObject = Start-ThreadJob -StreamingHost $Host -ScriptBlock {
                    #-- Need to have these two function accessbile from this script block ----------------
                    function Remove-Property {
                        [CmdletBinding()]
                        param (
                            [Parameter(Mandatory = $true, Position = 0)]
                            [Alias('InputObject')]
                            [PSObject]$Object,

                            [Parameter(Mandatory = $true, Position = 1)]
                            [string]$PropertyPath
                        )

                        # Split the property path into individual components
                        $properties = $PropertyPath -split '\.'

                        # Kick off recursive removal
                        Remove-PropertyRecursive -Object $Object -Properties $properties
                    }

                    function Remove-PropertyRecursive {
                        [CmdletBinding()]
                        param (
                            [Parameter(Mandatory = $true)]
                            [PSObject]$Object,

                            [Parameter(Mandatory = $true)]
                            [string[]]$Properties
                        )

                        if ($null -eq $Object) {
                            return
                        }

                        # If this object is a collection (but not a string), recurse into each element
                        if ($Object -is [System.Collections.IEnumerable] -and -not ($Object -is [string])) {
                            foreach ($item in $Object) {
                                Remove-PropertyRecursive -Object $item -Properties $Properties
                            }
                        }
                        else {
                            if ($Properties.Count -gt 1) {
                                # Peel off the first segment and go deeper
                                $first = $Properties[0]
                                $rest  = $Properties[1..($Properties.Count - 1)]

                                $next = $Object.PSObject.Properties[$first]?.Value
                                Remove-PropertyRecursive -Object $next -Properties $rest
                            }
                            else {
                                # Last segment: remove this property
                                $Object.PSObject.Properties.Remove($Properties[0]) | Out-Null
                            }
                        }
                    }

                    function Add-HashProperty {
                        [CmdletBinding()]
                        param (
                            [Parameter(Mandatory = $true, Position = 0)]
                            [Alias('InputObject')]
                            [PSObject]$Object,

                            [Parameter(Mandatory = $true, Position = 1)]
                            [string]$SourcePropertyPath,

                            [Parameter(Mandatory = $true, Position = 2)]
                            [string]$TargetPropertyPath
                        )

                        # Split the dot-notation into segments
                        $sourceProps = $SourcePropertyPath -split '\.'
                        $targetProps = $TargetPropertyPath -split '\.'

                        # Kick off the recursive work, starting both source- and target‐contexts at the root
                        ComputeHashPropertyRecursive -SrcParent $Object -TgtParent $Object -SourceProps $sourceProps -TargetProps $targetProps
                    }

                    function ComputeHashPropertyRecursive {
                        [CmdletBinding()]
                        param (
                            [Parameter(Mandatory = $true)]
                            [PSObject]$SrcParent,

                            [Parameter(Mandatory = $true)]
                            [PSObject]$TgtParent,

                            [Parameter(Mandatory = $true)]
                            [string[]]$SourceProps,

                            [Parameter(Mandatory = $true)]
                            [string[]]$TargetProps
                        )

                        if ($null -eq $SrcParent) { return }

                        # If this object is a collection (but not a string), recurse into each item
                        if ($SrcParent -is [System.Collections.IEnumerable] -and -not ($SrcParent -is [string])) {
                            foreach ($item in $SrcParent) {
                                ComputeHashPropertyRecursive -SrcParent $item -TgtParent $item -SourceProps $SourceProps -TargetProps $TargetProps
                            }
                        }
                        else {
                            # If we're not yet at the leaf segment, drill deeper
                            if ($SourceProps.Count -gt 1) {
                                $srcFirst = $SourceProps[0]
                                $srcRest  = $SourceProps[1..($SourceProps.Count - 1)]

                                $tgtFirst = $TargetProps[0]
                                $tgtRest  = $TargetProps[1..($TargetProps.Count - 1)]

                                # Pull out the next source object
                                $nextSrc = $SrcParent.PSObject.Properties[$srcFirst]?.Value

                                # Ensure the target‐container exists (create it if needed)
                                if (-not $TgtParent.PSObject.Properties[$tgtFirst]) {
                                    $TgtParent | Add-Member -MemberType NoteProperty -Name $tgtFirst -Value ([PSCustomObject]@{})
                                }
                                $nextTgt = $TgtParent.PSObject.Properties[$tgtFirst].Value

                                # Recurse
                                ComputeHashPropertyRecursive -SrcParent $nextSrc -TgtParent $nextTgt -SourceProps $srcRest -TargetProps $tgtRest
                            }
                            else {
                                # Leaf: compute hash of the single source property and write to target
                                $srcName = $SourceProps[0]
                                $tgtName = $TargetProps[0]

                                $value = $SrcParent.PSObject.Properties[$srcName].Value
                                # Here using MD5; swap in SHA256 if you like
                                $hashBytes   = [System.Security.Cryptography.MD5]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($value))
                                $hashString  = [BitConverter]::ToString($hashBytes) -replace '-'

                                $TgtParent | Add-Member -MemberType NoteProperty -Name $tgtName -Value $hashString
                            }
                        }
                    }
                    #------------------------------------
                    # Inherit the caller's -Verbose preference so Write-Verbose
                    # below is emitted only when the script was run with -Verbose.
                    $VerbosePreference = $using:VerbosePreference
                    $job = $using:job
                    $cmd = $job.PythonCmd -replace '"', "'"
                    $cmd = $cmd -replace 'true','True'
                    $cmd = $cmd -replace 'false','False'
                    $path = $job.Location
                    $tempFile = [System.IO.Path]::GetTempFileName()
                    $pythonExe = $using:PythonExe
                    Write-Verbose "  Starting job for $cmd "
                    if (-not (Test-Path -Path $path -PathType Container)) {
                        Write-Error "Working directory '$path' for $($job.Name).$($job.Id) does not exist. Check the monitor's 'exec' path and that the modules are installed under the script's parent folder."
                        Remove-Item $tempFile -ErrorAction SilentlyContinue
                        return
                    }
                    Start-Process -FilePath $pythonExe -ArgumentList "-c `"$cmd`"" -WorkingDirectory $path -RedirectStandardOutput $tempFile -Wait
                    Write-Verbose "  $($job.Name).$($job.Id) finished."

                    $inputConfig = $job.Configuration

                    # Get the test ouput from temp file
                    $jsonObject = Get-Content $tempFile | ConvertFrom-Json

                    # Compute Hash properties:
                    foreach ($hashProp in $job.HashProperties) {
                        Add-HashProperty -Object $jsonObject -SourceProperty $hashProp.src -TargetProperty $hashProp.trg
                    }
                    # Omit properties:
                    foreach ($omit in $job.OmitProperties) {
                        Remove-Property -Object $jsonObject -Property $omit
                    }


                    # Example usage:
                    $outputObject = [PSCustomObject]@{
                        Meta =  [PSCustomObject]@{
                            Timestamp = $(Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
                            TestId = "$($job.Name).$($job.Id)"
                        }
                        Config = $inputConfig | ConvertFrom-Json
                        Result = $jsonObject
                    }

                    # Serialize the result to a single-line JSON document.
                    $payload = $outputObject | ConvertTo-Json -Depth 100 -Compress

                    # Emit the result to the job's output stream; the main loop's
                    # Receive-Job surfaces it on the script's standard output.
                    Write-Output $payload

                    Remove-Item $tempFile
                }
                # Update the job's LastRun time.
                $job.LastRun = $now
            }
        }
        # Sleep briefly to avoid a busy loop.
        Start-Sleep -Seconds 1
        # Receive Completed Jobs:
        foreach ($job in $jobs) {
            if ($job.JobObject -and $job.JobObject.State -eq 'Completed') {
                Receive-Job -Job $job.JobObject -Wait
                Remove-Job -Job $job.JobObject
                $job.JobObject = $null
            }
        }
    }
}
finally {
    Write-Verbose "Cleaning up"
    Write-Verbose "Remove schedule jobs ($($jobs.Count))."
    $jobObjects = $jobs | Select-Object -ExpandProperty JobObject | Where-Object { $null -ne $_ }
    if ($null -ne $jobObjects -and @($jobObjects).Count -gt 0) {
        Remove-Job -Job $jobObjects
    }
}