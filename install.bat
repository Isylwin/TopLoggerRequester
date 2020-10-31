@echo off

python --version
python -m venv venv
CALL venv\Scripts\activate.bat

ECHO Installing very important things and stuff if necessary
python -m pip install --upgrade pip
pip install -r requirements.txt
ECHO Installed all the very important things and stuff

PAUSE
