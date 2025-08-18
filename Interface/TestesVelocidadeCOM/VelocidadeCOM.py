import socket
import time
import serial
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Configuração da comunicação Serial
SERIAL_PORT = "COM3"  # Altere para sua porta COM
SERIAL_BAUD = 9600

# Configuração da comunicação TCP
TCP_HOST = "0.0.0.0"  # IP do ESP32
TCP_PORT = 12345  # Porta usada no ESP32

# Variáveis globais para armazenar dados
times_total = []
tempo_entre_pacotes = []
medias_entre_pacotes = []  # Armazena a média dos valores obtidos
tempo_inicio = time.time()
last_receive_time = tempo_inicio

def atualizar_grafico(frame):
    """Atualiza o gráfico em tempo real, incluindo a média dos valores."""
    plt.clf()

    # Plota o tempo entre pacotes
    plt.plot(times_total, tempo_entre_pacotes, marker="o", linestyle="-", label="Tempo entre pacotes")

    if len(tempo_entre_pacotes) >= 10:
        # Calcula a média dos últimos 10 valores
        media = np.mean(tempo_entre_pacotes[-10:])
        medias_entre_pacotes.append(media)

        # Plota a linha de tendência da média
        plt.plot(times_total[-len(medias_entre_pacotes):], medias_entre_pacotes, color="red", linestyle="--", label="Média móvel")

    plt.xlabel("Tempo Total (s)")
    plt.ylabel("Tempo entre pacotes (s)")
    plt.title("Monitoramento de Tempo Entre Pacotes")
    plt.legend()
    
    plt.ylim(0, 0.1)  # Limita o eixo Y

def monitorar_serial():
    """Monitoramento de dados via Serial em uma thread separada."""
    print(f"Monitorando dados via Serial ({SERIAL_PORT})...")
    try:
        ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
        while True:
            data = ser.readline().decode().strip()
            if data:
                processar_dados()
    except Exception as e:
        print(f"Erro na comunicação Serial: {e}")

def monitorar_tcp():
    """Monitoramento de dados via TCP/IP em uma thread separada."""
    print(f"Monitorando dados via TCP/IP na porta {TCP_PORT}...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((TCP_HOST, TCP_PORT))
    server_socket.listen(5)

    client_socket, client_address = server_socket.accept()
    print(f"Cliente conectado: {client_address}")

    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break
            processar_dados()
        except Exception as e:
            print(f"Erro na comunicação TCP: {e}")
            break

    client_socket.close()
    server_socket.close()

def processar_dados():
    """Processa os dados recebidos e registra o tempo entre pacotes."""
    global last_receive_time
    current_time = time.time()
    time_diff = current_time - last_receive_time
    last_receive_time = current_time

    tempo_total = current_time - tempo_inicio

    times_total.append(tempo_total)
    tempo_entre_pacotes.append(time_diff)

    # Verifica se a lista não está vazia antes de remover elementos
    if len(times_total) > 50:
        times_total.pop(0)
    if len(tempo_entre_pacotes) > 50:
        tempo_entre_pacotes.pop(0)
    if len(medias_entre_pacotes) > 50:
        medias_entre_pacotes.pop(0)

    print(f"Tempo Total: {tempo_total:.3f} s | Tempo entre pacotes: {time_diff:.3f} s")

modo = input("Escolha o modo de monitoramento ('serial' ou 'tcp'): ").strip().lower()

# Configuração do gráfico
fig, ax = plt.subplots()
ani = FuncAnimation(fig, atualizar_grafico, interval=500)  # Atualiza o gráfico a cada 500ms

# Inicia o monitoramento de dados em uma thread separada
if modo == "serial":
    threading.Thread(target=monitorar_serial, daemon=True).start()
elif modo == "tcp":
    threading.Thread(target=monitorar_tcp, daemon=True).start()
else:
    print("Modo inválido. Escolha 'serial' ou 'tcp'.")

plt.show()