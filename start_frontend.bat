@echo off
echo Starting BLING Dashboard Frontend...
cd dashboard
if not exist node_modules (
    echo Installing dependencies...
    call npm install
)
call npm run dev
pause
