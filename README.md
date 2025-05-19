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
    ├── api/
    │   └── server.py
    ├── database/
    │   ├── db.py
    │   └── metadata_model.py
    ├── models/
    │   ├── __init__.py
    │   ├── validator.py
    │   └── schemas/
    │       ├── __init__.py
    │       ├── data_schema.py
    │       ├── download_schema.py
    │       └── optimization_schema.py
    ├── services/
    │   ├── storage_proxy.py
    │   └── sync_proxy.py
    └── utils/
        └── time.py
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

SYNC_API_URL=http://localhost:8001
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

Procesa una observación vehicular completa: valida, sube a storage, registra, recupera, y vuelve a subir.

**Cuerpo de la solicitud:**
```json
{
  "version": "1.0",
  "type": "data",
  "timestamp": "2025-05-01T15:30:00",
  "traffic_light_id": "TL-105",
  "controlled_edges": ["E1", "E2"],
  "metrics": {
    "vehicles_per_minute": 42,
    "avg_speed_kmh": 39.1,
    "avg_circulation_time_sec": 31.8,
    "density": 0.82
    },
  "vehicle_stats": {
    "motorcycle": 4,
    "car": 17,
    "bus": 0,
    "truck": 1
    }
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

---

## Arquitectura

### Validación (models/validator.py)

* Verifica versión, timestamp, tipo y campos requeridos según tipo (`data` u `optimization`).

### Almacenamiento (services/storage\_proxy.py)

* Sube/descarga datos hacia/desde `traffic-storage` usando `tls_id`, `timestamp`, `type`.

### Sincronización (services/sync\_proxy.py)

* Llama a `traffic-sync` vía `/evaluate` para obtener resultados optimizados.

### Base de Datos (database/)

* Guarda todos los registros con `tls_id`, `timestamp`, `type`.

---
## Autor
Majo Duarte
