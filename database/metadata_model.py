from datetime import datetime

from database.db import Base
from sqlalchemy import BigInteger, Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.sql import func


class MetadataIndex(Base):
    __tablename__ = "metadata_index"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)
    timestamp = Column(BigInteger, nullable=False)
    traffic_light_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    
    # Constraint único para evitar duplicados (equivalente a la PK compuesta original)
    __table_args__ = (
        UniqueConstraint('type', 'timestamp', 'traffic_light_id', name='uq_metadata_index'),
    )

