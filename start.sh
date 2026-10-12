#!/bin/bash
# Enable (start on boot) and start the validation app service
systemctl --user daemon-reload
systemctl --user enable kiln-validation-app.service
systemctl --user start kiln-validation-app.service
systemctl --user status kiln-validation-app.service --no-pager
