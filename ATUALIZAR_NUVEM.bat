@echo off
chcp 65001 >nul
cd /d "%~dp0"
git add -A
git commit -m "atualizacao de conteudo %date% %time%" || echo (nada novo)
git push
echo PRONTO.
pause
