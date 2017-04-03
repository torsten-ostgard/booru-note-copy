cd $PSScriptRoot

if (!(Test-Path -Path venv )) {
    virtualenv venv
}

.\venv\Scripts\activate
pip install --upgrade pip
pip install pip-tools
pip-sync
