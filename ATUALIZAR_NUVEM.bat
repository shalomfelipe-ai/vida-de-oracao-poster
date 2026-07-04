@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist ".git\index.lock" del /f /q ".git\index.lock"
git add -A
git commit -m "atualizacao de conteudo %date% %time%" || echo (nada novo)
git pull --rebase origin main
git push
echo PRONTO.
pause
