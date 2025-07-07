# migration_script.py - VERSIÓN CORREGIDA
"""
Script para migrar tu base de datos existente a la nueva estructura.
EJECUTAR SOLO UNA VEZ antes de usar las nuevas funcionalidades.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Product, Provider, init_db
import os

def migrate_database():
    """Migra la base de datos existente agregando soporte para proveedores"""
    
    print("🔄 Iniciando migración de base de datos...")
    
    # 1. Crear engine y session local
    engine = create_engine('sqlite:///pos.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 2. Verificar si la columna provider_id existe y agregarla si no
    try:
        with engine.connect() as conn:
            conn.execute(text('ALTER TABLE products ADD COLUMN provider_id INTEGER'))
            conn.commit()
        print("✅ Columna provider_id agregada exitosamente")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("ℹ️ Columna provider_id ya existe")
        else:
            print(f"⚠️ Error al agregar columna: {e}")
    
    # 3. Crear las tablas si no existen (especialmente la tabla providers)
    Base.metadata.create_all(engine, checkfirst=True)
    print("✅ Tablas verificadas/creadas")
    
    # 4. Crear algunos proveedores de ejemplo si no existen
    if session.query(Provider).count() == 0:
        proveedores_ejemplo = [
            Provider(name="Proveedor General", contact=""),
            Provider(name="Importaciones XYZ", contact="2222-3333"),
            Provider(name="Distribuidora ABC", contact="info@abc.com"),
            Provider(name="Mayorista 123", contact="8888-9999")
        ]
        
        for prov in proveedores_ejemplo:
            session.add(prov)
        
        session.commit()
        print("✅ Proveedores de ejemplo creados")
    else:
        print("ℹ️ Ya existen proveedores en la base de datos")
    
    # 5. Mostrar estadísticas
    total_products = session.query(Product).count()
    
    # Contar productos con proveedor (verificando si la columna existe)
    try:
        products_with_provider = session.query(Product).filter(Product.provider_id.isnot(None)).count()
    except:
        products_with_provider = 0
    
    products_without_provider = total_products - products_with_provider
    
    print(f"\n📊 Estadísticas de migración:")
    print(f"   • Total productos: {total_products}")
    print(f"   • Con proveedor asignado: {products_with_provider}")
    print(f"   • Sin proveedor: {products_without_provider}")
    print(f"   • Total proveedores: {session.query(Provider).count()}")
    
    if products_without_provider > 0:
        print(f"\n⚠️ Tienes {products_without_provider} productos sin proveedor asignado.")
        print("   Usa la nueva función 'Asignar Proveedor' en el inventario para completarlos.")
    
    session.close()
    
    print("\n🎉 ¡Migración completada exitosamente!")
    print("\n📋 Próximos pasos:")
    print("   1. Reemplaza database_setup.py con la versión mejorada")
    print("   2. Reemplaza tabs/inventario.py con la versión mejorada") 
    print("   3. Reemplaza tabs/entradas.py con la versión mejorada")
    print("   4. Ejecuta tu POS normalmente")
    print("   5. Asigna proveedores a productos existentes usando el botón 'Asignar Proveedor'")
    print("   6. Al hacer entradas, selecciona el proveedor correspondiente")

if __name__ == "__main__":
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('pos.db'):
        print("❌ Error: No se encontró pos.db")
        print("   Asegúrate de ejecutar este script desde la carpeta de tu proyecto")
        input("Presiona Enter para salir...")
        exit(1)
    
    if not os.path.exists('database_setup.py'):
        print("❌ Error: No se encontró database_setup.py")
        print("   Asegúrate de ejecutar este script desde la carpeta de tu proyecto")
        input("Presiona Enter para salir...")
        exit(1)
    
    migrate_database()
    input("\n✅ ¡Migración completada! Presiona Enter para continuar...")