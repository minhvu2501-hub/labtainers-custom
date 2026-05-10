#!/bin/bash
: <<'END'
This software was created by United States Government employees at
The Center for Cybersecurity and Cyber Operations (C3O)
at the Naval Postgraduate School NPS.  Please note that within the
United States, copyright protection is not available for any works
created  by United States Government employees, pursuant to Title 17
United States Code Section 105.   This software is in the public
domain and is not subject to copyright.
END
#
# pregrade.sh  -  run prior to grading student's gateway_content_disarm lab
#                 (runs on the user_pc container)
#
# Purpose:
#   1) Run dropper.py against downloaded lofi_chill.wav
#   2) Write result to .dropper_result for grader to read
#
homedir=$1
destdir=$2

wav_file="$homedir/$destdir/lofi_chill.wav"
dropper="$homedir/$destdir/dropper.py"
result_file="$homedir/$destdir/.dropper_result"

# Check WAV file exists and is non-zero
if [ ! -f "$wav_file" ] || [ ! -s "$wav_file" ]; then
    echo "DROPPER_ERROR_NO_WAV" > "$result_file"
    exit 0
fi

# Run dropper, capture exit code
python3 "$dropper" "$wav_file" > /dev/null 2>&1
exit_code=$?

if [ $exit_code -eq 1 ]; then
    # Dropper failed to extract valid payload → defense succeeded
    echo "DROPPER_FAILED" > "$result_file"
elif [ $exit_code -eq 0 ]; then
    # Dropper extracted payload successfully → defense failed
    echo "DROPPER_SUCCEEDED" > "$result_file"
else
    echo "DROPPER_ERROR" > "$result_file"
fi
