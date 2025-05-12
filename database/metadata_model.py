from sqlalchemy import Column, String, BigInteger
from database.db import Base

class MetadataIndex(Base):
    __tablename__ = "metadata_index"

    type = Column(String, primary_key=True)
    timestamp = Column(BigInteger, primary_key=True)
    traffic_light_id = Column(String, primary_key=True)

