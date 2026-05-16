@echo off
echo Starting BLING Sandbox Backend Services...
docker compose up -d
echo Backend services are starting in the background.
echo Use 'docker compose logs -f' to view logs.
pause
