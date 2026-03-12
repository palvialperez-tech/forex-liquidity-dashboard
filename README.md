# Forex Liquidity Dashboard

Dashboard interactivo para análisis de liquidez en el mercado Forex, diseñado para detectar zonas de interés institucional, sweeps de liquidez y posibles puntos de entrada utilizando conceptos de Smart Money Concepts (SMC).

El sistema procesa datos históricos de mercado, identifica señales relevantes y las visualiza en un dashboard interactivo construido en Python.

## Objetivo del proyecto

El objetivo es construir un motor de análisis que permita:

- Detectar zonas de liquidez
- Identificar posibles sweeps de liquidez
- Clasificar señales por probabilidad
- Visualizar el contexto del mercado
- Apoyar la toma de decisiones en trading

Este proyecto forma parte del desarrollo del **Liquidity Target Engine**, un sistema que prioriza objetivos de liquidez en el mercado.

## Tecnologías utilizadas

- Python
- Pandas
- Plotly
- Streamlit
- Trading Data APIs
- Smart Money Concepts (SMC)

## Funcionalidades

- Descarga automática de datos históricos
- Identificación de zonas de liquidez
- Ranking de señales activas
- Clasificación de señales descartadas
- Visualización mediante heatmap de liquidez
- Dashboard interactivo en Streamlit

## Estructura del proyecto


forex_liquidity_dashboard

config/
config-minimal.yaml

data/
raw/

modules/
liquidity/
signals/
ranking/

scripts/
run_download.py

run_pipeline.py

dashboard/
plot_liquidity_heatmap.py


## Ejecución rápida

Instalar dependencias:


pip install -r requirements.txt


Descargar datos:


python scripts/run_download.py


Ejecutar dashboard:


streamlit run run_pipeline.py


El dashboard se abrirá en:


http://localhost:8501


## Ejemplo de análisis

El sistema detecta:

- zonas de liquidez
- sweeps de mercado
- proximidad del precio a zonas institucionales
- ranking de señales según contexto y distancia al precio

Esto permite identificar oportunidades de trading con mayor probabilidad.

## Futuras mejoras

- integración con TradingView
- alertas automáticas
- integración con Telegram
- detección avanzada de Order Blocks
- motor de backtesting

## Autor

Patricio Alvial  
Data Engineer | Trading Systems Developer

Especializado en:

- Data Engineering
- Automatización de análisis financiero
- Sistemas de trading cuantitativo

prints:

<img width="1774" height="772" alt="image" src="https://github.com/user-attachments/assets/71fbdcaf-ba5c-4247-8c16-bed164bcea9a" />

<img width="1767" height="726" alt="image" src="https://github.com/user-attachments/assets/769e85cd-be84-4134-8a34-32ea6185c7e9" />

<img width="1786" height="857" alt="image" src="https://github.com/user-attachments/assets/215befbf-58e8-42b2-b1cc-e8f59f1f0891" />


<img width="1793" height="808" alt="image" src="https://github.com/user-attachments/assets/49a69df2-ddbc-4424-946e-a093c77be1c1" />

<img width="1848" height="746" alt="image" src="https://github.com/user-attachments/assets/aae70002-a02a-4ddb-9ac7-e2ff2dc8a79b" />

<img width="1870" height="665" alt="image" src="https://github.com/user-attachments/assets/70b914fc-be9f-45e9-b710-832d841ecd0c" />

