# db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Product  # ajusta el nombre si tu modelo está en otro módulo

# Conecta con pos.db (SQLite)
engine = create_engine('sqlite:///pos.db', echo=False)
Base.metadata.bind = engine

# Crea sesión
Session = sessionmaker(bind=engine)
session = Session()
