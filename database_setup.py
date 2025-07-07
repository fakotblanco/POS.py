from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Boolean, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    # 🆕 NUEVA COLUMNA: Relación con proveedor
    provider_id = Column(Integer, ForeignKey('providers.id'), nullable=True)
    provider = relationship("Provider", back_populates="products")

class Provider(Base):
    __tablename__ = 'providers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    contact = Column(String)
    # 🆕 NUEVA RELACIÓN: Productos que vende este proveedor
    products = relationship("Product", back_populates="provider")

# ... resto de clases igual ...
class BulkProduct(Base):
    __tablename__ = 'bulk_products'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)

class Sale(Base):
    __tablename__ = 'sales'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    items = relationship("SaleItem", back_populates="sale")

class SaleItem(Base):
    __tablename__ = 'sale_items'
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sales.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product")

class Entry(Base):
    __tablename__ = 'entries'
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey('providers.id'))
    date = Column(Date, nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer, nullable=False)
    provider = relationship("Provider")
    product = relationship("Product")

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String)
    is_provider = Column(Boolean, default=False)

class Shift(Base):
    __tablename__ = 'shifts'
    id = Column(Integer, primary_key=True)
    user = Column(String, nullable=False)
    start = Column(DateTime, nullable=False)
    end = Column(DateTime)

class Balance(Base):
    __tablename__ = 'balances'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    total_sales = Column(Float, default=0)
    total_entries = Column(Float, default=0)
    total_payments = Column(Float, default=0)
    total_providers = Column(Float, default=0)
    balance = Column(Float, default=0)

DailyBalance = Balance

def init_db(path='pos.db'):
    """Inicializa la base de datos con la nueva estructura"""
    engine = create_engine(f'sqlite:///{path}')
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    global session
    session = Session()
    
    # 🆕 MIGRACIÓN: Agregar columna provider_id si no existe
    try:
        # Intentar agregar la columna si no existe
        engine.execute('ALTER TABLE products ADD COLUMN provider_id INTEGER')
        print("✅ Columna provider_id agregada exitosamente")
    except:
        # La columna ya existe, no hacer nada
        pass

def reset_db(path='pos.db'):
    """Reinicia la base de datos completamente"""
    engine = create_engine(f'sqlite:///{path}')
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    global session
    session = Session()

if __name__ == '__main__':
    init_db()