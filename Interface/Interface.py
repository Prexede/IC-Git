import tkinter as tk
from tkinter import PhotoImage
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def Graficos():
    
    # Cria um gráfico usando Matplotlib
    fig = Figure(figsize=(5, 4), dpi=100)
    plot = fig.add_subplot(1, 1, 1)
    plot.plot([0, 1, 2, 3], [0, 1, 4, 9])  # Exemplo de dados para o gráfico

    # Incorpora o gráfico na janela do Tkinter
    canvas = FigureCanvasTkAgg(fig, master=janela)  # A 'master' é a janela do Tkinter
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    
    
def Conexao():
    grafico = Graficos.canvas.get_tk_widget()
    grafico.destroy()


# Cria a janela principal
janela = tk.Tk()
janela.title('Exemplo Tkinter')

# Define a largura e a altura desejadas
largura = 1280
altura = 720
# Configura a resolução da janela
janela.geometry(f'{largura}x{altura}')

# Carrega a imagem de fundo
caminho_imagem = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\FundoTelemetria.png'  # Substitua com o caminho correto da sua imagem
imagem_fundo = PhotoImage(file=caminho_imagem)

# Redimensiona a imagem para cobrir toda a janela
imagem_fundo = imagem_fundo.zoom(1)  # Ajuste o fator de zoom conforme necessário
imagem_fundo = imagem_fundo.subsample(1)  # Ajuste o fator de subsample conforme necessário

# Configura a imagem de fundo
label_fundo = tk.Label(janela, image=imagem_fundo)
label_fundo.place(x=0, y=0, relwidth=1, relheight=1)

#########################################################################################################3
# Cria um Frame3d para a barra lateral
barra_lateral = tk.Frame(janela, width=100, height=300, bg='#5179AA')
barra_lateral.pack(side='left', fill='none')  # Posiciona a barra lateral à esquerda

# Adiciona botões à barra lateral

################# CONEXAO ####################
# Carrega a imagem para o botão
caminho_imagemBotaoWifi = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Conexao.png'
imagem_botaoWifi = PhotoImage(file=caminho_imagemBotaoWifi)
# Cria um botão com a imagem e o posiciona no Frame3d
botao1 = tk.Button(barra_lateral, image=imagem_botaoWifi, compound='center', command=Conexao)
botao1.pack(pady=50)  # Adiciona espaço vertical entre os botões

############### GRAFICOS #####################################################
caminho_imagemBotaoGrafico = r'C:\Users\carlo\OneDrive\Documentos\Drive\Faculdade\IC\Interface\Background\Grafico.png' 
imagem_botaoGrafico = PhotoImage(file=caminho_imagemBotaoGrafico)
botao2 = tk.Button(barra_lateral, image=imagem_botaoGrafico, compound='center', command=Graficos)
botao2.pack(pady=50)

############################################################################################################

# Inicia o loop principal da interface gráfica
janela.mainloop()



### https://www.youtube.com/watch?v=95tJO7XJlko Video que pode ajudar a divisão de paginas