#!/bin/bash
# this script kills running test scripts
/usr/bin/pkill pwsh

# Capture the exit code of the pkill command
exit_code=$?

# Check the exit code and handle accordingly
if [ $exit_code -eq 0 ]; then
    echo "Process terminated successfully."
    exit 0  # Success
elif [ $exit_code -eq 1 ]; then
    echo "No matching processes found."
    exit 0  # No process to kill, but still consider as success
else
    echo "An error occurred with pkill."
    exit 1  # Error
fi
