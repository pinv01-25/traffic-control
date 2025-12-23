#!/usr/bin/env python3
"""
Script automático para inicializar la base de datos PostgreSQL de traffic-control
Se ejecuta automáticamente desde run.sh
"""

import sys

import psycopg2

# Configuración de la base de datos PostgreSQL
DB_CONFIG = {
    'host': 'localhost',
    'database': 'traffic_control',
    'user': 'traffic_user',
    'password': 'traffic_pass'
}

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

def create_tables():
    """Crea las tablas necesarias en PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Crear tabla metadata_index
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS metadata_index (
            type VARCHAR NOT NULL,
            timestamp BIGINT NOT NULL,
            traffic_light_id VARCHAR NOT NULL,
            PRIMARY KEY (type, timestamp, traffic_light_id)
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
            print("✓ Tabla metadata_index creada correctamente")
            
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
        print(f"✗ Error creando tablas: {e}")
        return False

def main():
    """Función principal"""
    print("🔍 Verificando base de datos PostgreSQL...")
    
    # Probar conexión primero
    if not test_connection():
        print("❌ No se puede conectar a PostgreSQL")
        return False
    
    # Verificar si la tabla ya existe
    if check_table_exists():
        print("✅ Base de datos PostgreSQL lista")
        return True
    
    print("📦 Creando tablas en PostgreSQL...")
    if create_tables():
        print("✅ Base de datos PostgreSQL inicializada correctamente")
        return True
    else:
        print("❌ Error inicializando base de datos")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 