import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)

Base = declarative_base()

# Intentar conectar a PostgreSQL con reintentos
def _try_postgresql_connection(database_url: str, max_retries: int = 3, retry_delay: int = 2) -> bool:
    """
    Intenta conectar a PostgreSQL con reintentos.
    
    Args:
        database_url: URL de conexión a PostgreSQL
        max_retries: Número máximo de reintentos
        retry_delay: Segundos de espera entre reintentos
    
    Returns:
        True si la conexión fue exitosa, False en caso contrario
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Intento {attempt}/{max_retries} de conexión a PostgreSQL...")
            test_engine = create_engine(database_url, connect_args={"connect_timeout": 5})
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ Conexión exitosa a PostgreSQL")
            return True
        except Exception as e:
            logger.warning(f"✗ Intento {attempt} fallido: {e}")
            if attempt < max_retries:
                logger.info(f"Esperando {retry_delay} segundos antes del siguiente intento...")
                time.sleep(retry_delay)
            else:
                logger.error(f"❌ No se pudo conectar a PostgreSQL después de {max_retries} intentos")
                return False
    return False

def _get_sqlite_url() -> str:
    """
    Genera la URL para SQLite local.
    
    Returns:
        URL de conexión para SQLite
    """
    # Crear directorio para la base de datos si no existe
    db_dir = Path("data")
    db_dir.mkdir(exist_ok=True)
    
    db_path = db_dir / "traffic_control.db"
    sqlite_url = f"sqlite:///{db_path.absolute()}"
    logger.info(f"Usando SQLite local: {sqlite_url}")
    return sqlite_url

def _initialize_database():
    """
    Inicializa la conexión a la base de datos.
    Intenta PostgreSQL primero, si falla usa SQLite.
    Si DATABASE_URL ya está configurado (por ejemplo, por auto_init_db.py), lo usa directamente.
    """
    global engine, SessionLocal, DATABASE_URL
    
    # Obtener DATABASE_URL del entorno
    postgres_url = os.getenv("DATABASE_URL")
    
    if not postgres_url:
        logger.warning("DATABASE_URL no configurado, usando SQLite por defecto")
        DATABASE_URL = _get_sqlite_url()
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(bind=engine)
        return
    
    # Si ya es SQLite (configurado por auto_init_db.py), usarlo directamente
    if postgres_url.startswith("sqlite:///"):
        logger.info("DATABASE_URL ya configurado para SQLite, usando directamente")
        DATABASE_URL = postgres_url
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(bind=engine)
        return
    
    # Verificar si es una URL de PostgreSQL
    if not postgres_url.startswith("postgresql://") and not postgres_url.startswith("postgres://"):
        logger.info("DATABASE_URL no es PostgreSQL ni SQLite, usando directamente")
        DATABASE_URL = postgres_url
        # Intentar detectar si necesita check_same_thread
        if "sqlite" in postgres_url.lower():
            engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        return
    
    # Intentar conectar a PostgreSQL
    if _try_postgresql_connection(postgres_url):
        # Conexión exitosa a PostgreSQL
        DATABASE_URL = postgres_url
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        logger.info("✅ Base de datos PostgreSQL configurada correctamente")
    else:
        # Fallback a SQLite
        logger.warning("⚠️  Cambiando a SQLite local después de fallar la conexión a PostgreSQL")
        DATABASE_URL = _get_sqlite_url()
        # Actualizar la variable de entorno para que otros módulos la vean
        os.environ["DATABASE_URL"] = DATABASE_URL
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(bind=engine)
        logger.info("✅ Base de datos SQLite configurada correctamente")

# Inicializar la conexión
_initialize_database()

def init_db():
    """Inicializa las tablas en la base de datos."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas de base de datos inicializadas correctamente")
    except Exception as e:
        logger.error(f"❌ Error inicializando tablas: {e}")
        raise
