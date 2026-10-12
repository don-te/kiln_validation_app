#!/bin/bash
# Restart the validation app service (picks up app.py changes)
systemctl --user daemon-reload
systemctl --user restart kiln-validation-app.service
systemctl --user status kiln-validation-app.service --no-pager
