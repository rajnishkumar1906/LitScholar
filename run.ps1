Start-Process powershell -ArgumentList "cd identity-service; ..\venv\Scripts\python.exe run.py"
Start-Process powershell -ArgumentList "cd rag-service; ..\venv\Scripts\python.exe run.py"
Start-Process powershell -ArgumentList "cd client; npm run dev"

