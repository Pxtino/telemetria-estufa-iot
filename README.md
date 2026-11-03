# 🌱 Plataforma de Telemetria IoT - Estufa Inteligente

Plataforma de monitoramento assíncrono, controle bidirecional e análise de microclima para estufas agrícolas.

## 🚀 Funcionalidades da Plataforma

* **Monitoramento Interativo:** Dashboard web (Streamlit + Plotly) exibindo séries temporais de Temperatura, Umidade, Luminosidade (Lux) e integridade do nó sensor (Bateria).
* **Máquina de Estados Dinâmica:** Lógica autônoma para prevenção de déficit hídrico e estresse térmico. Os limiares de acionamento (Piso Hídrico e Teto Térmico) são parametrizáveis em tempo real na interface, sem necessidade de reiniciar o sistema.
* **Controle Manual (Two-Way MQTT):** Capacidade de atuar sobre a estufa, publicando pacotes JSON no tópico de comandos do broker para acionar a bomba de irrigação ou ventilação manualmente.
* **Datalogger Embutido:** Exportação do histórico da sessão de monitoramento em `.csv` com um clique, facilitando análises estatísticas multivariadas posteriores.

## 🏗️ Arquitetura e Stack Tecnológico

* **Comunicação:** Protocolo MQTT (Broker público HiveMQ).
* **Edge / Hardware:** Nó sensor baseado na arquitetura ESP32 integrado com DHT22 e LDR (atualmente operando em simulação Python via `simulador.ipynb`).
* **Cloud / Frontend:** Python 3, Streamlit (Interface), Pandas (Thread-safe memory e DataFrames), Paho-MQTT e Plotly Express.

## ⚙️ Instalação e Execução

**1. Dependências**
Recomenda-se o uso de um ambiente virtual (ex: Miniconda). No terminal, instale as bibliotecas necessárias:
```bash
pip install paho-mqtt streamlit pandas plotly

**2. Execução Assíncrona**
O sistema requer que o painel e o nó sensor rodem em paralelo. Abra dois terminais na pasta do projeto:

**Terminal 1 (Painel Web):**
```bash
streamlit run app_estufa.py

*O painel abrirá automaticamente no navegador no endereço `http://localhost:8501`.*

**Terminal 2 (Nó Sensor):**
```bash
python simulador.py