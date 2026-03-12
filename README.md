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
