@echo off
echo Starting BLING Sandbox (Full System)...

echo Starting backend containers...
docker compose up -d

echo Checking dashboard dependencies...
cd dashboard
if not exist node_modules (
    echo Installing dependencies...
    call npm install
)

echo Starting frontend dev server...
echo The dashboard will be available at http://localhost:3000
call npm run dev
pause
