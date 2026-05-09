#!/bin/bash

DEST=$1

echo "[+] collect.sh running" > /tmp/collect_debug.txt

echo "[+] DEST=$DEST" >> /tmp/collect_debug.txt

echo "[+] HOME=$HOME" >> /tmp/collect_debug.txt

find /home -name "answers.txt" >> /tmp/collect_debug.txt 2>&1
find /home -name ".bash_history" >> /tmp/collect_debug.txt 2>&1

find /home -name "answers.txt" -exec cp {} $DEST/ \; 2>>/tmp/collect_debug.txt

find /home -name ".bash_history" -exec cp {} $DEST/ \; 2>>/tmp/collect_debug.txt

ls -la $DEST >> /tmp/collect_debug.txt 2>&1
