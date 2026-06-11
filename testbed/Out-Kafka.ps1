#Requires -Version 7.0

<#
.SYNOPSIS
    Reads result documents from the pipeline and publishes them to a Kafka topic
    through a single, long-lived kcat producer.

.DESCRIPTION
    A pipeline sink for the monitoring results emitted by Run-MonitorSession.ps1.
    Each result is a single-line JSON document.

    For efficiency the script starts ONE 'kcat' (kafkacat) producer process in its
    'begin' block and keeps it running for the whole session: every result is
    written to that producer's standard input, one message per line. This avoids
    the cost of launching a new process per measurement and lets librdkafka (inside
    kcat) batch and deliver messages asynchronously on its own background thread.

    Because writing a line to the producer's stdin returns almost immediately, the
    Kafka delivery is effectively decoupled from measurement production: a slow or
    unreachable broker no longer blocks the (single-threaded) PowerShell pipeline
    that schedules and runs the measurements.

    The Kafka message key is set to the result's Meta.TestId (when present) so that
    consumers can partition or route messages per test. Per-message keys are passed
    to the shared producer using kcat's key delimiter mode (-K).

.NOTES
    Requires the 'kcat' (kafkacat) producer CLI on PATH:
      Debian/Ubuntu : sudo apt-get install kafkacat
      Fedora/RHEL   : sudo dnf install kcat
      macOS (brew)  : brew install kcat

.PARAMETER KafkaBroker
    The Kafka bootstrap broker(s), e.g. 'localhost:9092' or a comma-separated list.

.PARAMETER KafkaTopic
    The Kafka topic that result messages are published to.

.PARAMETER TimeoutSeconds
    Maximum time, in seconds, that librdkafka keeps trying to deliver a queued
    message before it expires it and reports a delivery failure. Applied as
    'message.timeout.ms'. This bounds how long an unreachable broker holds messages
    in the producer queue; once messages expire the queue drains, so writes never
    block indefinitely. Defaults to 10 seconds.

.PARAMETER MaxQueueMessages
    Upper bound on the number of messages librdkafka buffers in the producer queue
    awaiting delivery. Applied as 'queue.buffering.max.messages'. This caps the
    producer's memory use when the broker is slow or down: once the queue is full
    the producer applies backpressure (further writes wait) instead of growing
    without limit, while expiring messages (see -TimeoutSeconds) keep draining it.
    Defaults to 100000 (the librdkafka default).

.PARAMETER InputObject
    The result line(s) received from the pipeline. Typically the standard output
    of Run-MonitorSession.ps1.

.EXAMPLE
    # Publish results to a Kafka topic via a single shared producer:
    .\Run-MonitorSession.ps1 -TestSuiteFile "./schedules/network.ping.yaml" |
        .\Out-Kafka.ps1 -KafkaBroker "localhost:9092" -KafkaTopic "inventor.results"

.EXAMPLE
    # Expire undelivered messages after 5 seconds when the broker is down:
    .\Run-MonitorSession.ps1 -TestSuiteFile "./schedules/network.ping.yaml" |
        .\Out-Kafka.ps1 -KafkaBroker "localhost:9092" -KafkaTopic "inventor.results" -TimeoutSeconds 5

.EXAMPLE
    # Cap the producer queue at 5000 buffered messages to bound memory use:
    .\Run-MonitorSession.ps1 -TestSuiteFile "./schedules/network.ping.yaml" |
        .\Out-Kafka.ps1 -KafkaBroker "localhost:9092" -KafkaTopic "inventor.results" -MaxQueueMessages 5000
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory = $true, HelpMessage = "Kafka bootstrap broker(s), e.g. 'localhost:9092'.")]
    [string]$KafkaBroker,

    [Parameter(Mandatory = $true, HelpMessage = "Kafka topic to publish result messages to.")]
    [string]$KafkaTopic,

    [Parameter(HelpMessage = "Seconds librdkafka keeps a queued message before expiring it (avoids blocking forever).")]
    [ValidateRange(1, 3600)]
    [int]$TimeoutSeconds = 10,

    [Parameter(HelpMessage = "Max messages buffered in the producer queue before backpressure (queue.buffering.max.messages).")]
    [ValidateRange(1, 10000000)]
    [int]$MaxQueueMessages = 100000,

    [Parameter(ValueFromPipeline = $true, HelpMessage = "Result line received from the pipeline.")]
    [string]$InputObject
)

