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
# pregrade.sh  -  run prior to grading student's audio_steg_analysis lab
#
# Purpose:
#   1) Parse browser history (default)
#   2) Any additional pre-processing of student artifacts
#
homedir=$1
destdir=$2
cd $homedir/$destdir
exec > pregrade.log 2>&1
set -x

is_sqlite=`which sqlite3`
if [ ! -z $is_sqlite ]; then
   here=`pwd`
   places=$here/.mozilla/firefox/*default/places.sqlite
   for fname in $(ls $places 2>/dev/null); do
     if [[ -f $fname ]]; then
        outpath=$here/.local/result
        outfile=$outpath/moz_places.txt
        mkdir -p "$outpath"
        sqlite3 "$fname" "SELECT moz_places.* FROM moz_places;" >"$outfile"
     fi
   done
fi

#
#  Normalize answers.txt: strip whitespace and ensure lowercase keys
#
answers_file="$homedir/$destdir/answers.txt"
if [[ -f "$answers_file" ]]; then
    sed -i 's/ //g' "$answers_file"   # remove all spaces
fi
exit 0
