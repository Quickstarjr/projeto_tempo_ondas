@echo off
REM Rodar modo anisotropia a partir da raiz do projeto
cd /d "%~dp0.."
python src\pipeline_v2.py --modo anisotropia --output data\synthetic
pause