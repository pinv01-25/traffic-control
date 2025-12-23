from database.db import Base
from sqlalchemy import BigInteger, Column, String


class MetadataIndex(Base):
    __tablename__ = "metadata_index"

    type = Column(String, primary_key=True)
    timestamp = Column(BigInteger, primary_key=True)
    traffic_light_id = Column(String, primary_key=True)

