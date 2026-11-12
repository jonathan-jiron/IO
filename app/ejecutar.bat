@echo off
title Servidor PERT-CPM (no cierres esta ventana)
cd /d "%~dp0"
echo Iniciando en http://127.0.0.1:8765 ...
python server.py
if errorlevel 1 py server.py
echo.
echo Si ves un error arriba, copialo. Para detener el servidor cierra esta ventana.
pause
