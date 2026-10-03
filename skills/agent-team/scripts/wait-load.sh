#!/bin/sh
# usage: wait-load.sh [max] — waits until the 5-minute load average is at or under max (default 6).
# Put it in front of anything heavy: sh wait-load.sh && sh start-review.sh 306 301
MAX=${1:-6}
load5() { uptime | awk -F'load averages?: ' '{split($2, a, /[, ]+/); print int(a[2])}'; }
while [ "$(load5)" -gt "$MAX" ]; do sleep 30; done
