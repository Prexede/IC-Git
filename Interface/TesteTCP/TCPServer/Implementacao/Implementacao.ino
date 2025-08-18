#include <Wire.h>
#include <WiFi.h>

// 🔹 Configuração do Wi-Fi
const char* ssid = "BrownieGordo2.4";
const char* password = "Kartodromo";
//const char* ssid = "cubo";
//const char* password = "cubocubo";
const int NumClients = 1;
WiFiServer server(12345);
WiFiClient clients[NumClients];  // Array para múltiplos clientes

unsigned long lastSendTime = 0; // Variável para controle de tempo

// 🔹 Configuração da Serial
#define SERIAL_BAUD 115200  // Velocidade da comunicação serial
//9600 115200 230400 460800 921600



// 🔹 Configuração dos encoders
const int E1ChannelA = 2; //Preto
const int E1ChannelB = 4; //Branco
const int E1ChannelZ = 5; //Laranja

volatile int somador = 0;
volatile int E1counter = 0;
bool E1Direction;
volatile int Angle = 0;

// 🔹 Funções de interrupção para leitura dos encoders
void FuncE1Counter() {
    int A1_val = digitalRead(E1ChannelA);
    int B1_val = digitalRead(E1ChannelB);

    if (B1_val == LOW) {
        E1counter++;
        E1Direction = true; 
    } else {
        E1counter--;
        E1Direction = false;
    }
}

void FuncE1Origin() {
    int Z1 = digitalRead(E1ChannelZ);
    if (Z1 == HIGH) {
        E1counter = 0;
    }
}
int Pulse2Angle(int Pulse){
    //Serial.println(Pulse);
    if (Pulse >= 0){
        Angle = (Pulse*360)/3600;
    } else {
        Pulse = 360 + Pulse;
        Angle = (Pulse*360)/3600;
    }
    //Serial.println(Angle);
    return Angle;
}

//////////////////////////////////////////////////////////// SETUP ////////////////////////////////////////////////////////////
void setup() {
    Serial.begin(SERIAL_BAUD);  // Inicializa comunicação Serial

    // 🔹 Conectar ao Wi-Fi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\n✅ Conectado ao Wi-Fi!");
    Serial.print("🔹 Endereço IP: ");
    Serial.println(WiFi.localIP());

    server.begin();  // 🔹 Inicia o servidor TCP

    // 🔹 Configuração dos pinos do encoder
    pinMode(E1ChannelA, INPUT);
    pinMode(E1ChannelB, INPUT);
    pinMode(E1ChannelZ, INPUT);

    attachInterrupt(digitalPinToInterrupt(E1ChannelA), FuncE1Counter, RISING);
    attachInterrupt(digitalPinToInterrupt(E1ChannelZ), FuncE1Origin, RISING);
}

//////////////////////////////////////////////////////////// LOOP ////////////////////////////////////////////////////////////
void loop() {
    // 🔹 Verifica novas conexões de clientes
    WiFiClient newClient = server.available();
    if (newClient) {
        for (int i = 0; i < NumClients; i++) {
            if (!clients[i]) { 
                clients[i] = newClient;
                Serial.println("🔹 Novo cliente conectado!");
                break;
            }
        }
    }

    // 🔹 Enviar dados do encoder
    if (millis() - lastSendTime >= 50) {
        lastSendTime = millis(); // Atualiza o tempo

        int mensagem = somador;
        somador++;

        mensagem = (Pulse2Angle(E1counter));
        // 🔹 Monta a mensagem a ser enviada
        String mensagemCompleta = String(mensagem) + " " + String(mensagem + 10) + " " + String(mensagem - 20);
        
        // 🔹 Envia para todos os clientes conectados via Wi-Fi
        for (int i = 0; i < NumClients; i++) {
            if (clients[i] && clients[i].connected()) {
                clients[i].println(mensagemCompleta);  
            } else {
                clients[i].stop();
                clients[i] = WiFiClient();
            }
        }

        // 🔹 Envia também via Serial
        Serial.println(mensagemCompleta);  // Envia os dados pela porta COM para um dispositivo Serial
        
    }
}