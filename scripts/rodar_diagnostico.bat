@echo off
REM Rodar modo diagnóstico a partir da raiz do projeto
cd /d "%~dp0.."
python src\pipeline_v2.py --modo diagnostico --output data\synthetic
pause