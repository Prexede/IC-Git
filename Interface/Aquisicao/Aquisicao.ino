#include <Wire.h>
#include <WiFi.h>

///////////////// CONFIGURAÇÂO WIFI///////////////////////////////
const char* ssid = "BrownieGordo2.4";
const char* password = "Kartodromo";
WiFiServer server(12345);
WiFiClient clients[5];  // Array para múltiplos clientes
//////////////////////////////////////////////////////////////////


// Setar PINOS A,B e Z dos encoder
///////////////////////////////////////////////////////////////////////////////////////Encoder 1 (Centro)////////////////////////////////////////////////////////////
const int E1ChannelA = 2; //Pino que lerá a interrupção
const int E1ChannelB = 4;
const int E1ChannelZ = 5;
//Contadores de pulso e sentido de rotação
volatile int E1counter = 0;
bool E1Direction;
volatile int Angle = 0;
// Funções de contagem de pulsos
void FuncE1Counter(){
    int A1_val = digitalRead(E1ChannelA);
    int B1_val = digitalRead(E1ChannelB);
    /*
    Serial.print("A");
    Serial.println(A1_val);
    Serial.print("B");
    Serial.println(B1_val);
    */
    
    if ((B1_val == LOW)) {   // Se o canal A estiver alto e o B baixo quando ele fizer a leitura, temos o movimetno no sentido horário
        E1counter++;
        E1Direction = true; //Sentido Horário

      } else{
        E1counter--;
        E1Direction = false;
      }

    //Serial.print("Count");
    //Serial.println(E1counter);
    //return E1counter;
}

void FuncE1Origin(){
    int Z1 = digitalRead(E1ChannelZ);
    //Serial.print("Z");
    //Serial.println(Z1);
    if(Z1 == HIGH){
        E1counter = 0;
    }
    //return E1counter;
}


///////////////////////////////////////////////////////////////////////////////////////Encoder 2 (Interno)////////////////////////////////////////////////////////////
/*int E2ChannelA = XX; //Pino que lerá a interrupção
int E2ChannelB = XX;
int E2ChannelZ = XX;
//Contadores de pulso e sentido de rotação
int E2counter = 0;
bool E2Direction;

// Funções de contagem de pulsos
void FuncE2Counter(){
    int A2 = digitalRead(E2ChannelA);
    int B2 = digitalRead(E2ChannelB);
    
    if ((A2 == HIGH) == (B2 == LOW)) {   // Se o canal A estiver alto e o B baixo quando ele fizer a leitura, temos o movimetno no sentido horário
        E2counter++;
        E2Direction = true; //Sentido Horário
      } else {
        E2counter--;
        E2Direction = false;
      }
}

void FuncE2Origin(){
    int Z2 = digitalRead(E2ChannelZ);
    if(Z2 == HIGH){
        E2counter = 0;
    }
}

///////////////////////////////////////////////////////////////////////////////////////Encoder 3 (Externo)////////////////////////////////////////////////////////////
int E3ChannelA = XX; //Pino que lerá a interrupção
int E3ChannelB = XX;
int E3ChannelZ = XX;
//Contadores de pulso e sentido de rotação
int E3counter = 0;
bool E3Direction;

// Funções de contagem de pulsos
void FuncE3Counter(){
    int A3 = digitalRead(E3ChannelA);
    int B3 = digitalRead(E3ChannelB);
    
    if ((A3 == HIGH) == (B3 == LOW)) {   // Se o canal A estiver alto e o B baixo quando ele fizer a leitura, temos o movimetno no sentido horário
        E3counter++;
        E3Direction = true; //Sentido Horário
      } else {
        E3counter--;
        E3Direction = false;
      }
}

void FuncE3Origin(){
    int Z3 = digitalRead(E3ChannelZ);
    if(Z3 == HIGH){
        E3counter = 0;
    }
}
*/
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

////////////////////////////////////////////////////////////SETUP////////////////////////////////////////////////////////////
void setup() {
Serial.begin(9600);
//Definição de pinos para entrada do encoder
//Encoder 1
pinMode(E1ChannelA,INPUT);
pinMode(E1ChannelB,INPUT);
pinMode(E1ChannelZ,INPUT);
//Interrupção encoder
attachInterrupt(digitalPinToInterrupt(E1ChannelA),FuncE1Counter, RISING);
//Interrupção Origem
attachInterrupt(digitalPinToInterrupt(E1ChannelZ),FuncE1Origin, RISING);

//Encoder 2
/*
pinMode(E2ChannelA,INPUT);
pinMode(E2ChannelB,INPUT);
pinMode(E2ChannelZ,INPUT);
//Interrupção encoder
attachInterrupt(digitalPinToInterrupt(E2ChannelA),FuncE2Counter, RISING);
//Interrupção Origem
attachInterrupt(digitalPinToInterrupt(E2ChannelZ),FuncE2Origin, RISING);

//Encoder 3
pinMode(E3ChannelA,INPUT);
pinMode(E3ChannelB,INPUT);
pinMode(E3ChannelZ,INPUT);
//Interrupção encoder
attachInterrupt(digitalPinToInterrupt(E3ChannelA),FuncE3Counter, RISING);
//Interrupção Origem
attachInterrupt(digitalPinToInterrupt(E3ChannelZ),FuncE3Origin, RISING);
*/
}


////////////////////////////////////////////////////////////MAIN LOOP ////////////////////////////////////////////////////////////
void loop() {
    //Serial.print("Angulo Encoder 1: ");
    //Serial.println(Pulse2Angle(E1counter));
    int mensagem = (E1counter);
    String mensagemCompleta = String(mensagem) + " " + String(mensagem + 10) + " " + String(mensagem - 20);
    Serial.println(mensagemCompleta);
    //Serial.println("\nAngulo Encoder 2: %d",Pulse2Angle(E2counter))
    //Serial.println("\nAngulo Encoder 3: %d",Pulse2Angle(E3counter))
}