begin {
    # The kcat (kafkacat) producer CLI must be available on PATH.
    if (-not (Get-Command -Name 'kcat' -ErrorAction SilentlyContinue)) {
        Write-Error @"
This script requires the 'kcat' (kafkacat) producer CLI, which was not found on PATH.
Install it and run the script again, e.g.:
  Debian/Ubuntu : sudo apt-get install kafkacat
  Fedora/RHEL   : sudo dnf install kcat
  macOS (brew)  : brew install kcat
"@
        exit 1
    }

    # A tab separates the per-message key from the JSON payload on each stdin line
    # (kcat -K). Compact JSON never contains a raw tab — embedded tabs are escaped
    # as \t — so the first tab unambiguously delimits key from value.
    $script:KeyDelimiter = "`t"

    # Bound how long librdkafka retries delivery so an unreachable broker cannot
    # hold messages (and ultimately stall stdin) forever.
    $timeoutMs = $TimeoutSeconds * 1000

    # Start a single, long-lived kcat producer and keep its stdin open for the
    # whole session. ArgumentList avoids any manual quoting of the arguments.
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName               = (Get-Command -Name 'kcat').Source
    $psi.RedirectStandardInput  = $true
    $psi.UseShellExecute        = $false
    $psi.StandardInputEncoding  = [System.Text.UTF8Encoding]::new($false)  # no BOM
    foreach ($a in @(
            '-P'
            '-b', $KafkaBroker
            '-t', $KafkaTopic
            '-K', $script:KeyDelimiter
            '-X', "message.timeout.ms=$timeoutMs"
            '-X', "queue.buffering.max.messages=$MaxQueueMessages"
        )) {
        $psi.ArgumentList.Add($a)
    }

    Write-Verbose "Starting shared kcat producer: $($psi.FileName) $($psi.ArgumentList -join ' ')"
    try {
        $script:Producer = [System.Diagnostics.Process]::Start($psi)
    }
    catch {
        Write-Error "Failed to start the kcat producer: $($_.Exception.Message)"
        exit 1
    }

    # Promptly hand each line to kcat rather than waiting for the writer to fill.
    $script:Producer.StandardInput.AutoFlush = $true
}

process {
    # Ignore blank lines that may appear between results.
    if ([string]::IsNullOrWhiteSpace($InputObject)) {
        return
    }

    # If the producer has died (e.g. fatal kcat error), surface it and stop
    # silently dropping results.
    if ($script:Producer.HasExited) {
        Write-Error "The kcat producer exited unexpectedly (code $($script:Producer.ExitCode)); cannot publish further results."
        return
    }

    # Use the test identifier as the message key when the payload carries one.
    $messageKey = $null
    try {
        $messageKey = ($InputObject | ConvertFrom-Json).Meta.TestId
    }
    catch {
        Write-Verbose "Could not parse Meta.TestId from the result; publishing without a key."
    }

    # Write one message per line as "<key><TAB><payload>". An empty key produces a
    # message with no (null) key, which is fine.
    $line = "$messageKey$($script:KeyDelimiter)$InputObject"
    try {
        $script:Producer.StandardInput.WriteLine($line)
    }
    catch {
        Write-Error "Failed to hand a result to the kcat producer: $($_.Exception.Message)"
    }
}

end {
    if (-not $script:Producer) {
        return
    }

    # Close stdin to signal end-of-input, then let kcat flush any queued messages.
    # Wait only a little longer than the delivery budget so a hung broker cannot
    # make the script itself hang here either.
    Write-Verbose "Closing kcat producer stdin and waiting for outstanding deliveries..."
    if (-not $script:Producer.HasExited) {
        $script:Producer.StandardInput.Close()
    }

    $waitMs = ($TimeoutSeconds * 1000) + 2000
    if (-not $script:Producer.WaitForExit($waitMs)) {
        Write-Warning "kcat did not exit within ${waitMs}ms after flushing; terminating it."
        try { $script:Producer.Kill() } catch { }
    }
    elseif ($script:Producer.ExitCode -ne 0) {
        Write-Error "kcat producer exited with code $($script:Producer.ExitCode); some results may not have been delivered."
    }

    $script:Producer.Dispose()
}
