@echo off

SET /A delay=240

CALL venv\Scripts\activate

python main.py -d %delay%

PAUSE