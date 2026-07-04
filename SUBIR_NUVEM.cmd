@echo off
chcp 65001 >nul
cd /d "%~dp0"
where git >nul 2>nul || (echo ERRO: Git nao instalado. Baixe em https://git-scm.com/download/win ^(instalacao padrao^) e rode de novo. & pause & exit /b 1)
if not exist .git (
  git init -b main
  git remote add origin https://github.com/shalomfelipe-ai/vida-de-oracao-poster.git
  git config user.name "Felipe Bezerra"
  git config user.email "shalomfelipe-ai@users.noreply.github.com"
)
echo Subindo tudo para o GitHub (na 1a vez abre o login: escolha "Sign in with your browser", conta shalomfelipe-ai)...
git add -A
git commit -m "poster backup na nuvem: scripts + conteudo (fila ate 28/07)" || echo (nada novo para commitar)
git push -u origin main
echo.
echo PRONTO. Confira em https://github.com/shalomfelipe-ai/vida-de-oracao-poster
pause
