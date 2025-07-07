# tabs/agranel.py - VERSIÓN CON DISEÑO CONSISTENTE
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QFormLayout, QDialogButtonBox, QDoubleSpinBox, QAbstractItemView,
    QLabel, QHeaderView
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer
from db import session
from database_setup import BulkProduct

class AgranelTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(15)

        # Timer para búsqueda con delay
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        # ========== TÍTULO DE SECCIÓN ==========
        title = QLabel("⚖️ Gestión de Productos a Granel")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; margin: 10px 0;")
        self.layout().addWidget(title)

        # ========== INFORMACIÓN DESCRIPTIVA ==========
        info_label = QLabel("🛒 Gestione productos vendidos por peso (kg, libras, etc.)")
        info_label.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 10px;")
        self.layout().addWidget(info_label)

        # ========== BARRA DE BÚSQUEDA CON DISEÑO CONSISTENTE ==========
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        search_label = QLabel("🔍 Buscar:")
        search_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        search_layout.addWidget(search_label)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Código o nombre del producto a granel")
        self.search.setStyleSheet(
            """
            QLineEdit {
                min-height: 35px; 
                font-size: 14px; 
                background-color: #FAFAFA;
                padding: 8px 12px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
                background-color: white;
            }
            """
        )
        self.search.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search, 3)
        search_layout.addStretch()
        
        self.layout().addLayout(search_layout)

        # ========== TABLA CON DISEÑO CONSISTENTE ==========
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Código", "Producto", "Precio por Kg"])
        
        # Configuración de columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Código
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Producto se expande
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Precio
        
        # Estilo consistente con otras pestañas
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            """
            QTableWidget {
                background-color: white;
                alternate-background-color: #F8F9FA;
                gridline-color: #DEE2E6;
                border: 1px solid #DEE2E6;
                font-size: 14px;
                color: #212529;
            }
            QHeaderView::section {
                background-color: #8E44AD;
                color: white;
                padding: 12px 8px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-right: 1px solid #A569BD;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #E9ECEF;
            }
            QTableWidget::item:selected {
                background-color: #E8DAEF;
                color: #6C3483;
            }
            """
        )
        
        # Configuración de edición y selección
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Fuente optimizada (más pequeña que el original)
        table_font = QFont()
        table_font.setPointSize(14)
        self.table.setFont(table_font)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.verticalHeader().setVisible(False)

        self.layout().addWidget(self.table)

        # ========== BOTONES CON DISEÑO CONSISTENTE ==========
        btns = QHBoxLayout()
        btns.setSpacing(8)
        
        # Botones principales
        button_style = """
            QPushButton {
                background-color: #8E44AD;
                color: white;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #7D3C98;
            }
            QPushButton:pressed {
                background-color: #6C3483;
            }
        """
        
        self.btn_add = QPushButton("➕ Agregar Producto")
        self.btn_add.setStyleSheet(button_style)
        
        self.btn_edit = QPushButton("✏️ Editar Producto")
        self.btn_edit.setStyleSheet(button_style)
        
        # Botón eliminar con color rojo pero manteniendo la consistencia
        self.btn_del = QPushButton("🗑️ Eliminar Producto")
        self.btn_del.setStyleSheet(
            """
            QPushButton {
                background-color: #DC3545;
                color: white;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:pressed {
                background-color: #BD2130;
            }
            """
        )
        
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_edit)
        btns.addWidget(self.btn_del)
        btns.addStretch()  # Empujar botones hacia la izquierda
        
        self.layout().addLayout(btns)

        # ========== CONEXIONES ==========
        self.btn_add.clicked.connect(self.add_item)
        self.btn_edit.clicked.connect(self.edit_item)
        self.btn_del.clicked.connect(self.delete_item)

        # Carga inicial
        self.load()

    def on_search_changed(self, text):
        """✅ BÚSQUEDA CON DELAY: Evita lag al escribir"""
        self.search_timer.stop()
        if len(text) >= 2 or len(text) == 0:  # Buscar solo con 2+ caracteres o vacío
            self.search_timer.start(300)  # Esperar 300ms antes de buscar

    def perform_search(self):
        """✅ EJECUTAR BÚSQUEDA"""
        self.load()

    def load(self):
        """✅ Cargar productos a granel con filtro de búsqueda"""
        try:
            text = self.search.text().lower().strip()
            
            # Query base
            query = session.query(BulkProduct)
            
            # Aplicar filtro si hay texto de búsqueda
            if text:
                query = query.filter(
                    (BulkProduct.code.ilike(f'%{text}%')) |
                    (BulkProduct.name.ilike(f'%{text}%'))
                )
            
            items = query.order_by(BulkProduct.id).all()
            
            # Llenar tabla
            self.table.setRowCount(len(items))
            for r, i in enumerate(items):
                code_item = QTableWidgetItem(i.code)
                name_item = QTableWidgetItem(i.name)
                price_item = QTableWidgetItem(f"₡{int(i.price):,}")
                
                # Resaltar productos con precios altos
                if i.price > 5000:  # Más de 5000 por kg
                    price_item.setBackground(Qt.GlobalColor.yellow)
                
                self.table.setItem(r, 0, code_item)
                self.table.setItem(r, 1, name_item)
                self.table.setItem(r, 2, price_item)
                
        except Exception as e:
            print(f"❌ Error cargando productos a granel: {e}")
            QMessageBox.warning(self, "Error", f"Error cargando productos: {str(e)}")

    def show_dialog(self, prod=None):
        """✅ Diálogo mejorado para agregar/editar productos"""
        dlg = QDialog(self)
        dlg.setWindowTitle("Agregar Producto a Granel" if not prod else f"Editar: {prod.name}")
        dlg.setModal(True)
        dlg.setStyleSheet(
            """
            QDialog {
                background-color: white;
            }
            QLineEdit, QDoubleSpinBox {
                padding: 8px 12px;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                background-color: #FAFAFA;
                min-height: 20px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus {
                border: 2px solid #8E44AD;
                background-color: white;
            }
            """
        )
        
        form = QFormLayout(dlg)
        form.setSpacing(15)
        
        inp_code = QLineEdit(prod.code if prod else "")
        inp_code.setPlaceholderText("Código único del producto")
        
        inp_name = QLineEdit(prod.name if prod else "")
        inp_name.setPlaceholderText("Nombre descriptivo del producto")
        
        inp_price = QDoubleSpinBox()
        inp_price.setDecimals(0)
        inp_price.setRange(0, 1e6)
        inp_price.setPrefix("₡")
        inp_price.setSuffix(" /kg")
        inp_price.setValue(int(prod.price) if prod else 0)
        
        form.addRow("⚖️ Código:", inp_code)
        form.addRow("🏷️ Nombre:", inp_name)
        form.addRow("💰 Precio por kg:", inp_price)
        
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("✅ Guardar")
        bb.button(QDialogButtonBox.Cancel).setText("❌ Cancelar")
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)
        
        if dlg.exec() == QDialog.Accepted:
            code = inp_code.text().strip()
            name = inp_name.text().strip()
            price = inp_price.value()
            
            if not code or not name:
                QMessageBox.warning(self, "Campos Requeridos", 
                                   "Código y nombre son obligatorios")
                return None
                
            if price <= 0:
                QMessageBox.warning(self, "Precio Inválido", 
                                   "El precio debe ser mayor a 0")
                return None
                
            return code, name, price
        return None

    def add_item(self):
        """✅ Agregar producto con validaciones"""
        data = self.show_dialog()
        if not data:
            return
            
        code, name, price = data
        
        # Verificar código duplicado
        if session.query(BulkProduct).filter_by(code=code).first():
            QMessageBox.warning(self, "Código Duplicado", 
                               f"Ya existe un producto a granel con el código '{code}'")
            return
        
        try:
            # Crear producto
            session.add(BulkProduct(code=code, name=name, price=price))
            session.commit()
            
            QMessageBox.information(self, "Producto Creado", 
                                   f"✅ Producto a granel creado correctamente\n\n" +
                                   f"⚖️ Código: {code}\n" +
                                   f"🏷️ Nombre: {name}\n" +
                                   f"💰 Precio: ₡{int(price):,}/kg")
            self.load()
            
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Error creando producto: {str(e)}")

    def edit_item(self):
        """✅ Editar producto con validaciones"""
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.information(self, "Seleccionar Producto", 
                                   "Seleccione un producto de la lista para editar")
            return
            
        code = self.table.item(r, 0).text()
        prod = session.query(BulkProduct).filter_by(code=code).first()
        
        if not prod:
            QMessageBox.warning(self, "Producto No Encontrado", 
                               "El producto seleccionado no existe en la base de datos")
            self.load()
            return
        
        data = self.show_dialog(prod)
        if not data:
            return
            
        new_code, name, price = data
        
        # Verificar código duplicado (solo si cambió)
        if new_code != prod.code and session.query(BulkProduct).filter_by(code=new_code).first():
            QMessageBox.warning(self, "Código Duplicado", 
                               f"Ya existe otro producto con el código '{new_code}'")
            return
        
        try:
            # Actualizar producto
            old_name = prod.name
            prod.code = new_code
            prod.name = name
            prod.price = price
            session.commit()
            
            QMessageBox.information(self, "Producto Actualizado", 
                                   f"✅ Producto actualizado correctamente\n\n" +
                                   f"⚖️ Código: {new_code}\n" +
                                   f"🏷️ Nombre: {old_name} → {name}\n" +
                                   f"💰 Precio: ₡{int(price):,}/kg")
            self.load()
            
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Error actualizando producto: {str(e)}")

    def delete_item(self):
        """✅ Eliminar producto con confirmación robusta"""
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.information(self, "Seleccionar Producto", 
                                   "Seleccione un producto de la lista para eliminar")
            return
            
        code = self.table.item(r, 0).text()
        name = self.table.item(r, 1).text()
        price = self.table.item(r, 2).text()
        
        reply = QMessageBox.question(
            self, "Confirmar Eliminación", 
            f"¿Eliminar este producto a granel?\n\n" +
            f"⚖️ Código: {code}\n" +
            f"🏷️ Nombre: {name}\n" +
            f"💰 Precio: {price}\n\n" +
            "⚠️ Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            prod = session.query(BulkProduct).filter_by(code=code).first()
            if prod:
                product_info = f"{prod.name} ({prod.code})"
                session.delete(prod)
                session.commit()
                
                QMessageBox.information(self, "Producto Eliminado", 
                                       f"✅ Producto eliminado correctamente\n\n{product_info}")
                self.load()
                print(f"✅ Producto a granel eliminado: {product_info}")
            else:
                QMessageBox.warning(self, "Producto No Encontrado", 
                                   "El producto no se encontró en la base de datos")
                self.load()
                
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Error eliminando producto: {str(e)}")

    def eventFilter(self, obj, event):
        """✅ Manejo de eventos del teclado"""
        if (obj is self.table and event.type() == QEvent.KeyPress and 
            event.key() == Qt.Key_Delete):
            self.delete_item()
            return True
        return super().eventFilter(obj, event)