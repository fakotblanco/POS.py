# tabs/factura.py - VERSIÓN COMPLETA CORREGIDA CON ELIMINACIÓN POR SELECCIÓN
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QCompleter, QMessageBox, QLabel
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QEvent, Signal, QTimer, QStringListModel
from db import session
from database_setup import Sale, SaleItem, Product, BulkProduct
from datetime import date

class FacturaTab(QWidget):
    saleDone = Signal(float, float, float, float)

    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())

        # 🆕 INDICADOR DE CLIENTE SIMPLE Y CLARO
        self.client_indicator = QLabel()
        self.client_indicator.setAlignment(Qt.AlignCenter)
        self.client_indicator.setStyleSheet(
            """
            QLabel {
                background-color: #2196F3; 
                color: white; 
                padding: 10px; 
                font-size: 16px; 
                font-weight: bold; 
                border-radius: 6px; 
                margin: 5px;
            }
            """
        )
        self.layout().addWidget(self.client_indicator)

        # Fila de entrada limpia
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        # Barra de búsqueda clara
        self.input_code = QLineEdit()
        self.input_code.setPlaceholderText("Código, nombre o monto (5-20000) - También productos A GRANEL")
        self.input_code.setStyleSheet(
            """
            QLineEdit {
                min-height: 40px; 
                font-size: 16px; 
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
        # Configurar autocompleter y popup
        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        popup_font = QFont(); popup_font.setPointSize(14)
        popup = self.completer.popup()
        popup.setFont(popup_font)
        popup.setMinimumHeight(150)
        popup.setMinimumWidth(300)
        self.completer.setMaxVisibleItems(10)
        self.input_code.setCompleter(self.completer)
        self.input_code.textChanged.connect(self.update_completer)

        # Botón Añadir simple
        self.btn_add = QPushButton("Añadir")
        self.btn_add.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white; 
                padding: 10px 20px; 
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            """
        )

        input_layout.addWidget(self.input_code, 4)
        input_layout.addWidget(self.btn_add, 1)
        self.layout().addLayout(input_layout)

        # Tabla limpia y clara con selección temporal
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID","Producto","Precio","Cantidad","Total"])
        self.table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.table.setAlternatingRowColors(True)
        # 🆕 SELECCIÓN TEMPORAL: Solo cuando se necesita
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # Estilo minimalista SIN resaltado de selección
        self.table.setStyleSheet(
            """
            QTableWidget {
                background-color: white;
                alternate-background-color: #F8F9FA;
                gridline-color: #DEE2E6;
                border: 1px solid #DEE2E6;
                font-size: 16px;
                color: #212529;
            }
            QHeaderView::section {
                background-color: #495057;
                color: white;
                padding: 12px 8px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-right: 1px solid #6C757D;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #E9ECEF;
            }
            QTableWidget::item:selected {
                background-color: #F8F9FA;
                color: #212529;
                border: none;
            }
            """
        )
        table_font = QFont(); table_font.setPointSize(24)
        self.table.setFont(table_font)
        self.table_font = table_font
        self.table.verticalHeader().setDefaultSectionSize(table_font.pointSize() * 2)
        
        # 🆕 INSTALAR EVENT FILTER EN LA TABLA PARA BACKSPACE
        self.table.installEventFilter(self)
        
        # 🆕 CONECTAR PARA LIMPIAR SELECCIÓN CUANDO SE HACE CLIC EN BARRA DE BÚSQUEDA
        self.input_code.focusInEvent = self.on_search_focus
        
        # Conectar manejo de cambios en precio o cantidad
        self.table.cellChanged.connect(self._on_cell_changed)
        self.input_code.installEventFilter(self)  # ✅ Solo en barra de búsqueda
        self.layout().addWidget(self.table)
        # Aumentar ancho de columna Nombre al triple
        self.table.setColumnWidth(1, self.table.width() * 3 // 5)

        # 🎨 BARRA DE TOTAL Y BOTONES MODERNA
        total_layout = QHBoxLayout()
        total_layout.setSpacing(15)
        
        # Display de total con diseño premium
        self.display_total = QLineEdit("₡0")
        font2 = QFont(); font2.setPointSize(36); font2.setBold(True)
        self.display_total.setFont(font2)
        self.display_total.setReadOnly(True)
        self.display_total.setStyleSheet(
            """
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #E3F2FD, stop:1 #BBDEFB);
                color: #0D47A1;
                padding: 15px 20px;
                font-weight: bold;
                border: 3px solid #2196F3;
                border-radius: 15px;
                text-align: center;
            }
            """
        )
        
        # Botón Confirmar con gradiente verde
        self.btn_confirm = QPushButton("✅ Confirmar Venta")
        self.btn_confirm.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4CAF50, stop:1 #2E7D32);
                color: white;
                padding: 15px 25px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
                min-width: 150px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #66BB6A, stop:1 #4CAF50);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2E7D32, stop:1 #1B5E20);
            }
            """
        )
        
        # Botón Cancelar con gradiente rojo
        self.btn_cancel = QPushButton("❌ Cancelar")
        self.btn_cancel.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #F44336, stop:1 #D32F2F);
                color: white;
                padding: 15px 25px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #EF5350, stop:1 #F44336);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #D32F2F, stop:1 #B71C1C);
            }
            """
        )
        
        total_layout.addWidget(self.display_total, 3)  # Más espacio para el total
        total_layout.addWidget(self.btn_confirm, 1)
        total_layout.addWidget(self.btn_cancel, 1)
        self.layout().addLayout(total_layout)

        # Conexiones
        self.btn_add.clicked.connect(self.add_line)
        self.input_code.returnPressed.connect(self.on_enter_pressed)  # 🆕 Cambio aquí
        self.btn_confirm.clicked.connect(self.finish_sale)
        self.btn_cancel.clicked.connect(self.clear)
        self.clear()  # inicializar focus
        
        # ✅ AHORA SÍ actualizar indicador (después de que todo esté creado)
        self.update_client_indicator()

    def on_search_focus(self, event):
        """🆕 LIMPIAR SELECCIÓN CUANDO SE HACE CLIC EN LA BARRA DE BÚSQUEDA"""
        self.table.clearSelection()
        # Llamar al evento original
        QLineEdit.focusInEvent(self.input_code, event)

    def update_client_indicator(self):
        """🆕 ACTUALIZAR INDICADOR DE CLIENTE SIMPLE"""
        client_name = self.objectName() or "Cliente"
        item_count = self.table.rowCount()
        
        if item_count > 0:
            total_text = self.display_total.text()
            self.client_indicator.setText(f"🛒 {client_name} - {item_count} artículos - {total_text}")
            self.client_indicator.setStyleSheet(
                """
                QLabel {
                    background-color: #28A745; 
                    color: white; 
                    padding: 10px; 
                    font-size: 16px; 
                    font-weight: bold; 
                    border-radius: 6px; 
                    margin: 5px;
                }
                """
            )
        else:
            self.client_indicator.setText(f"🛒 {client_name} - Factura vacía")
            self.client_indicator.setStyleSheet(
                """
                QLabel {
                    background-color: #2196F3; 
                    color: white; 
                    padding: 10px; 
                    font-size: 16px; 
                    font-weight: bold; 
                    border-radius: 6px; 
                    margin: 5px;
                }
                """
            )

    def update_completer(self, text):
        if not any(c.isalpha() for c in text):
            self.completer_model.setStringList([])
            return
        if not text:
            self.completer_model.setStringList([])
            return
        
        suggestions = []
        
        # 🔥 PRIORIDAD 1: Códigos exactos primero
        exact_products = session.query(Product).filter(Product.code.ilike(text)).limit(2).all()
        for p in exact_products:
            suggestions.append(f"{p.code} - {p.name}")
        
        exact_bulk = session.query(BulkProduct).filter(BulkProduct.code.ilike(text)).limit(2).all()
        for p in exact_bulk:
            suggestions.append(f"{p.code} - {p.name} (A GRANEL)")
        
        # 🔥 PRIORIDAD 2: Códigos parciales
        pattern = f"{text}%"  # Solo que empiecen con el texto
        partial_products = (
            session.query(Product)
            .filter(Product.code.ilike(pattern))
            .filter(~Product.code.ilike(text))  # Excluir exactos ya agregados
            .limit(3)
            .all()
        )
        for p in partial_products:
            suggestions.append(f"{p.code} - {p.name}")
        
        partial_bulk = (
            session.query(BulkProduct)
            .filter(BulkProduct.code.ilike(pattern))
            .filter(~BulkProduct.code.ilike(text))  # Excluir exactos ya agregados
            .limit(3)
            .all()
        )
        for p in partial_bulk:
            suggestions.append(f"{p.code} - {p.name} (A GRANEL)")
        
        # 🔥 PRIORIDAD 3: Nombres (solo si hay espacio)
        if len(suggestions) < 8:
            pattern = f"%{text}%"
            name_products = (
                session.query(Product)
                .filter(Product.name.ilike(pattern))
                .limit(2)
                .all()
            )
            for p in name_products:
                if f"{p.code} - {p.name}" not in suggestions:
                    suggestions.append(f"{p.code} - {p.name}")
        
        self.completer_model.setStringList(suggestions[:10])  # Máximo 10 sugerencias

    def on_enter_pressed(self):
        """🆕 FUNCIÓN NUEVA: Manejar Enter inteligentemente"""
        text = self.input_code.text().strip()
        
        if text:
            # Si hay texto, agregar línea
            self.add_line()
        else:
            # Si está vacío, confirmar venta
            self.finish_sale()

    def eventFilter(self, obj, event):
        """✅ EVENT FILTER MEJORADO: Backspace inteligente + Eliminación por selección"""
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Backspace:
            if obj is self.input_code:
                # 🆕 BACKSPACE EN BARRA DE BÚSQUEDA
                if not self.input_code.text().strip():  # Si la barra está vacía
                    return self.smart_backspace()  # Eliminar último producto
                # Si hay texto, dejar que funcione normalmente
                return False
            elif obj is self.table:
                # 🆕 BACKSPACE EN LA TABLA - ELIMINAR FILA SELECCIONADA
                return self.delete_selected_row()
        return super().eventFilter(obj, event)

    def delete_selected_row(self):
        """🆕 ELIMINAR FILA SELECCIONADA EN LA TABLA"""
        current_row = self.table.currentRow()
        
        if current_row < 0 or current_row >= self.table.rowCount():
            # No hay fila seleccionada o fila inválida
            return True
        
        # Obtener nombre del producto para feedback
        product_name = self.table.item(current_row, 1).text() if self.table.item(current_row, 1) else "Producto"
        
        # Eliminar la fila seleccionada
        self.table.removeRow(current_row)
        self._update_total()
        self.update_client_indicator()
        
        # Feedback visual opcional
        print(f"🗑️ Eliminado (selección): {product_name}")
        
        # 🆕 LIMPIAR SELECCIÓN Y DEVOLVER FOCO A BARRA DE BÚSQUEDA
        self.table.clearSelection()
        self.input_code.setFocus()
        
        return True  # Consumir el evento

    def smart_backspace(self):
        """🆕 BACKSPACE INTELIGENTE: Eliminar último producto agregado"""
        row_count = self.table.rowCount()
        
        if row_count == 0:
            # No hay productos, no hacer nada
            return True
        
        # Eliminar la última fila (último producto agregado)
        last_row = row_count - 1
        product_name = self.table.item(last_row, 1).text() if self.table.item(last_row, 1) else "Producto"
        
        # Eliminar silenciosamente sin confirmación (para rapidez)
        self.table.removeRow(last_row)
        self._update_total()
        self.update_client_indicator()
        
        # Feedback visual opcional (puedes comentar esta línea si quieres que sea completamente silencioso)
        print(f"🗑️ Eliminado (último): {product_name}")
        
        return True  # Consumir el evento

    def add_line(self):
        text = self.input_code.text().strip()
        if not text:
            return
        
        # Limpiar texto si viene del completer
        if ' - ' in text:
            text = text.split(' - ', 1)[0]
        
        # 🆕 VARIABLES PARA MANEJAR PRODUCTOS A GRANEL
        prod = None
        bulk_prod = None
        price = None
        is_bulk = False
        
        # 🆕 BÚSQUEDA MEJORADA CON PRIORIDAD
        if text.isdigit():
            # Buscar por código exacto numérico
            prod = session.query(Product).filter_by(code=text).first()
            if not prod:
                val = int(text)
                if 5 <= val <= 20000 and val % 5 == 0:
                    price = val
        else:
            # 🔥 PRIORIDAD 1: Código exacto en productos normales
            prod = session.query(Product).filter(Product.code.ilike(text)).first()
            
            # 🔥 PRIORIDAD 2: Código exacto en productos a granel
            if not prod:
                bulk_prod = session.query(BulkProduct).filter(BulkProduct.code.ilike(text)).first()
                if bulk_prod:
                    is_bulk = True
            
            # 🔥 PRIORIDAD 3: Código parcial en productos normales
            if not prod and not bulk_prod:
                pattern = f"%{text}%"
                prod = session.query(Product).filter(Product.code.ilike(pattern)).first()
            
            # 🔥 PRIORIDAD 4: Código parcial en productos a granel
            if not prod and not bulk_prod:
                pattern = f"%{text}%"
                bulk_prod = session.query(BulkProduct).filter(BulkProduct.code.ilike(pattern)).first()
                if bulk_prod:
                    is_bulk = True
            
            # 🔥 PRIORIDAD 5: Nombre en productos normales (solo si no hay coincidencias de código)
            if not prod and not bulk_prod:
                pattern = f"%{text}%"
                prod = session.query(Product).filter(Product.name.ilike(pattern)).first()
            
            # 🔥 PRIORIDAD 6: Nombre en productos a granel (último recurso)
            if not prod and not bulk_prod:
                pattern = f"%{text}%"
                bulk_prod = session.query(BulkProduct).filter(BulkProduct.name.ilike(pattern)).first()
                if bulk_prod:
                    is_bulk = True
        
        # 🆕 DETERMINAR DATOS DE FILA
        if prod:
            # Producto normal
            code, name, price = prod.code, prod.name, int(prod.price)
            qty = 1
        elif bulk_prod:
            # 🆕 PRODUCTO A GRANEL
            code, name, price = bulk_prod.code, f"{bulk_prod.name} (kg)", int(bulk_prod.price)
            qty = 1  # Por defecto 1kg, el usuario puede cambiar a 0.5, 2.3, etc.
            is_bulk = True
        elif price is not None:
            # Monto directo
            code, name, qty = '', 'Monto', 1
        else:
            # Producto no reconocido
            code, name, price, qty = text, 'Producto no reconocido', 0, 1
        
        total = qty * (price or 0)
        
        # 🆕 INSERTAR FILA CON FORMATO CORRECTO
        r = self.table.rowCount()
        self.table.insertRow(r)
        for i, v in enumerate([code, name, str(price or 0), str(qty), f"₡{total:,}"]):
            item = QTableWidgetItem(v)
            item.setFont(self.table_font)  # ✅ FUENTE CORRECTA DESDE EL INICIO
            
            # Alineación correcta por columna
            if i == 2:  # Precio
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            elif i == 3:  # Cantidad
                item.setTextAlignment(Qt.AlignCenter)
            elif i == 4:  # Total
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # ✅ PERMITIR EDITAR CANTIDAD EN PRODUCTOS A GRANEL
            if i == 3 and is_bulk:  # Columna cantidad para productos a granel
                item.setFlags(item.flags() | Qt.ItemIsEditable)
            elif i in (1,2,3):  # Permitir editar nombre, precio y cantidad en productos no reconocidos
                item.setFlags(item.flags() | Qt.ItemIsEditable)
            
            self.table.setItem(r, i, item)
        
        self._update_total()
        self.input_code.clear()
        self.input_code.setFocus()
        self.update_client_indicator()  # 🆕 Actualizar indicador

    def round_to_5_or_0(self, amount):
        """🆕 REDONDEO INTELIGENTE: +50 colones y redondear hacia arriba a 5 o 0"""
        # Agregar 50 colones extra
        amount += 50
        
        # Obtener el último dígito
        last_digit = int(amount) % 10
        
        # Redondear hacia arriba al próximo 5 o 0
        if last_digit == 0 or last_digit == 5:
            # Ya termina en 5 o 0, no cambiar
            return int(amount)
        elif last_digit < 5:
            # Redondear al próximo 5
            return int(amount) + (5 - last_digit)
        else:  # last_digit > 5
            # Redondear al próximo 0
            return int(amount) + (10 - last_digit)

    def _on_cell_changed(self, row, col):
        # Si cambia precio(2) o cantidad(3), recalcular total fila
        if col not in (2,3):
            return
        try:
            price = float(self.table.item(row, 2).text())
            qty = float(self.table.item(row, 3).text())
        except (ValueError, AttributeError):
            return
        
        # Calcular total
        total = qty * price
        
        # 🆕 DETECTAR SI ES PRODUCTO A GRANEL (cantidad decimal)
        is_bulk = (qty != int(qty))  # Si la cantidad no es entera, es a granel
        
        if is_bulk:
            # 🆕 APLICAR REDONDEO INTELIGENTE PARA PRODUCTOS A GRANEL
            total = self.round_to_5_or_0(total)
            print(f"🔄 Producto a granel: {qty}kg × ₡{price} = ₡{total} (redondeado)")
        else:
            # Productos normales sin redondeo
            total = int(total)
        
        self.table.blockSignals(True)
        # ✅ CREAR ITEM CON FUENTE CORRECTA Y FORMATO
        total_item = QTableWidgetItem(f"₡{total:,}")
        total_item.setFont(self.table_font)  # 🎯 APLICAR FUENTE CORRECTA
        total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)  # Alineación a la derecha
        self.table.setItem(row, 4, total_item)
        self.table.blockSignals(False)
        self._update_total()

    def _update_total(self):
        """✅ FUNCIÓN ARREGLADA: Suma correcta del total"""
        total_sum = 0
        
        for r in range(self.table.rowCount()):
            try:
                # Obtener el texto de la columna total (columna 4)
                total_text = self.table.item(r, 4).text()
                
                # Limpiar el texto: quitar ₡, comas y espacios
                clean_text = total_text.replace('₡', '').replace(',', '').strip()
                
                # Convertir a número y sumar
                total_sum += float(clean_text)
                
            except (ValueError, AttributeError, TypeError):
                # Si hay error en alguna fila, continuar con la siguiente
                print(f"⚠️ Error procesando fila {r}: {total_text if 'total_text' in locals() else 'N/A'}")
                continue
        
        # Actualizar display del total
        self.display_total.setText(f"₡{int(total_sum):,}")
        self.update_client_indicator()  # Actualizar indicador cuando cambie el total
        
        print(f"💰 Total calculado: ₡{int(total_sum):,}")  # Debug

    def finish_sale(self):
        if self.table.rowCount() == 0:
            return
        
        sale = Sale(date=date.today())
        session.add(sale)
        total_ventas = 0.0
        
        for r in range(self.table.rowCount()):
            code = self.table.item(r, 0).text()
            price = float(self.table.item(r, 2).text())
            qty = float(self.table.item(r, 3).text())  # 🆕 Permitir decimales para productos a granel
            
            # 🆕 BUSCAR EN PRODUCTOS NORMALES Y A GRANEL
            prod = session.query(Product).filter_by(code=code).first() if code else None
            bulk_prod = session.query(BulkProduct).filter_by(code=code).first() if code and not prod else None
            
            # Determinar product_id para SaleItem
            if prod:
                pid = prod.id
                # Descontar stock solo para productos normales
                prod.stock -= int(qty)  # Stock siempre en enteros
            elif bulk_prod:
                # 🆕 PARA PRODUCTOS A GRANEL, NO HAY product_id NI DESCUENTO DE STOCK
                pid = None  # Los productos a granel no tienen stock
            else:
                pid = None
            
            session.add(SaleItem(sale=sale, product_id=pid, quantity=qty, price=price))
            total_ventas += qty * price
        
        session.commit()
        self.saleDone.emit(total_ventas, 0.0, 0.0, total_ventas)

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Venta")
        msg.setText("Registrada con éxito")
        msg.setStandardButtons(QMessageBox.NoButton)
        msg.show()
        QTimer.singleShot(1000, msg.accept)

        self.clear()

    def clear(self):
        self.table.setRowCount(0)
        self.display_total.setText("₡0")
        self.input_code.setFocus()
        self.update_client_indicator()  # 🆕 Actualizar indicador al limpiar