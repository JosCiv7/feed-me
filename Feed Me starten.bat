@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Eerste keer: vertaler en tekstlezer installeren...
  python -m venv .venv
)
.venv\Scripts\python.exe -m pip install --quiet --disable-pip-version-check -r requirements.txt
echo Nieuws ophalen, lezen en vertalen...
.venv\Scripts\python.exe fetcher\fetch_news.py
echo.
echo Feed Me draait op http://localhost:8321  (sluit dit venster om te stoppen)
start "" http://localhost:8321
python -m http.server 8321 --directory app
