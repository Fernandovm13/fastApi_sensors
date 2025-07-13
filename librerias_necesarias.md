# Librerías Necesarias para el Proyecto

## Librerías Principales
- **fastapi** - Framework web para crear la API REST
- **uvicorn** - Servidor ASGI para ejecutar la aplicación FastAPI
- **pydantic** - Validación de datos y schemas
- **sqlalchemy** - ORM para manejo de base de datos
- **pymysql** - Driver para conectar con MySQL
- **python-dotenv** - Manejo de variables de entorno desde archivo .env

## Librerías para Análisis de Datos
- **pandas** - Análisis y manipulación de datos
- **numpy** - Cálculos numéricos
- **matplotlib** - Generación de gráficos y visualizaciones
- **requests** - Cliente HTTP para hacer peticiones a la API

## Comando de Instalación
```bash
pip install fastapi uvicorn pydantic sqlalchemy pymysql python-dotenv pandas numpy matplotlib requests
```

## Archivo requirements.txt
```
fastapi
uvicorn
pydantic
sqlalchemy
pymysql
python-dotenv
pandas
numpy
matplotlib
requests
```

## Nota
El proyecto también utiliza librerías estándar de Python que no requieren instalación:
- datetime, threading, time, random, uuid, urllib.parse, os, typing, statistics, sys