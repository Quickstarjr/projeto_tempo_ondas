import numpy as np
import matplotlib.pyplot as plt

# Cria uma grade 2D (simulando uma fatia do universo)
x = np.linspace(-1, 1, 500)
y = np.linspace(-1, 1, 500)
X, Y = np.meshgrid(x, y)

# Função de Bessel (modo fundamental de uma placa circular)
def modo_chladni(X, Y, freq, fase=0):
    r = np.sqrt(X**2 + Y**2)
    theta = np.arctan2(Y, X)
    # Simula um modo circular (Bessel)
    return np.cos(freq * np.pi * r) * np.cos(3 * theta + fase)

# 1. Uma única frequência (Modo fundamental)
Z1 = modo_chladni(X, Y, freq=2.0, fase=0)

# 2. Múltiplas frequências (Superposição - Ideia do Quickstar)
Z2 = modo_chladni(X, Y, freq=2.0, fase=0) + 0.5 * modo_chladni(X, Y, freq=5.0, fase=np.pi/4)

# Plotagem
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Painel 1: Uma única onda
axes[0].contourf(X, Y, np.abs(Z1), levels=20, cmap='Greys')
axes[0].set_title('Chladni: Uma Única Frequência\n(Nós isolados)')
axes[0].set_xlabel('X')
axes[0].set_ylabel('Y')
axes[0].set_aspect('equal')

# Painel 2: Superposição de 2 ondas
axes[1].contourf(X, Y, np.abs(Z2), levels=20, cmap='Greys')
axes[1].set_title('Chladni: Superposição de 2 Frequências\n(Estrutura fractal/hierárquica)')
axes[1].set_xlabel('X')
axes[1].set_ylabel('Y')
axes[1].set_aspect('equal')

plt.tight_layout()
plt.savefig('outputs/plots/chladni_multiplas_frequencias.png', dpi=120)
print("[+] Gráfico salvo em outputs/plots/chladni_multiplas_frequencias.png")