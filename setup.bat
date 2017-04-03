set BASEDIR=%~dp0
chdir /d %BASEDIR%

if not exist "venv" virtualenv venv

call .\venv\Scripts\activate
pip install --upgrade pip
pip install pip-tools
pip-sync
