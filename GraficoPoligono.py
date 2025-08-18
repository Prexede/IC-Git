import numpy as np
import matplotlib.pyplot as plt

# Valores de n
n_values = np.arange(2, 14, 2)  # n de 1 a 50

# Calculando I para diferentes valores de n
I_values = np.sin(np.pi / n_values)

# Criando a figura e os subgráficos
fig, ax = plt.subplots()

# Plotando os pontos
ax.plot(n_values, I_values, marker='o', linestyle='-', color='b', label=r'$I = \sin(\frac{\pi}{n})$')

# Adicionando título e rótulos
ax.set_title("$I = \sin(\pi / n)$")
ax.set_xlabel("Numero de arestas [n]")
ax.set_ylabel("Momento de força [I]")

# Adicionando legenda
ax.legend()

ax.grid()
# Exibindo o gráfico
plt.show()