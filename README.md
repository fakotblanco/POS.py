# POS Py - Punto de Venta con PySide6

![POS Py](mi_icono.ico)

## Descripción

POS Py es un sistema de Punto de Venta (POS) desarrollado en Python con PySide6 para la interfaz gráfica y SQLite para la gestión de base de datos.  
Está diseñado para pequeños comercios que necesitan un control sencillo y eficiente de facturación, inventario, proveedores, pagos y caja.  
Cuenta con una interfaz basada en pestañas para manejar múltiples clientes y diferentes módulos de gestión en una misma aplicación.

## Características principales

- Gestión de facturación con pestañas para atender a dos clientes simultáneamente.  
- Control y administración de inventario con módulo específico.  
- Registro de entradas de productos, proveedores y pagos.  
- Módulo de caja para cierre y control de movimientos.  
- Resumen y balance general de las operaciones.  
- Atajos de teclado para navegación rápida entre pestañas.  
- Base de datos SQLite integrada para almacenamiento local.

## Requisitos

- Python 3.10+  
- PySide6==6.9.1  
- SQLAlchemy==2.0.41  
- greenlet==3.2.3  
- typing_extensions==4.14.0  
- Otras dependencias listadas en `requirements.txt`

## Instalación

1. Clona este repositorio:

   ```bash
   git clone https://github.com/fakotblanco/pos-py.git
   cd pos-py

2.Crea y activa un entorno virtual:

bash
Copiar
Editar
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate


3.Instala las dependencias:

bash
Copiar
Editar
pip install -r requirements.txt


Uso
Ejecuta la aplicación con:

bash
Copiar
Editar
python main.py


Licencia
Este proyecto está bajo la licencia MIT. Consulta el archivo LICENSE para más detalles.

© 2025 fakotblanco
Contacto: fakotblanco@gmail.com | GitHub
