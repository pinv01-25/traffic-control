#!/usr/bin/env python3
"""
Script automático para inicializar la base de datos de traffic-control
Intenta PostgreSQL primero, si falla después de 3 reintentos usa SQLite local
Se ejecuta automáticamente desde run.sh
"""

import os
import sys
import time
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Configuración de la base de datos PostgreSQL
DB_CONFIG = {
    'host': 'localhost',
    'database': 'traffic_control',
    'user': 'traffic_user',
    'password': 'traffic_pass'
}

MAX_RETRIES = 3
RETRY_DELAY = 2

def test_connection():
    """Prueba la conexión a PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ Conexión exitosa a PostgreSQL: {version}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Error conectando a PostgreSQL: {e}")
        return False

def test_connection_with_retries():
    """Intenta conectar a PostgreSQL con reintentos"""
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"Intento {attempt}/{MAX_RETRIES} de conexión a PostgreSQL...")
        if test_connection():
            return True
        if attempt < MAX_RETRIES:
            print(f"Esperando {RETRY_DELAY} segundos antes del siguiente intento...")
            time.sleep(RETRY_DELAY)
    return False

def check_table_exists():
    """Verifica si la tabla metadata_index existe"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'metadata_index'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        if table_exists:
            print("✓ Tabla metadata_index ya existe")
            return True
        return False
        
    except Exception as e:
        print(f"✗ Error verificando tabla: {e}")
        return False

def create_tables_postgresql():
    """Crea las tablas necesarias en PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Crear tabla metadata_index (compatible con el nuevo modelo)
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS metadata_index (
            id SERIAL PRIMARY KEY,
            type VARCHAR NOT NULL,
            timestamp BIGINT NOT NULL,
            traffic_light_id VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_metadata_index UNIQUE (type, timestamp, traffic_light_id)
        );
        """
        
        cursor.execute(create_table_sql)
        conn.commit()
        
        # Verificar que la tabla se creó
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'metadata_index'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✓ Tabla metadata_index creada correctamente en PostgreSQL")
            
            # Contar registros
            cursor.execute("SELECT COUNT(*) FROM metadata_index;")
            count = cursor.fetchone()[0]
            print(f"✓ Base de datos verificada - {count} registros en metadata_index")
        else:
            print("✗ Error: La tabla metadata_index no se creó")
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error creando tablas en PostgreSQL: {e}")
        return False

def init_sqlite():
    """Inicializa SQLite local usando SQLAlchemy"""
    try:
        # Importar el modelo para que se registre en Base.metadata (necesario para create_all)
        from database.db import Base
        
        print("📦 Inicializando base de datos SQLite local...")
        
        # Crear directorio si no existe
        db_dir = Path("data")
        db_dir.mkdir(exist_ok=True)
        
        # Configurar SQLite directamente
        db_path = db_dir / "traffic_control.db"
        sqlite_url = f"sqlite:///{db_path.absolute()}"
        
        # Crear engine para SQLite
        sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        
        # Crear tablas
        Base.metadata.create_all(bind=sqlite_engine)
        print("✓ Tabla metadata_index creada correctamente en SQLite")
        
        # Verificar que la tabla existe
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM metadata_index"))
            count = result.scalar()
            print(f"✓ Base de datos SQLite verificada - {count} registros en metadata_index")
        
        # Actualizar DATABASE_URL en el entorno para que database/db.py lo use
        os.environ["DATABASE_URL"] = sqlite_url
        print(f"✓ DATABASE_URL configurado para SQLite: {sqlite_url}")
        
        return True
    except Exception as e:
        print(f"✗ Error inicializando SQLite: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🔍 Verificando base de datos...")
    
    # Intentar conectar a PostgreSQL con reintentos
    if test_connection_with_retries():
        # PostgreSQL disponible
        print("✅ PostgreSQL disponible")
        
        # Verificar si la tabla ya existe
        if check_table_exists():
            print("✅ Base de datos PostgreSQL lista")
            return True
        
        print("📦 Creando tablas en PostgreSQL...")
        if create_tables_postgresql():
            print("✅ Base de datos PostgreSQL inicializada correctamente")
            return True
        else:
            print("⚠️  Error creando tablas en PostgreSQL, cambiando a SQLite...")
            return init_sqlite()
    else:
        # PostgreSQL no disponible después de reintentos
        print("⚠️  PostgreSQL no disponible después de 3 intentos")
        print("📦 Cambiando a SQLite local...")
        return init_sqlite()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 