volatile long encoderCount = 0;  // Contador global para os pulsos do encoder

const int pinA = 2;  // Canal A conectado ao pino 2
const int pinB = 3;  // Canal B conectado ao pino 3

void setup() {
  Serial.begin(115200);
  
  // Configure os pinos como entradas com pull-up interno para obter níveis lógicos estáveis
  pinMode(pinA, INPUT_PULLUP);
  pinMode(pinB, INPUT_PULLUP);
  
  // Configura a interrupção para o canal A na borda de subida
  attachInterrupt(digitalPinToInterrupt(pinA), encoderISR, RISING);
}

void encoderISR() {
  // Quando o canal A sobe, leia o estado do canal B
  if (digitalRead(pinB) == HIGH) {
    // Se B está HIGH, considere que a rotação foi no sentido horário (incrementa)
    encoderCount++;
  } else {
    // Se B está LOW, considere que a rotação foi no sentido anti-horário (decrementa)
    encoderCount--;
  }
}

void loop() {
  // Exibe o valor atual do contador do encoder
  Serial.print("Contador: ");
  Serial.println(encoderCount);
}