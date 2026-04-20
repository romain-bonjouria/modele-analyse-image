$ErrorActionPreference = "Stop"

Write-Host "[1/3] Installation des dépendances..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "[2/3] Build de l'exécutable..."
pyinstaller --noconfirm --clean --onefile --name RagClientApp --paths src --add-data "src/streamlit_app.py;." src/windows_launcher.py

Write-Host "[3/3] Terminé"
Write-Host "Executable disponible: dist/RagClientApp.exe"
