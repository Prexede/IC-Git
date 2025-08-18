#include <WiFi.h>

const char* ssid = "BrownieGordo2.4";
const char* password = "Kartodromo";
WiFiServer server(12345);
WiFiClient clients[5];  // Array para múltiplos clientes

unsigned long lastSendTime = 0; // Variável para controle de tempo

void setup() {
    Serial.begin(115200);
    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\n✅ Conectado ao Wi-Fi!");
    Serial.print("Endereço IP: ");
    Serial.println(WiFi.localIP());

    server.begin(); // Inicia o servidor TCP
}

void loop() {
    // Verifica novas conexões
    WiFiClient newClient = server.available();
    if (newClient) {
        for (int i = 0; i < 5; i++) {
            if (!clients[i]) { 
                clients[i] = newClient;
                Serial.println("🔹 Novo cliente conectado!");
                break;
            }
        }
    }

    // 🔹 Enviar mensagem a cada 1 segundo
    if (millis() - lastSendTime >= 100) {
        lastSendTime = millis(); // Atualiza o tempo
        String mensagem = "Mensagem periodica do ESP32: " + String(millis());

        Serial.println(mensagem); // 🔹 Envia para o Serial

        // 🔹 Envia para todos os clientes TCP
        for (int i = 0; i < 5; i++) {
            if (clients[i] && clients[i].connected()) {
                clients[i].println(mensagem);
            } else {
                clients[i].stop();
                clients[i] = WiFiClient();
            }
        }
    }
}