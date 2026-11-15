@echo off
cd /d "%~dp0"
py -m pip install -r requirements.txt
if errorlevel 1 (
 echo No se pudieron instalar las dependencias. Instala Python 3.10+ y comprueba tu conexion.
 pause
 exit /b 1
)
py main.py
if errorlevel 1 pause
