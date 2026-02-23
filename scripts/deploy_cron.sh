#!/bin/bash

# Configuration
PROJECT_DIR="/opt/ims" # Adjust if different
BRANCH="main"

# Navigate to project
cd "$PROJECT_DIR" || exit 1

# Fetch latest changes
git fetch origin "$BRANCH"

# Check if local is behind remote
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "$(date): Changes detected. Deploying..."
    
    # Update code
    git pull origin "$BRANCH"
    
    # Rebuild and restart containers
    docker compose up -d --build --remove-orphans
    
    # Optional: Prune old images to save space
    docker image prune -f
    
    echo "$(date): Deployment successful."
else
    :
fi
