#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";
const char* serverUrl = "https://TU_SERVIDOR_RENDER.onrender.com/audio";

#define FRAGMENT_SAMPLES 2205
float frag_buffer[FRAGMENT_SAMPLES]; // tu buffer de audio

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while(WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }
  Serial.println("Conectado a WiFi");
}

void loop() {
  // Aquí deberías llenar frag_buffer con audio del INMP441
  // Por simplicidad simulamos datos
  for(int i=0;i<FRAGMENT_SAMPLES;i++) frag_buffer[i] = random(-1000,1000)/1000.0;

  if(WiFi.status() == WL_CONNECTED){
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/octet-stream");
    http.POST((uint8_t*)frag_buffer, FRAGMENT_SAMPLES * sizeof(float));
    int code = http.GET(); // Puedes leer el código de respuesta
    String resp = http.getString();
    Serial.println("R detectada? " + resp);
    http.end();
  }
  delay(100);
}
