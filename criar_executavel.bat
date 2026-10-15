@echo off
chcp 65001 >nul
title Criando Executável PDF Manager

echo.
echo ========================================
echo    CRIANDO EXECUTÁVEL PDF MANAGER
echo ========================================
echo.
echo Este processo vai criar um arquivo .exe
echo para você usar sem precisar do Python.
echo.
echo Pode demorar alguns minutos...
echo.
pause

echo.
echo Passo 1: Instalando PyInstaller...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo ❌ Erro ao instalar PyInstaller
    echo Tente executar como Administrador
    pause
    exit
)

echo.
echo Passo 2: Criando executável...
pyinstaller --onefile --windowed --name "PDFManager" main.py

echo.
if exist "dist\PDFManager.exe" (
    echo ✅ EXECUTÁVEL CRIADO COM SUCESSO!
    echo.
    echo Arquivo: dist\PDFManager.exe
    echo.
    echo Agora você pode:
    echo 1. Fechar esta janela
    echo 2. Entrar na pasta 'dist'
    echo 3. Clique duas vezes em 'PDFManager.exe'
    echo 4. Usar o programa sem precisar do Python!
) else (
    echo ❌ Erro ao criar executável
)

echo.
pause