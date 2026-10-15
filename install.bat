@echo off
chcp 65001 >nul
title Instalador PDF Manager

echo.
echo ========================================
echo        INSTALADOR PDF MANAGER
echo ========================================
echo.
echo Este programa vai preparar o sistema para
echo executar o Gerenciador de PDFs.
echo.
echo NÃO é necessário conhecimento técnico!
echo.
pause

echo.
echo Criando pasta para armazenar PDFs...
if not exist "pdf_storage" (
    mkdir pdf_storage
    echo ✅ Pasta 'pdf_storage' criada
) else (
    echo ✅ Pasta 'pdf_storage' já existe
)

echo.
echo Verificando se o Python está instalado...
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Python está instalado
    goto :python_ok
) else (
    echo ❌ Python não encontrado
    echo.
    echo É necessário ter o Python instalado.
    echo.
    echo Vamos abrir o site para download...
    echo.
    pause
    start https://www.python.org/downloads/
    echo.
    echo Por favor, instale o Python e execute este instalador novamente.
    echo.
    pause
    exit
)

:python_ok
echo.
echo Configuração concluída com sucesso!
echo.
echo ========================================
echo         COMO USAR O PROGRAMA
echo ========================================
echo.
echo OPÇÃO 1 - Executar com Python:
echo   1. Feche esta janela
echo   2. Clique duas vezes no arquivo 'main.py'
echo   3. O programa vai abrir automaticamente
echo.
echo OPÇÃO 2 - Criar executável (RECOMENDADO):
echo   1. Clique duas vezes no arquivo 'criar_executavel.bat'
echo   2. Aguarde o processo terminar
echo   3. Vá na pasta 'dist' e clique duas vezes em 'PDFManager.exe'
echo.
echo ========================================
echo.
pause