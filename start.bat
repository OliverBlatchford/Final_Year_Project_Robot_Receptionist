@echo off
cd "C:\Users\olive\OneDrive\Desktop\Final year project\PepperReceptionist"

for /f %%i in ('venv\Scripts\python.exe -c "from config import PEPPER_IP; print(PEPPER_IP)"') do set PEPPER_IP=%%i

start "Flask" cmd /k "cd /d "C:\Users\olive\OneDrive\Desktop\Final year project\PepperReceptionist" && venv\Scripts\activate && python app.py"
timeout /t 2 /nobreak >nul
start "Startup" cmd /k "ssh nao@%PEPPER_IP% bash /home/nao/startup.sh"
timeout /t 2 /nobreak >nul
start "Bridge" cmd /k "cd /d "C:\Users\olive\OneDrive\Desktop\Final year project\PepperReceptionist" && C:\Python27\python.exe pepperBridge.py"
timeout /t 2 /nobreak >nul
start "Main" cmd /k "cd /d "C:\Users\olive\OneDrive\Desktop\Final year project\PepperReceptionist" && venv\Scripts\activate && python main.py"
