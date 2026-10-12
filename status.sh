#!/bin/bash
# Service state, listening port, and recent logs
systemctl --user status kiln-validation-app.service --no-pager
echo; echo "=== Port 8501 ==="
ss -tlpn 2>/dev/null | grep 8501
echo; echo "=== Recent logs ==="
tail -n 15 "$(dirname "$(readlink -f "$0")")/app_run.log"
