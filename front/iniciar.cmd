@echo off
setlocal

cd /d "%~dp0app"

where node >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js no esta instalado o no esta en el PATH.
  echo Instala Node.js y vuelve a ejecutar este archivo.
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm no esta disponible.
  echo Revisa la instalacion de Node.js.
  pause
  exit /b 1
)

if not exist node_modules (
  echo Instalando dependencias...
  call npm install
  if errorlevel 1 (
    echo [ERROR] No se pudieron instalar las dependencias.
    pause
    exit /b 1
  )
)

echo Abriendo http://localhost:5173
start "" "http://localhost:5173"

echo Iniciando servidor de desarrollo...
call npm run dev -- --host 127.0.0.1 --port 5173

pause
