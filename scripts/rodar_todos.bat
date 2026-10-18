@echo off
REM Rodar os 3 modos em sequência
cd /d "%~dp0.."

echo ============================================
echo TESTE 1 — DIAGNOSTICO
echo ============================================
python src\pipeline_v2.py --modo diagnostico --output data\synthetic

echo.
echo ============================================
echo TESTE 2 — SANIDADE
echo ============================================
python src\pipeline_v2.py --modo sanidade --output data\synthetic

echo.
echo ============================================
echo TESTE 3 — ANISOTROPIA
echo ============================================
python src\pipeline_v2.py --modo anisotropia --output data\synthetic

echo.
echo Todos os testes concluidos.
pause