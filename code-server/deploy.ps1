# Deploy code-server stack to IMS server
# Usage: .\deploy.ps1

$SERVER = "ims@77.42.66.251"
$SSH_PORT = "2222"
$SSH_KEY = "$env:USERPROFILE\.ssh\id_ims"
$REMOTE_DIR = "/opt/code-server"
$SSH_CMD = "ssh -p $SSH_PORT -i $SSH_KEY $SERVER"
$SCP_CMD = "scp -P $SSH_PORT -i $SSH_KEY"

Write-Host "=== Deploying code-server to IMS server ===" -ForegroundColor Cyan

# 1. Create remote directory
Write-Host "`n[1/7] Creating remote directory..." -ForegroundColor Yellow
Invoke-Expression "$SSH_CMD 'sudo mkdir -p $REMOTE_DIR && sudo chown ims:ims $REMOTE_DIR'"

# 2. Copy Docker files
Write-Host "[2/7] Copying Docker files..." -ForegroundColor Yellow
$files = @(
    "Dockerfile.code-server",
    "docker-compose.yml",
    "ssh-config",
    "settings.json"
)
foreach ($file in $files) {
    Invoke-Expression "$SCP_CMD $file ${SERVER}:${REMOTE_DIR}/"
}

# 3. Copy .env (secrets)
Write-Host "[3/7] Copying .env..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Invoke-Expression "$SCP_CMD .env ${SERVER}:${REMOTE_DIR}/"
} else {
    Write-Host "  WARNING: .env not found! Copy .env.example and fill in values." -ForegroundColor Red
    exit 1
}

# 4. Create projects directory
Write-Host "[4/7] Creating projects directory..." -ForegroundColor Yellow
Invoke-Expression "$SSH_CMD 'mkdir -p /home/ims/projects'"

# 5. Install nginx config for code.agentportal.nl
Write-Host "[5/7] Installing nginx config..." -ForegroundColor Yellow
Invoke-Expression "$SCP_CMD nginx-code-server.conf ${SERVER}:/tmp/nginx-code-server.conf"
Invoke-Expression "$SSH_CMD 'sudo cp /tmp/nginx-code-server.conf /etc/nginx/sites-available/code-server && sudo ln -sf /etc/nginx/sites-available/code-server /etc/nginx/sites-enabled/code-server && sudo nginx -t && sudo systemctl reload nginx'"

# 6. Build and start containers
Write-Host "[6/7] Building and starting containers..." -ForegroundColor Yellow
Invoke-Expression "$SSH_CMD 'cd $REMOTE_DIR && sudo docker compose up -d --build'"

# 7. Get SSL certificate via Certbot
Write-Host "[7/7] Requesting SSL certificate..." -ForegroundColor Yellow
Invoke-Expression "$SSH_CMD 'sudo certbot --nginx -d code.agentportal.nl --non-interactive --agree-tos --email admin@agentportal.nl'"

Write-Host "`n=== Deploy complete ===" -ForegroundColor Green
Write-Host "Access: https://code.agentportal.nl" -ForegroundColor Cyan
