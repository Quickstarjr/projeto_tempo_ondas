@echo off
REM Rodar modo sanidade a partir da raiz do projeto
cd /d "%~dp0.."
python src\pipeline_v2.py --modo sanidade --output data\synthetic
pause