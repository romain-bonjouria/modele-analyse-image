$ErrorActionPreference = "Stop"

Write-Host "[1/3] Installation des dépendances..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "[2/3] Build de l'exécutable..."
Remove-Item -Recurse -Force ".\\dist\\RagClientApp" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ".\\build\\RagClientApp" -ErrorAction SilentlyContinue
Remove-Item -Force ".\\dist\\RagClientApp.exe" -ErrorAction SilentlyContinue
pyinstaller `
  --noconfirm `
  --clean `
  --onedir `
  --name RagClientApp `
  --paths src `
  --add-data "src/streamlit_app.py;." `
  --hidden-import rag_service `
  --hidden-import chromadb `
  --hidden-import ollama `
  --copy-metadata streamlit `
  --copy-metadata chromadb `
  --copy-metadata ollama `
  --collect-all streamlit `
  --collect-all chromadb `
  --collect-all ollama `
  src/windows_launcher.py

Write-Host "[3/3] Terminé"
Write-Host "Executable disponible: dist/RagClientApp/RagClientApp.exe"
