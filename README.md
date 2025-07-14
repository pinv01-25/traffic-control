# Traffic-Control: Servicio de Orquestación de Tráfico Inteligente

Traffic-Control es el módulo orquestador del sistema distribuido de gestión de tráfico. Valida, registra, almacena, recupera y optimiza datos vehiculares generados por simulaciones urbanas. Coordina la interacción entre `traffic-sim`, `traffic-storage` e `traffic-sync`, asegurando un flujo coherente de datos. Expone una API RESTful que sirve como punto de entrada central al sistema.

---

## Estructura del Directorio

```
└── pinv01-25-traffic-control/
    ├── README.md
    ├── LICENSE
    ├── requirements.txt
    ├── run.sh
    ├── vercel.json
    ├── config/
    │   ├── __init__.py
    │   ├── settings.py
    │   └── logging_config.py
    ├── api/
    │   └── server.py
    ├── database/
    │   ├── db.py
    │   └── metadata_model.py
    ├── models/
    │   ├── __init__.py
    │   ├── validator.py
    │   ├── response_models.py
    │   └── schemas/
    │       ├── __init__.py
    │       ├── data_schema.py
    │       ├── download_schema.py
    │       └── optimization_schema.py
    ├── services/
    │   ├── process_service.py
    │   ├── database_service.py
    │   ├── data_processor.py
    │   ├── storage_proxy.py
    │   └── sync_proxy.py
    ├── utils/
    │   ├── time.py
    │   └── error_handler.py
    └── examples/
        └── batch_data_example.py
```

---

## Primeros Pasos

### Requisitos previos
* Python ≥ 3.10

* PostgreSQL (u otro motor soportado por SQLAlchemy)

* Variables de entorno configuradas:

  * .env con:
```
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/dbname
STORAGE_API_URL=http://localhost:8000
SYNC_API_URL=http://localhost:8002
```

### Instalar dependencias
```
pip install -r requirements.txt
```

### Ejecutar el servidor
```
./run.sh
```

Visita: [http://localhost:8003](http://localhost:8003)

---

## API REST

### POST /process

Procesa una observación vehicular completa: valida, sube a storage, registra, recupera, y vuelve a subir. Maneja tanto sensores individuales como lotes de 1-10 sensores.

**Cuerpo de la solicitud (sensor individual):**
```json
{
  "version": "2.0",
  "type": "data",
  "timestamp": "2025-05-19T14:20:00Z",
  "traffic_light_id": "21",
  "sensors": [
    {
      "traffic_light_id": "21",
      "controlled_edges": ["edge42", "edge43"],
      "metrics": {
        "vehicles_per_minute": 65,
        "avg_speed_kmh": 43.5,
        "avg_circulation_time_sec": 92,
        "density": 0.72
      },
      "vehicle_stats": {
        "motorcycle": 12,
        "car": 45,
        "bus": 2,
        "truck": 6
      }
    }
  ]
}
```

**Cuerpo de la solicitud (lote de sensores):**
```json
{
  "version": "2.0",
  "type": "data",
  "timestamp": "2025-05-19T14:20:00Z",
  "traffic_light_id": "21",
  "sensors": [
    {
      "traffic_light_id": "21",
      "controlled_edges": ["edge42", "edge43"],
      "metrics": {
        "vehicles_per_minute": 65,
        "avg_speed_kmh": 43.5,
        "avg_circulation_time_sec": 92,
        "density": 0.72
      },
      "vehicle_stats": {
        "motorcycle": 12,
        "car": 45,
        "bus": 2,
        "truck": 6
      }
    },
    {
      "traffic_light_id": "22",
      "controlled_edges": ["edge44", "edge45"],
      "metrics": {
        "vehicles_per_minute": 78,
        "avg_speed_kmh": 38.2,
        "avg_circulation_time_sec": 105,
        "density": 0.85
      },
      "vehicle_stats": {
        "motorcycle": 8,
        "car": 52,
        "bus": 5,
        "truck": 13
      }
    }
  ]
}
```

**Respuesta:**
```json
{
"status": "success",
"message": "Data processed and optimized successfully"
}
```

### GET /healthcheck

Verifica que el servicio esté activo.

### Endpoints de Metadatos

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/metadata/traffic-light/{id}` | GET | Obtener metadatos por semáforo |
| `/metadata/type/{type}` | GET | Obtener metadatos por tipo |
| `/metadata/recent` | GET | Obtener metadatos recientes |
| `/metadata/stats` | GET | Obtener estadísticas de metadatos |
| `/metadata/traffic-light/{id}` | DELETE | Eliminar metadatos por semáforo |

---

## Arquitectura

### Validación (models/validator.py)

* Verifica versión, timestamp, tipo y campos requeridos según tipo (`data` u `optimization`).
* Validación de IDs de semáforo: solo números (`"21"`, `"22"`, etc.)
* Validación de límites: 1-10 sensores por lote
* Tipo `data` unificado: maneja tanto sensores individuales como lotes

### Almacenamiento (services/storage_proxy.py)

* Sube/descarga datos hacia/desde `traffic-storage` usando `tls_id`, `timestamp`, `type`.
* Soporte para lotes de datos y datos individuales.

### Sincronización (services/sync_proxy.py)

* Llama a `traffic-sync` vía `/evaluate` para obtener resultados optimizados.
* Soporte para optimización de lotes con múltiples sensores.

### Base de Datos (database/)

* Guarda todos los registros con `tls_id`, `timestamp`, `type`.
* Nuevos endpoints para gestión de metadatos.

### Manejo de Errores (utils/error_handler.py)

* Manejo centralizado de errores con contexto.
* Respuestas de error estandarizadas.
* Logging automático de errores.

### Respuestas Estandarizadas (models/response_models.py)

* Formato consistente para todas las respuestas de la API.
* Factory pattern para crear respuestas estandarizadas.

---

## Pruebas

### Pruebas con curl
```bash
# Health check
curl -X GET http://localhost:8003/healthcheck

# Procesar sensor individual
curl -X POST http://localhost:8003/process \
  -H "Content-Type: application/json" \
  -d '{
    "version": "2.0",
    "type": "data",
    "timestamp": "2025-05-19T14:20:00Z",
    "traffic_light_id": "21",
    "sensors": [
      {
        "traffic_light_id": "21",
        "controlled_edges": ["edge42", "edge43"],
        "metrics": {
          "vehicles_per_minute": 65,
          "avg_speed_kmh": 43.5,
          "avg_circulation_time_sec": 92,
          "density": 0.72
        },
        "vehicle_stats": {
          "motorcycle": 12,
          "car": 45,
          "bus": 2,
          "truck": 6
        }
      }
    ]
  }'
```

---

## Configuración

### Variables de Entorno

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `DATABASE_URL` | `sqlite:///./traffic_control.db` | URL de conexión a la base de datos |
| `STORAGE_API_URL` | `http://localhost:8000` | URL del servicio de almacenamiento |
| `SYNC_API_URL` | `http://localhost:8002` | URL del servicio de sincronización |

---

## Compatibilidad

**Nuevas funcionalidades:**
- Tipo `data` unificado que maneja tanto sensores individuales como lotes
- Endpoint `/process` unificado para procesar sensores individuales y lotes
- Compatibilidad total hacia atrás con el formato original
- Validación mejorada para lotes de 1-10 sensores

---

## Autor
Majo Duarte
