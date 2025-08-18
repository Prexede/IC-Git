import socket

ESP_IP = "192.168.0.112"  # Substitua pelo IP do ESP32
ESP_PORT = 12345

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((ESP_IP, ESP_PORT))

while True:
    try:
        data = client.recv(10).decode()  # Aguarda até que novos dados sejam recebidos
        if data:  # Apenas exibe se há conteúdo na mensagem
            print(f" Dados recebidos: {data}")
    except socket.error as e:
        print(f"Erro na comunicação: {e}")
        break  # Encerra se houver erro grave na conexão