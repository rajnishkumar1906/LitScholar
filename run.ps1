Start-Process powershell -ArgumentList "cd identity-service; python run.py"
Start-Process powershell -ArgumentList "cd rag-service; python run.py"
Start-Process powershell -ArgumentList "cd client; npm run dev"

