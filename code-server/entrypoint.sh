#!/bin/bash
# Fix SSH key permissions (bind-mounted from host with wrong uid)
if [ -f /home/coder/.ssh/id_ed25519 ]; then
    sudo cp /home/coder/.ssh/id_ed25519 /home/coder/.ssh/id_ed25519_fixed
    sudo chown coder:coder /home/coder/.ssh/id_ed25519_fixed
    chmod 600 /home/coder/.ssh/id_ed25519_fixed
fi

# Start code-server
exec dumb-init /usr/bin/code-server "$@"
