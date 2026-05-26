from sqlalchemy import Column, Integer, Float, String
from database import Base

class Contrato(Base):
    __tablename__ = "contratos"

    id = Column(Integer, primary_key=True, index=True)
    precio_alquiler = Column(Float, nullable=True)
    penalizacion_retraso = Column(Float, nullable=True)
    fecha_inicio = Column(String, nullable=True)
    fecha_fin = Column(String, nullable=True)
    propietario = Column(String, nullable=True)
    arrendatario = Column(String, nullable=True)
    direccion_inmueble = Column(String, nullable=True)
    moneda = Column(String, nullable=True)