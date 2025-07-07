# tabs/entradas.py - VERSIÓN CORREGIDA COMPLETA
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget,
    QTableWidgetItem, QPushButton, QMessageBox, QLabel,
    QAbstractItemView, QHeaderView, QCompleter, QComboBox
)
from PySide6.QtCore import Qt, QEvent, QStringListModel
from PySide6.QtGui import QFont, QColor
from db import session
from database_setup import Product, Entry, Provider
from datetime import date

class EntradasTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())

        # ========== CONTROLES SUPERIORES CON DISEÑO CONSISTENTE ==========
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # Selector de proveedor con estilo consistente
        controls_layout.addWidget(QLabel("🏪 Proveedor:"))
        self.combo_provider = QComboBox()
        self.combo_provider.setStyleSheet(
            """
            QComboBox {
                min-height: 35px; 
                font-size: 14px; 
                background-color: #FAFAFA;
                padding: 8px 12px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                color: #333;
                min-width: 200px;
            }
            QComboBox:focus {
                border: 2px solid #2196F3;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
            }
            """
        )
        self.load_providers()
        controls_layout.addWidget(self.combo_provider, 2)
        
        # Input de código/nombre con estilo consistente
        controls_layout.addWidget(QLabel("🔍 Agregar:"))
        self.input_code = QLineEdit()
        self.input_code.setPlaceholderText("Código o nombre del producto")
        self.input_code.setStyleSheet(
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
        
        # Completer para código/nombre
        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.input_code.setCompleter(self.completer)
        self.input_code.textChanged.connect(self.update_completer)
        self.input_code.returnPressed.connect(self.add_line)
        controls_layout.addWidget(self.input_code, 3)
        
        controls_layout.addStretch()
        self.layout().addLayout(controls_layout)

        # ========== TABLA DE ENTRADAS CON DISEÑO CONSISTENTE ==========
        entry_title = QLabel("📦 Productos a Ingresar")
        entry_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin: 10px 0;")
        self.layout().addWidget(entry_title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Código", "Nombre", "Stock Actual", "Cantidad", "Precio", "Proveedor"
        ])
        
        # Configuración de columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Código
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Nombre se expande
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Stock
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Cantidad
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Precio
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Proveedor
        
        # Estilo consistente con inventario
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
                background-color: #495057;
                color: white;
                padding: 12px 8px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-right: 1px solid #6C757D;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #E9ECEF;
            }
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
            """
        )

        # Configuración de edición
        self.table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )
        
        # Fuente optimizada
        table_font = QFont()
        table_font.setPointSize(14)
        self.table.setFont(table_font)
        self.table.verticalHeader().setDefaultSectionSize(40)
        
        self.table.installEventFilter(self)
        self.table.cellChanged.connect(self._on_cell_changed)
        self.layout().addWidget(self.table)

        # ========== BOTONES CON DISEÑO CONSISTENTE ==========
        btns = QHBoxLayout()
        btns.setSpacing(8)
        
        # Botón confirmar (verde)
        self.btn_confirm = QPushButton("✅ Confirmar Entradas")
        self.btn_confirm.setStyleSheet(
            """
            QPushButton {
                background-color: #28A745;
                color: white;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1E7E34;
            }
            """
        )
        
        # Botón cancelar (rojo)
        self.btn_cancel = QPushButton("❌ Cancelar")
        self.btn_cancel.setStyleSheet(
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
        
        btns.addWidget(self.btn_confirm)
        btns.addWidget(self.btn_cancel)
        btns.addStretch()
        self.layout().addLayout(btns)

        # ========== HISTORIAL CON DISEÑO CONSISTENTE ==========
        history_title = QLabel("📋 Historial de Entradas")
        history_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin: 20px 0 10px 0;")
        self.layout().addWidget(history_title)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Fecha", "Código", "Producto", "Cantidad", "Proveedor"
        ])
        
        # Configuración de columnas del historial
        history_header = self.history_table.horizontalHeader()
        history_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Fecha
        history_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Código
        history_header.setSectionResizeMode(2, QHeaderView.Stretch)           # Producto se expande
        history_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Cantidad
        history_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Proveedor
        
        # Estilo consistente - solo lectura
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setStyleSheet(
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
                background-color: #6C757D;
                color: white;
                padding: 12px 8px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-right: 1px solid #ADB5BD;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #E9ECEF;
            }
            """
        )
        
        self.history_table.setFont(table_font)
        self.history_table.verticalHeader().setDefaultSectionSize(35)
        self.layout().addWidget(self.history_table)

        # ========== CONEXIONES ==========
        self.btn_confirm.clicked.connect(self.finish)
        self.btn_cancel.clicked.connect(self.clear)

        # Carga inicial
        self.load_history()

    def load_providers(self):
        """✅ CARGAR PROVEEDORES - MANEJA SI NO HAY NINGUNO"""
        self.combo_provider.clear()
        
        try:
            providers = session.query(Provider).order_by(Provider.name).all()
            
            if not providers:
                # Si no hay proveedores, permitir continuar sin uno
                self.combo_provider.addItem("🚫 Sin proveedor (crear uno en Proveedores)", None)
            else:
                self.combo_provider.addItem("📋 Seleccionar proveedor...", None)
                for prov in providers:
                    self.combo_provider.addItem(f"🏪 {prov.name}", prov.id)
                    
        except Exception as e:
            # Si hay error, permitir continuar
            self.combo_provider.addItem("⚠️ Error - Continuar sin proveedor", None)

    def update_completer(self, text):
        """✅ ACTUALIZAR AUTOCOMPLETADO"""
        if not text:
            self.completer_model.setStringList([])
            return
            
        try:
            pattern = f"%{text}%"
            prods = (
                session.query(Product)
                .filter(
                    (Product.code.ilike(pattern)) | (Product.name.ilike(pattern))
                )
                .limit(10)
                .all()
            )
            suggestions = [f"{p.code} - {p.name}" for p in prods]
            self.completer_model.setStringList(suggestions)
        except Exception as e:
            print(f"Error en autocompletado: {e}")
            self.completer_model.setStringList([])

    def add_line(self):
        """✅ AGREGAR LÍNEA - VERSIÓN CORREGIDA COMPLETAMENTE"""
        text = self.input_code.text().strip()
        if not text:
            return
        
        # Parsear el código del input
        if ' - ' in text:
            code = text.split(' - ', 1)[0].strip()
        else:
            code = text.strip()
            
        # Buscar producto en la base de datos
        try:
            prod = session.query(Product).filter_by(code=code).first()
            if not prod:
                QMessageBox.warning(self, "Producto No Encontrado", 
                                   f"No se encontró un producto con código: '{code}'")
                self.input_code.clear()
                return
        except Exception as e:
            QMessageBox.critical(self, "Error de Base de Datos", 
                                f"Error al buscar producto: {str(e)}")
            return
        
        # Verificar si ya está en la tabla
        for r in range(self.table.rowCount()):
            existing_item = self.table.item(r, 0)
            if existing_item and existing_item.text() == code:
                QMessageBox.information(self, "Producto Duplicado", 
                                       f"El producto '{code}' ya está en la lista de entradas.")
                self.input_code.clear()
                return
        
        # Obtener proveedor seleccionado
        provider_id = self.combo_provider.currentData()
        provider_text = self.combo_provider.currentText()
        
        # Limpiar el texto del proveedor
        provider_name = "Sin proveedor"
        if provider_text and not provider_text.startswith("📋"):
            provider_name = (provider_text
                           .replace("🏪 ", "")
                           .replace("🚫 ", "")
                           .replace("⚠️ ", "")
                           .strip())
        
        # Asignar proveedor al producto si no lo tiene y hay uno seleccionado
        try:
            if not prod.provider_id and provider_id:
                prod.provider_id = provider_id
                session.commit()
                print(f"✅ Proveedor asignado a {code}: {provider_name}")
        except Exception as e:
            print(f"⚠️ No se pudo asignar proveedor: {e}")
        
        # ===== PASO CRÍTICO: INSERTAR FILA ANTES DE CREAR ITEMS =====
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)
        
        # Crear todos los items con manejo de errores
        try:
            # Columna 0: Código (solo lectura)
            code_item = QTableWidgetItem(str(prod.code))
            code_item.setFlags(code_item.flags() & ~Qt.ItemIsEditable)
            
            # Columna 1: Nombre (editable)
            name_item = QTableWidgetItem(str(prod.name))
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            
            # Columna 2: Stock actual (solo lectura)
            stock_item = QTableWidgetItem(f"{int(prod.stock):,}")
            stock_item.setFlags(stock_item.flags() & ~Qt.ItemIsEditable)
            
            # Columna 3: Cantidad (editable, por defecto 1)
            qty_item = QTableWidgetItem("1")
            qty_item.setFlags(qty_item.flags() | Qt.ItemIsEditable)
            qty_item.setBackground(QColor(232, 245, 232))  # Verde claro para indicar que es editable
            
            # Columna 4: Precio (editable)
            price_item = QTableWidgetItem(f"₡{int(prod.price):,}")
            price_item.setFlags(price_item.flags() | Qt.ItemIsEditable)
            
            # Columna 5: Proveedor (solo lectura)
            provider_item = QTableWidgetItem(provider_name)
            provider_item.setFlags(provider_item.flags() & ~Qt.ItemIsEditable)
            
            # INSERTAR TODOS LOS ITEMS EN LA TABLA
            self.table.setItem(row_index, 0, code_item)
            self.table.setItem(row_index, 1, name_item)
            self.table.setItem(row_index, 2, stock_item)
            self.table.setItem(row_index, 3, qty_item)
            self.table.setItem(row_index, 4, price_item)
            self.table.setItem(row_index, 5, provider_item)
            
            # ✅ CONFIRMAR QUE SE INSERTÓ CORRECTAMENTE
            print(f"✅ Producto agregado: {code} - {prod.name} (Fila {row_index})")
            
            # Limpiar input y mantener foco
            self.input_code.clear()
            self.input_code.setFocus()
            
            # Seleccionar la celda de cantidad para edición rápida
            self.table.setCurrentCell(row_index, 3)
            
        except Exception as e:
            # Si hay error creando los items, eliminar la fila vacía
            print(f"❌ Error creando items: {e}")
            self.table.removeRow(row_index)
            QMessageBox.critical(self, "Error", 
                                f"Error al agregar producto a la tabla: {str(e)}")

    def _on_cell_changed(self, row, col):
        """✅ MEJORADO: Maneja cambios en NOMBRE (col 1), CANTIDAD (col 3) y PRECIO (col 4)"""
        if col not in (1, 3, 4):  # Solo columnas editables
            return
            
        item = self.table.item(row, col)
        if not item:
            return
            
        code_item = self.table.item(row, 0)
        if not code_item:
            return
            
        code = code_item.text()
        
        try:
            prod = session.query(Product).filter_by(code=code).first()
            if not prod:
                return
                
            if col == 1:  # ✅ CAMBIO DE NOMBRE
                new_name = item.text().strip()
                if new_name:
                    prod.name = new_name
                    session.commit()
                    print(f"✅ Nombre actualizado: {code} -> {new_name}")
                    
            elif col == 3:  # ✅ VALIDAR CANTIDAD
                qty_text = item.text().strip()
                if qty_text:
                    qty = int(qty_text)
                    if qty <= 0:
                        item.setText("1")
                        QMessageBox.warning(self, "Cantidad Inválida", 
                                           "La cantidad debe ser mayor a 0")
                    
            elif col == 4:  # ✅ CAMBIO DE PRECIO
                price_text = item.text().replace("₡", "").replace(",", "").strip()
                new_price = float(price_text)
                if new_price < 0:
                    item.setText(f"₡{int(prod.price):,}")
                    QMessageBox.warning(self, "Precio Inválido", 
                                       "El precio no puede ser negativo")
                    return
                    
                prod.price = new_price
                session.commit()
                item.setText(f"₡{int(new_price):,}")  # Formatear correctamente
                print(f"✅ Precio actualizado: {code} -> ₡{new_price:,.0f}")
                
        except ValueError as e:
            # Si hay error en cantidad o precio, revertir
            if col == 3:
                item.setText("1")
            elif col == 4:
                item.setText(f"₡{int(prod.price):,}")
            QMessageBox.warning(self, "Valor Inválido", 
                               "Por favor ingrese un número válido")
            return
        except Exception as e:
            print(f"❌ Error actualizando producto: {e}")
            return
        
        # ✅ Actualizar inventario en tiempo real
        self.update_inventory_tab()

    def update_inventory_tab(self):
        """✅ Actualizar pestaña de inventario si existe"""
        try:
            parent = self.parentWidget()
            while parent and not hasattr(parent, 'widget'):
                parent = parent.parentWidget()
            if parent:
                # Buscar la pestaña de inventario (asumiendo que está en índice 0)
                inv_tab = parent.widget(0)
                if hasattr(inv_tab, 'load_optimized'):
                    inv_tab.load_optimized()
                elif hasattr(inv_tab, 'load'):
                    inv_tab.load()
        except Exception as e:
            print(f"⚠️ No se pudo actualizar inventario: {e}")

    def finish(self):
        """✅ CONFIRMAR - FUNCIONA CON O SIN PROVEEDORES"""
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "Sin Productos", 
                                   "No hay productos para procesar.")
            return
            
        provider_id = self.combo_provider.currentData()
        
        # ✅ PERMITIR CONTINUAR SIN PROVEEDOR (para compatibilidad)
        if not provider_id:
            result = QMessageBox.question(
                self, "Sin Proveedor", 
                "No has seleccionado un proveedor.\n\n¿Continuar de todas formas?",
                QMessageBox.Yes | QMessageBox.No
            )
            if result != QMessageBox.Yes:
                return
            
        entries_processed = 0
        total_quantity = 0
        
        try:
            for r in range(self.table.rowCount()):
                code_item = self.table.item(r, 0)
                qty_item = self.table.item(r, 3)
                
                if not code_item or not qty_item:
                    continue
                    
                code = code_item.text()
                
                try:
                    qty_text = qty_item.text().strip()
                    qty = int(qty_text) if qty_text else 0
                except (ValueError, AttributeError):
                    continue
                    
                if qty <= 0:
                    continue
                    
                prod = session.query(Product).filter_by(code=code).first()
                if prod:
                    # Actualizar stock
                    old_stock = prod.stock
                    prod.stock += qty
                    
                    # ✅ Crear entrada (con o sin proveedor)
                    entry = Entry(
                        provider_id=provider_id,  # Puede ser None
                        date=date.today(),
                        product_id=prod.id,
                        quantity=qty
                    )
                    session.add(entry)
                    
                    # ✅ Asignar proveedor al producto si no lo tiene Y hay uno seleccionado
                    if not prod.provider_id and provider_id:
                        prod.provider_id = provider_id
                    
                    entries_processed += 1
                    total_quantity += qty
                    print(f"✅ Stock actualizado: {code} {old_stock} → {prod.stock} (+{qty})")
                        
            session.commit()
            
            # Actualizar inventario
            self.update_inventory_tab()
                
            provider_name = self.combo_provider.currentText().replace("🏪 ", "").replace("📋 ", "")
            QMessageBox.information(self, "Entradas Procesadas", 
                                   f"✅ {entries_processed} productos actualizados\n" +
                                   f"📦 {total_quantity} unidades ingresadas\n" +
                                   f"🏪 Proveedor: {provider_name}")
            self.clear()
            self.load_history()
            
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", 
                                f"Error procesando entradas: {str(e)}")

    def clear(self):
        """✅ Limpiar tabla de entradas"""
        self.table.setRowCount(0)
        self.input_code.clear()
        self.input_code.setFocus()

    def load_history(self):
        """✅ HISTORIAL - MANEJA ERRORES GRACIOSAMENTE"""
        self.history_table.setRowCount(0)
        try:
            # Cargar las últimas 100 entradas para mejor rendimiento
            entries = (session.query(Entry)
                      .outerjoin(Provider)
                      .order_by(Entry.date.desc(), Entry.id.desc())
                      .limit(100)
                      .all())
            
            for e in entries:
                r = self.history_table.rowCount()
                self.history_table.insertRow(r)
                
                # Fecha
                date_item = QTableWidgetItem(e.date.strftime("%Y-%m-%d"))
                self.history_table.setItem(r, 0, date_item)
                
                # Código y nombre del producto
                if e.product:
                    code_item = QTableWidgetItem(e.product.code)
                    name_item = QTableWidgetItem(e.product.name)
                    self.history_table.setItem(r, 1, code_item)
                    self.history_table.setItem(r, 2, name_item)
                else:
                    self.history_table.setItem(r, 1, QTableWidgetItem("N/A"))
                    self.history_table.setItem(r, 2, QTableWidgetItem("Producto eliminado"))
                
                # Cantidad
                qty_item = QTableWidgetItem(f"{e.quantity:,}")
                self.history_table.setItem(r, 3, qty_item)
                
                # Proveedor
                provider_name = e.provider.name if e.provider else "Sin proveedor"
                provider_item = QTableWidgetItem(provider_name)
                self.history_table.setItem(r, 4, provider_item)
                
        except Exception as e:
            # Si hay error cargando historial, continuar sin mostrar error molesto
            print(f"❌ Error cargando historial: {e}")

    def eventFilter(self, obj, event):
        """✅ Manejo de eventos del teclado"""
        if (obj is self.table and event.type() == QEvent.KeyPress and 
            event.key() == Qt.Key_Delete):
            r = self.table.currentRow()
            if r >= 0:
                name_item = self.table.item(r, 1)
                product_name = name_item.text() if name_item else "Producto"
                reply = QMessageBox.question(
                    self, "Eliminar Producto", 
                    f"¿Eliminar '{product_name}' de la lista de entradas?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.table.removeRow(r)
            return True
        return super().eventFilter(obj, event)