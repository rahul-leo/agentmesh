Write-Host "Starting AgentMesh Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\Users\RAHUL\OneDrive\Desktop\intern project\intern project\agentmesh'; .\.venv\Scripts\Activate.ps1; uvicorn backend.main:app --reload"

Write-Host "Starting AgentMesh Frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\Users\RAHUL\OneDrive\Desktop\intern project\intern project\agentmesh\frontend'; npm run dev"

Write-Host "Starting AgentMesh Streamlit Dashboard..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\Users\RAHUL\OneDrive\Desktop\intern project\intern project\agentmesh'; .\.venv\Scripts\Activate.ps1; streamlit run streamlit_app.py"
