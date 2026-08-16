@echo off
setlocal

set "APP_DIR=%~dp0app"
set "BACK_DIR=%~dp0..\back"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python no esta disponible.
  pause
  exit /b 1
)

python -c "import fastapi, uvicorn, joblib, pandas, sklearn" >nul 2>nul
if errorlevel 1 (
  echo Instalando dependencias del backend...
  python -m pip install -r "%BACK_DIR%\requirements.txt"
  if errorlevel 1 (
    echo [ERROR] No se pudieron instalar las dependencias del backend.
    pause
    exit /b 1
  )
)

echo Iniciando API local en http://127.0.0.1:8000
start "Precipita API" cmd /k "cd /d %BACK_DIR% && python -m uvicorn main:app --host 127.0.0.1 --port 8000"
timeout /t 4 /nobreak >nul

cd /d "%APP_DIR%"

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
