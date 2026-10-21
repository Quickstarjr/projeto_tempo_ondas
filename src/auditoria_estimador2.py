# Executar no terminal, dentro do projeto:
#   cd ~/projeto_tempo_ondas
#   python -c "..."
import pandas as pd
from src.auditoria_estimador import rodar_experimento

df1 = rodar_experimento(REPS=30, seed_master=20261021)
df2 = rodar_experimento(REPS=30, seed_master=20261021)
pd.testing.assert_frame_equal(df1, df2)
print("T1 OK: bit-a-bit idênticos")