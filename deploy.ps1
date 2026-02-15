param(
    [switch]$InitOnly  # First-time setup: create dirs, copy .env
)

$SERVER = "77.42.66.251"
$PORT = "2222"
$USER = "ims"
$KEY = "C:\Users\shgst\.ssh\id_ims"
$REMOTE_DIR = "/opt/IMS"
$LOCAL_DIR = "X:\DEV\IMS"

Write-Host "=== IMS Deploy ===" -ForegroundColor Cyan

# Ensure remote directory exists
ssh -i $KEY -p $PORT "$USER@$SERVER" "mkdir -p $REMOTE_DIR"

if ($InitOnly) {
    Write-Host "First-time setup..." -ForegroundColor Yellow

    # Copy .env to server
    Write-Host "Copying .env to server..."
    scp -i $KEY -P $PORT "$LOCAL_DIR\.env" "${USER}@${SERVER}:${REMOTE_DIR}/.env"
}

Write-Host "Creating local archive..."
$excludes = "--exclude=node_modules --exclude=.next --exclude=__pycache__ --exclude=*.pyc --exclude=.pytest_cache --exclude=.venv --exclude=venv --exclude=.env --exclude=.git --exclude=deploy.tar.gz --exclude=illustrations"
tar -czf deploy.tar.gz -C "$LOCAL_DIR" $excludes backend frontend docker-compose.yml .env.example

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create tar archive."
    exit 1
}

Write-Host "Copying archive to server..."
scp -i $KEY -P $PORT deploy.tar.gz "${USER}@${SERVER}:${REMOTE_DIR}/deploy.tar.gz"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to copy archive to server."
    exit 1
}

Write-Host "Extracting archive on server..."
$remoteCmd = "cd $REMOTE_DIR && tar -xzf deploy.tar.gz && rm deploy.tar.gz"
ssh -i $KEY -p $PORT "$USER@$SERVER" $remoteCmd

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to extract archive on server."
    exit 1
}

# Build and start services
Write-Host "Building and starting services..."
ssh -i $KEY -p $PORT "$USER@$SERVER" "cd $REMOTE_DIR && docker compose up -d --build --remove-orphans"

# Run migrations
Write-Host "Running database migrations..."
ssh -i $KEY -p $PORT "$USER@$SERVER" "cd $REMOTE_DIR && docker compose exec -T ims-api alembic upgrade head"

# Clean up local archive
if (Test-Path "deploy.tar.gz") {
    Remove-Item "deploy.tar.gz"
}

# Show status
Write-Host ""
Write-Host "=== Service Status ===" -ForegroundColor Cyan
ssh -i $KEY -p $PORT "$USER@$SERVER" "cd $REMOTE_DIR && docker compose ps"

Write-Host ""
Write-Host "Deploy complete!" -ForegroundColor Green
