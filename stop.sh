#!/bin/bash
# Stop the validation app service (it restarts on next boot unless disabled)
systemctl --user stop kiln-validation-app.service
echo "Stopped kiln-validation-app."
