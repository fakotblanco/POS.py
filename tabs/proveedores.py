# tabs/proveedores.py - VERSIÓN COMPLETA CORREGIDA
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QLineEdit, QDoubleSpinBox, QAbstractItemView, QFileDialog, QCompleter,
    QTabWidget, QHeaderView, QLabel, QSplitter
)
from PySide6.QtCore import Qt, QEvent, Signal, QTimer
from PySide6.QtGui import QFont
from db import session
from database_setup import Provider, Payment, Product
from datetime import datetime
import csv
import unicodedata
import re

class ProveedoresTab(QWidget):
    providerDone = Signal(float)

    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())

        # Timer para búsqueda con delay
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        # Timer para búsqueda de pagos con delay
        self.payments_search_timer = QTimer()
        self.payments_search_timer.setSingleShot(True)
        self.payments_search_timer.timeout.connect(self.perform_payments_search)

        # ========== PESTAÑAS CON DISEÑO CONSISTENTE ==========
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #DEE2E6;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #F8F9FA;
                color: #495057;
                padding: 12px 20px;
                margin-right: 2px;
                border: 1px solid #DEE2E6;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #2196F3;
                border-bottom: 2px solid #2196F3;
            }
            QTabBar::tab:hover:!selected {
                background-color: #E9ECEF;
                color: #495057;
            }
            """
        )
        
        # Pestaña 1: Gestión de Proveedores
        self.providers_tab = self.create_providers_tab()
        self.tabs.addTab(self.providers_tab, "🏪 Gestión de Proveedores")
        
        # Pestaña 2: Pagos a Proveedores
        self.payments_tab = self.create_payments_tab()
        self.tabs.addTab(self.payments_tab, "💰 Pagos a Proveedores")
        
        self.layout().addWidget(self.tabs)

    def create_providers_tab(self):
        """✅ PESTAÑA DE PROVEEDORES CON VISTA DETALLADA MEJORADA"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)

        # ========== BARRA DE BÚSQUEDA COMPACTA ==========
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        search_label = QLabel("🔍 Buscar:")
        search_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #495057;")
        search_layout.addWidget(search_label)

        self.search_provider = QLineEdit()
        self.search_provider.setPlaceholderText("Nombre del proveedor o contacto")
        self.search_provider.setStyleSheet(
            """
            QLineEdit {
                min-height: 30px; 
                font-size: 13px; 
                background-color: #FAFAFA;
                padding: 6px 10px;
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
                background-color: white;
            }
            """
        )
        self.search_provider.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_provider, 3)
        search_layout.addStretch()
        
        layout.addLayout(search_layout)

        # ========== SPLITTER PRINCIPAL ==========
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setStyleSheet("QSplitter::handle { background-color: #DEE2E6; }")

        # ========== PANEL IZQUIERDO: LISTA DE PROVEEDORES ==========
        providers_widget = QWidget()
        providers_layout = QVBoxLayout(providers_widget)
        providers_layout.setSpacing(8)

        providers_title = QLabel("📋 Proveedores")
        providers_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; margin: 2px 0;")
        providers_layout.addWidget(providers_title)

        self.providers_table = QTableWidget()
        self.providers_table.setColumnCount(3)
        self.providers_table.setHorizontalHeaderLabels(["Proveedor", "Contacto", "Productos"])
        
        # Configuración de columnas
        header = self.providers_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # Estilo consistente
        self.providers_table.setAlternatingRowColors(True)
        self.providers_table.setStyleSheet(
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
        
        self.providers_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.providers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.providers_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.providers_table.installEventFilter(self)
        
        # ✅ CONECTAR SELECCIÓN PARA MOSTRAR DETALLES
        self.providers_table.selectionModel().selectionChanged.connect(self.on_provider_selected)
        
        table_font = QFont()
        table_font.setPointSize(14)
        self.providers_table.setFont(table_font)
        self.providers_table.verticalHeader().setDefaultSectionSize(40)
        
        providers_layout.addWidget(self.providers_table)

        # Botones para proveedores
        prov_btn_layout = QHBoxLayout()
        prov_btn_layout.setSpacing(6)
        
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """
        
        self.btn_add_provider = QPushButton("➕ Agregar")
        self.btn_add_provider.setStyleSheet(button_style)
        
        self.btn_edit_provider = QPushButton("✏️ Editar")
        self.btn_edit_provider.setStyleSheet(button_style)
        
        self.btn_delete_provider = QPushButton("🗑️ Eliminar")
        self.btn_delete_provider.setStyleSheet(
            """
            QPushButton {
                background-color: #DC3545;
                color: white;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:pressed {
                background-color: #BD2130;
            }
            """
        )
        
        prov_btn_layout.addWidget(self.btn_add_provider)
        prov_btn_layout.addWidget(self.btn_edit_provider)
        prov_btn_layout.addWidget(self.btn_delete_provider)
        prov_btn_layout.addStretch()
        
        providers_layout.addLayout(prov_btn_layout)
        main_splitter.addWidget(providers_widget)

        # ========== PANEL DERECHO: DETALLES DEL PROVEEDOR ==========
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setSpacing(8)

        # Título dinámico
        self.details_title = QLabel("📝 Seleccione un proveedor para ver detalles")
        self.details_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #666; margin: 2px 0;")
        details_layout.addWidget(self.details_title)

        # ========== SUB-SPLITTER VERTICAL PARA PRODUCTOS Y PAGOS ==========
        details_splitter = QSplitter(Qt.Vertical)
        details_splitter.setStyleSheet("QSplitter::handle { background-color: #DEE2E6; }")

        # ========== SECCIÓN DE PRODUCTOS ==========
        products_widget = QWidget()
        products_layout = QVBoxLayout(products_widget)
        products_layout.setSpacing(6)

        products_header = QLabel("📦 Productos")
        products_header.setStyleSheet("font-size: 13px; font-weight: bold; color: #495057; margin: 2px 0;")
        products_layout.addWidget(products_header)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels(["Código", "Producto", "Precio", "Stock"])
        
        # Configuración de columnas para productos
        products_header_view = self.products_table.horizontalHeader()
        products_header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        products_header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        products_header_view.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        products_header_view.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setStyleSheet(
            """
            QTableWidget {
                background-color: white;
                alternate-background-color: #F8F9FA;
                gridline-color: #DEE2E6;
                border: 1px solid #DEE2E6;
                font-size: 13px;
                color: #212529;
            }
            QHeaderView::section {
                background-color: #6C757D;
                color: white;
                padding: 8px 6px;
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-right: 1px solid #ADB5BD;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #E9ECEF;
            }
            QTableWidget::item:selected {
                background-color: #E8DAEF;
                color: #6C3483;
            }
            """
        )
        
        self.products_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        products_font = QFont()
        products_font.setPointSize(12)
        self.products_table.setFont(products_font)
        self.products_table.verticalHeader().setDefaultSectionSize(32)
        
        products_layout.addWidget(self.products_table)
        details_splitter.addWidget(products_widget)

        # ========== SECCIÓN DE PAGOS AL PROVEEDOR ==========
        payments_widget = QWidget()
        payments_layout = QVBoxLayout(payments_widget)
        payments_layout.setSpacing(6)

        payments_header_layout = QHBoxLayout()
        payments_header_layout.setSpacing(8)
        
        payments_header = QLabel("💰 Pagos")
        payments_header.setStyleSheet("font-size: 13px; font-weight: bold; color: #495057; margin: 2px 0;")
        payments_header_layout.addWidget(payments_header)
        
        # Botón para agregar pago específico a este proveedor
        self.btn_add_provider_payment = QPushButton("➕ Pago")
        self.btn_add_provider_payment.setStyleSheet(
            """
            QPushButton {
                background-color: #28A745;
                color: white;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
                border: none;
                border-radius: 3px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #CCC;
                color: #999;
            }
            """
        )
        self.btn_add_provider_payment.setEnabled(False)  # Se habilita al seleccionar proveedor
        self.btn_add_provider_payment.clicked.connect(self.add_payment_to_selected_provider)
        payments_header_layout.addWidget(self.btn_add_provider_payment)
        payments_header_layout.addStretch()
        
        payments_layout.addLayout(payments_header_layout)

        self.provider_payments_table = QTableWidget()
        self.provider_payments_table.setColumnCount(2)
        self.provider_payments_table.setHorizontalHeaderLabels(["Fecha", "Monto"])
        
        # Configuración de columnas para pagos
        payments_header_view = self.provider_payments_table.horizontalHeader()
        payments_header_view.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        payments_header_view.setSectionResizeMode(1, QHeaderView.Stretch)
        
        self.provider_payments_table.setAlternatingRowColors(True)
        self.provider_payments_table.setStyleSheet(
            """
            QTableWidget {
                background-color: white;
                alternate-background-color: #F8F9FA;
                gridline-color: #DEE2E6;
                border: 1px solid #DEE2E6;
                font-size: 13px;
                color: #212529;
            }
            QHeaderView::section {
                background-color: #17A2B8;
                color: white;
                padding: 8px 6px;
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-right: 1px solid #138496;
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid #E9ECEF;
            }
            QTableWidget::item:selected {
                background-color: #D1ECF1;
                color: #0C5460;
            }
            """
        )
        
        self.provider_payments_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.provider_payments_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.provider_payments_table.setFont(products_font)
        self.provider_payments_table.verticalHeader().setDefaultSectionSize(32)
        
        payments_layout.addWidget(self.provider_payments_table)
        details_splitter.addWidget(payments_widget)

        # Configurar proporciones del splitter vertical (60% productos, 40% pagos)
        details_splitter.setSizes([300, 200])
        details_layout.addWidget(details_splitter)

        # Estadísticas del proveedor
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet(
            """
            QLabel {
                background-color: #F8F9FA;
                color: #495057;
                padding: 6px;
                border: 1px solid #DEE2E6;
                border-radius: 4px;
                font-size: 12px;
            }
            """
        )
        details_layout.addWidget(self.stats_label)

        main_splitter.addWidget(details_widget)
        
        # Configurar proporciones del splitter principal (35% proveedores, 65% detalles)
        main_splitter.setSizes([350, 650])
        layout.addWidget(main_splitter)

        # ========== CONEXIONES ==========
        self.btn_add_provider.clicked.connect(self.add_provider)
        self.btn_edit_provider.clicked.connect(self.edit_provider)
        self.btn_delete_provider.clicked.connect(self.delete_provider)

        # Cargar proveedores
        self.refresh_providers()
        
        return widget

    def on_search_changed(self, text):
        """✅ BÚSQUEDA CON DELAY"""
        self.search_timer.stop()
        if len(text) >= 2 or len(text) == 0:
            self.search_timer.start(300)

    def perform_search(self):
        """✅ EJECUTAR BÚSQUEDA DE PROVEEDORES"""
        self.refresh_providers()

    def on_provider_selected(self):
        """✅ MOSTRAR DETALLES COMPLETOS DEL PROVEEDOR SELECCIONADO"""
        selected_rows = self.providers_table.selectionModel().selectedRows()
        
        if not selected_rows:
            self.details_title.setText("📝 Seleccione un proveedor para ver detalles")
            self.details_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #666; margin: 2px 0;")
            self.products_table.setRowCount(0)
            self.provider_payments_table.setRowCount(0)
            self.stats_label.setText("")
            self.btn_add_provider_payment.setEnabled(False)
            return
        
        row = selected_rows[0].row()
        name_item = self.providers_table.item(row, 0)
        provider_id = name_item.data(Qt.UserRole)
        
        if not provider_id:
            return
            
        try:
            # Obtener proveedor
            provider = session.query(Provider).filter_by(id=provider_id).first()
            if not provider:
                return
                
            # Actualizar título
            provider_name = provider.name.replace("🏪 ", "")
            self.details_title.setText(f"📝 {provider_name}")
            self.details_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2196F3; margin: 2px 0;")
            
            # Habilitar botón de agregar pago
            self.btn_add_provider_payment.setEnabled(True)
            
            # ========== CARGAR PRODUCTOS ==========
            products = session.query(Product).filter_by(provider_id=provider_id).order_by(Product.name).all()
            
            self.products_table.setRowCount(len(products))
            
            total_products = len(products)
            total_value = 0
            low_stock_count = 0
            
            for r, prod in enumerate(products):
                code_item = QTableWidgetItem(prod.code)
                name_item = QTableWidgetItem(prod.name)
                price_item = QTableWidgetItem(f"₡{int(prod.price):,}")
                stock_item = QTableWidgetItem(f"{prod.stock:,}")
                
                # Resaltar stock bajo
                if prod.stock < 5:
                    stock_item.setBackground(Qt.GlobalColor.yellow)
                    stock_item.setText(f"⚠️ {prod.stock:,}")
                    low_stock_count += 1
                elif prod.stock == 0:
                    stock_item.setBackground(Qt.GlobalColor.red)
                    stock_item.setForeground(Qt.GlobalColor.white)
                    stock_item.setText("❌ Agotado")
                
                # Alineación
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                stock_item.setTextAlignment(Qt.AlignCenter)
                
                self.products_table.setItem(r, 0, code_item)
                self.products_table.setItem(r, 1, name_item)
                self.products_table.setItem(r, 2, price_item)
                self.products_table.setItem(r, 3, stock_item)
                
                total_value += prod.price * prod.stock

            # ========== CARGAR PAGOS DEL PROVEEDOR ==========
            payments = session.query(Payment).filter(
                Payment.is_provider == True,
                Payment.category == provider.name
            ).order_by(Payment.date.desc()).all()
            
            self.provider_payments_table.setRowCount(len(payments))
            
            total_payments = 0
            
            for r, payment in enumerate(payments):
                date_item = QTableWidgetItem(payment.date.strftime("%Y-%m-%d"))
                amount_item = QTableWidgetItem(f"₡{int(payment.amount):,}")
                
                # Guardar datos para edición
                date_item.setData(Qt.UserRole, payment.id)
                
                amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                self.provider_payments_table.setItem(r, 0, date_item)
                self.provider_payments_table.setItem(r, 1, amount_item)
                
                total_payments += payment.amount
            
            # ========== ACTUALIZAR ESTADÍSTICAS ==========
            stats_text = (
                f"📊 {total_products} productos • "
                f"💰 Inventario: ₡{int(total_value):,} • "
                f"💸 Total pagado: ₡{int(total_payments):,} • "
                f"📞 {provider.contact or 'Sin contacto'}"
            )
            
            if low_stock_count > 0:
                stats_text += f" • ⚠️ {low_stock_count} productos con stock bajo"
                
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            print(f"❌ Error cargando detalles del proveedor: {e}")

    def add_payment_to_selected_provider(self):
        """✅ AGREGAR PAGO AL PROVEEDOR SELECCIONADO"""
        selected_rows = self.providers_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.information(self, "Seleccionar Proveedor", 
                                   "Seleccione un proveedor primero")
            return
        
        row = selected_rows[0].row()
        name_item = self.providers_table.item(row, 0)
        provider_id = name_item.data(Qt.UserRole)
        
        provider = session.query(Provider).filter_by(id=provider_id).first()
        if not provider:
            return
        
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Agregar Pago - {provider.name}")
        dlg.setModal(True)
        
        layout = QFormLayout(dlg)
        layout.setSpacing(15)

        provider_label = QLabel(f"🏪 {provider.name}")
        provider_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2196F3;")

        inp_amount = QDoubleSpinBox()
        inp_amount.setRange(0, 1_000_000_000)
        inp_amount.setDecimals(0)
        inp_amount.setPrefix("₡")
        inp_amount.setValue(0)

        layout.addRow("Proveedor:", provider_label)
        layout.addRow("💰 Monto:", inp_amount)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("✅ Registrar Pago")
        btns.button(QDialogButtonBox.Cancel).setText("❌ Cancelar")
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)

        if dlg.exec() == QDialog.Accepted:
            amount = inp_amount.value()
            
            if amount <= 0:
                QMessageBox.warning(self, "Monto Inválido", "El monto debe ser mayor a 0")
                return
            
            try:
                # Crear el pago
                pay = Payment(
                    date=datetime.now(),
                    amount=amount,
                    category=provider.name,
                    is_provider=True
                )
                session.add(pay)
                session.commit()
                
                # Emitir señal
                self.providerDone.emit(amount)
                
                QMessageBox.information(self, "Pago Registrado", 
                                       f"✅ Pago de ₡{int(amount):,} registrado para '{provider.name}'")
                
                # Refrescar vista
                self.on_provider_selected()
                self.refresh()  # Refrescar la pestaña de pagos también
                
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Error", f"Error registrando pago: {str(e)}")

    def refresh_providers(self):
        """✅ CARGAR LISTA DE PROVEEDORES CON FILTRO DE BÚSQUEDA"""
        self.providers_table.setRowCount(0)
        try:
            search_text = self.search_provider.text().lower().strip()
            
            query = session.query(Provider)
            
            if search_text:
                query = query.filter(
                    (Provider.name.ilike(f'%{search_text}%')) |
                    (Provider.contact.ilike(f'%{search_text}%'))
                )
            
            providers = query.order_by(Provider.name).all()
            
            for prov in providers:
                product_count = session.query(Product).filter_by(provider_id=prov.id).count()
                
                r = self.providers_table.rowCount()
                self.providers_table.insertRow(r)
                
                name_item = QTableWidgetItem(f"🏪 {prov.name}")
                name_item.setData(Qt.UserRole, prov.id)
                
                contact_item = QTableWidgetItem(prov.contact or "Sin contacto")
                products_item = QTableWidgetItem(f"{product_count:,}")
                
                if product_count == 0:
                    products_item.setBackground(Qt.GlobalColor.yellow)
                    products_item.setText("⚠️ 0")
                
                self.providers_table.setItem(r, 0, name_item)
                self.providers_table.setItem(r, 1, contact_item)
                self.providers_table.setItem(r, 2, products_item)
                
        except Exception as e:
            print(f"❌ Error cargando proveedores: {e}")

    def create_payments_tab(self):
        """✅ PESTAÑA DE PAGOS CON BOTÓN DE EDITAR Y BÚSQUEDA"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # ========== TÍTULO DE SECCIÓN ==========
        title = QLabel("💰 Registro de Pagos a Proveedores")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; margin: 10px 0;")
        layout.addWidget(title)

        # ========== BARRA DE BÚSQUEDA ==========
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        search_label = QLabel("🔍 Buscar:")
        search_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        search_layout.addWidget(search_label)

        self.search_payments = QLineEdit()
        self.search_payments.setPlaceholderText("Buscar por proveedor")
        self.search_payments.setStyleSheet(
            """
            QLineEdit {
                min-height: 32px; 
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
        self.search_payments.textChanged.connect(self.on_payments_search_changed)
        search_layout.addWidget(self.search_payments, 3)

        # Botón para limpiar búsqueda
        self.btn_clear_search = QPushButton("🗑️ Limpiar")
        self.btn_clear_search.setStyleSheet(
            """
            QPushButton {
                background-color: #6C757D;
                color: white;
                padding: 8px 12px;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
            QPushButton:pressed {
                background-color: #545B62;
            }
            """
        )
        self.btn_clear_search.clicked.connect(self.clear_payments_search)
        search_layout.addWidget(self.btn_clear_search)
        search_layout.addStretch()
        
        layout.addLayout(search_layout)

        # ========== TABLA DE PAGOS ==========
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Fecha", "Proveedor", "Monto"])
        
        # Configuración de columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # Estilo consistente
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
            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
            """
        )
        
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.installEventFilter(self)
        
        table_font = QFont()
        table_font.setPointSize(14)
        self.table.setFont(table_font)
        self.table.verticalHeader().setDefaultSectionSize(40)
        
        layout.addWidget(self.table)

        # ========== BOTONES ==========
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 110px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """
        
        edit_button_style = """
            QPushButton {
                background-color: #FFC107;
                color: #212529;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 110px;
            }
            QPushButton:hover {
                background-color: #E0A800;
            }
            QPushButton:pressed {
                background-color: #D39E00;
            }
        """
        
        delete_button_style = """
            QPushButton {
                background-color: #DC3545;
                color: white;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 110px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:pressed {
                background-color: #BD2130;
            }
        """
        
        self.btn_add = QPushButton("➕ Agregar Pago")
        self.btn_add.setStyleSheet(button_style)
        
        self.btn_edit = QPushButton("✏️ Editar Pago")
        self.btn_edit.setStyleSheet(edit_button_style)
        
        self.btn_del = QPushButton("🗑️ Eliminar Pago")
        self.btn_del.setStyleSheet(delete_button_style)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_del)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)

        # ========== CONEXIONES ==========
        self.btn_add.clicked.connect(self.open_add_dialog)
        self.btn_edit.clicked.connect(self.edit_payment)
        self.btn_del.clicked.connect(self.delete_payment)

        # Cargar pagos
        self.refresh()
        
        return widget

    def add_provider(self):
        """✅ AGREGAR PROVEEDOR"""
        dlg = QDialog(self)
        dlg.setWindowTitle("Agregar Nuevo Proveedor")
        dlg.setModal(True)
        
        layout = QFormLayout(dlg)
        layout.setSpacing(15)

        inp_name = QLineEdit()
        inp_name.setPlaceholderText("Nombre del proveedor")
        
        inp_contact = QLineEdit()
        inp_contact.setPlaceholderText("Teléfono, email o dirección")
        
        layout.addRow("🏪 Nombre:", inp_name)
        layout.addRow("📞 Contacto:", inp_contact)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("✅ Crear Proveedor")
        btns.button(QDialogButtonBox.Cancel).setText("❌ Cancelar")
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)

        if dlg.exec() == QDialog.Accepted:
            name = inp_name.text().strip()
            contact = inp_contact.text().strip()
            
            if not name:
                QMessageBox.warning(self, "Campo Requerido", "El nombre del proveedor es obligatorio")
                return
            
            if session.query(Provider).filter_by(name=name).first():
                QMessageBox.warning(self, "Proveedor Duplicado", 
                                   f"Ya existe un proveedor con el nombre '{name}'")
                return
            
            try:
                prov = Provider(name=name, contact=contact)
                session.add(prov)
                session.commit()
                
                QMessageBox.information(self, "Proveedor Creado", 
                                       f"✅ Proveedor '{name}' creado correctamente")
                self.refresh_providers()
                
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Error", f"Error creando proveedor: {str(e)}")

    def edit_provider(self):
        """✅ EDITAR PROVEEDOR"""
        r = self.providers_table.currentRow()
        if r < 0:
            QMessageBox.information(self, "Seleccionar Proveedor", 
                                   "Seleccione un proveedor de la lista para editar")
            return
        
        name_item = self.providers_table.item(r, 0)
        provider_id = name_item.data(Qt.UserRole)
        
        if not provider_id:
            QMessageBox.warning(self, "Error de Datos", "No se pudo obtener el ID del proveedor")
            self.refresh_providers()
            return
            
        prov = session.query(Provider).filter_by(id=provider_id).first()
        
        if not prov:
            QMessageBox.warning(self, "Proveedor No Encontrado", 
                               "El proveedor seleccionado no existe en la base de datos")
            self.refresh_providers()
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Editar Proveedor: {prov.name}")
        dlg.setModal(True)
        
        layout = QFormLayout(dlg)
        layout.setSpacing(15)

        inp_name = QLineEdit(prov.name)
        inp_contact = QLineEdit(prov.contact or "")
        
        layout.addRow("🏪 Nombre:", inp_name)
        layout.addRow("📞 Contacto:", inp_contact)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("✅ Guardar Cambios")
        btns.button(QDialogButtonBox.Cancel).setText("❌ Cancelar")
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)

        if dlg.exec() == QDialog.Accepted:
            new_name = inp_name.text().strip()
            new_contact = inp_contact.text().strip()
            
            if not new_name:
                QMessageBox.warning(self, "Campo Requerido", "El nombre del proveedor es obligatorio")
                return
            
            existing = session.query(Provider).filter(
                Provider.name == new_name,
                Provider.id != prov.id
            ).first()
            
            if existing:
                QMessageBox.warning(self, "Nombre Duplicado", 
                                   f"Ya existe otro proveedor con el nombre '{new_name}'")
                return
            
            try:
                old_name = prov.name
                prov.name = new_name
                prov.contact = new_contact
                session.commit()
                
                QMessageBox.information(self, "Proveedor Actualizado", 
                                       f"✅ Proveedor actualizado correctamente\n" +
                                       f"'{old_name}' → '{new_name}'")
                self.refresh_providers()
                
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Error", f"Error actualizando proveedor: {str(e)}")

    def delete_provider(self):
        """✅ ELIMINAR PROVEEDOR"""
        r = self.providers_table.currentRow()
        if r < 0:
            QMessageBox.information(self, "Seleccionar Proveedor", 
                                   "Seleccione un proveedor de la lista para eliminar")
            return
        
        name_item = self.providers_table.item(r, 0)
        provider_id = name_item.data(Qt.UserRole)
        
        if not provider_id:
            QMessageBox.warning(self, "Error de Datos", "No se pudo obtener el ID del proveedor")
            self.refresh_providers()
            return
            
        prov = session.query(Provider).filter_by(id=provider_id).first()
        
        if not prov:
            QMessageBox.warning(self, "Proveedor No Encontrado", 
                               "El proveedor seleccionado no existe en la base de datos")
            self.refresh_providers()
            return

        # Verificar si tiene productos asignados
        product_count = session.query(Product).filter_by(provider_id=prov.id).count()
        
        if product_count > 0:
            reply = QMessageBox.question(
                self, "Confirmar Eliminación",
                f"⚠️ El proveedor '{prov.name}' tiene {product_count:,} productos asignados.\n\n" +
                "¿Eliminar de todas formas?\n\n" +
                "📝 Los productos quedarán sin proveedor asignado.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            
            # Desasignar proveedor de productos
            products = session.query(Product).filter_by(provider_id=prov.id).all()
            for prod in products:
                prod.provider_id = None
                
            print(f"🔧 Desasignados {len(products)} productos del proveedor {prov.name}")
        else:
            reply = QMessageBox.question(
                self, "Confirmar Eliminación",
                f"¿Eliminar el proveedor '{prov.name}'?\n\n" +
                "⚠️ Esta acción no se puede deshacer.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        try:
            provider_name = prov.name
            session.delete(prov)
            session.commit()
            print(f"✅ Proveedor eliminado: {provider_name} (ID: {provider_id})")
            
            QMessageBox.information(self, "Proveedor Eliminado", 
                                   f"✅ Proveedor '{provider_name}' eliminado correctamente")
            self.refresh_providers()
            
            # Limpiar vista de detalles
            self.details_title.setText("📝 Seleccione un proveedor para ver detalles")
            self.details_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #666; margin: 2px 0;")
            self.products_table.setRowCount(0)
            self.provider_payments_table.setRowCount(0)
            self.stats_label.setText("")
            self.btn_add_provider_payment.setEnabled(False)
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error eliminando proveedor: {e}")
            QMessageBox.critical(self, "Error", f"Error eliminando proveedor: {str(e)}")
            self.refresh_providers()

    # ========== FUNCIONES DE PAGOS ==========
    def on_payments_search_changed(self, text):
        """✅ BÚSQUEDA DE PAGOS CON DELAY"""
        self.payments_search_timer.stop()
        if len(text) >= 2 or len(text) == 0:
            self.payments_search_timer.start(300)

    def perform_payments_search(self):
        """✅ EJECUTAR BÚSQUEDA DE PAGOS"""
        self.refresh()

    def clear_payments_search(self):
        """✅ LIMPIAR BÚSQUEDA DE PAGOS"""
        self.search_payments.clear()
        self.refresh()

    def refresh(self):
        """✅ Cargar pagos a proveedores con filtro de búsqueda"""
        self.table.setRowCount(0)
        try:
            # Obtener texto de búsqueda
            search_text = ""
            if hasattr(self, 'search_payments'):
                search_text = self.search_payments.text().lower().strip()
            
            # Query base
            query = session.query(Payment).filter(Payment.is_provider == True)
            
            # Aplicar filtro si hay búsqueda (solo por proveedor)
            if search_text:
                query = query.filter(Payment.category.ilike(f'%{search_text}%'))
            
            payments = query.order_by(Payment.date.desc()).all()
            
            for p in payments:
                r = self.table.rowCount()
                self.table.insertRow(r)
                
                date_item = QTableWidgetItem(p.date.strftime("%Y-%m-%d"))
                provider_item = QTableWidgetItem(p.category or "Sin especificar")
                amount_item = QTableWidgetItem(f"₡{int(p.amount):,}")
                
                # Guardar ID del pago para edición/eliminación
                date_item.setData(Qt.UserRole, p.id)
                
                amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                self.table.setItem(r, 0, date_item)
                self.table.setItem(r, 1, provider_item)
                self.table.setItem(r, 2, amount_item)
                
        except Exception as e:
            print(f"❌ Error cargando pagos: {e}")

    def open_add_dialog(self):
        """✅ AGREGAR PAGO A PROVEEDOR"""
        dlg = QDialog(self)
        dlg.setWindowTitle("Registrar Pago a Proveedor")
        dlg.setModal(True)
        
        layout = QFormLayout(dlg)
        layout.setSpacing(15)

        # Autocompletar con nombres de proveedores existentes
        prov_names = [pr.name for pr in session.query(Provider).order_by(Provider.name).all()]
        inp_name = QLineEdit()
        inp_name.setPlaceholderText("Seleccione o escriba el nombre del proveedor")
        
        if prov_names:
            completer = QCompleter(prov_names, dlg)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            inp_name.setCompleter(completer)

        inp_amount = QDoubleSpinBox()
        inp_amount.setRange(0, 1_000_000_000)
        inp_amount.setDecimals(0)
        inp_amount.setPrefix("₡")
        inp_amount.setValue(0)

        layout.addRow("🏪 Proveedor:", inp_name)
        layout.addRow("💰 Monto:", inp_amount)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("✅ Registrar Pago")
        btns.button(QDialogButtonBox.Cancel).setText("❌ Cancelar")
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)

        if dlg.exec() == QDialog.Accepted:
            name = inp_name.text().strip()
            amount = inp_amount.value()
            
            if not name:
                QMessageBox.warning(self, "Campo Requerido", "Debe especificar un proveedor")
                return
                
            if amount <= 0:
                QMessageBox.warning(self, "Monto Inválido", "El monto debe ser mayor a 0")
                return
            
            try:
                # Verificar si el proveedor existe, si no, crearlo
                prov = session.query(Provider).filter_by(name=name).first()
                if not prov:
                    reply = QMessageBox.question(
                        self, "Proveedor Nuevo",
                        f"El proveedor '{name}' no existe.\n\n¿Crear automáticamente?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        prov = Provider(name=name, contact="")
                        session.add(prov)
                        session.commit()
                        self.refresh_providers()
                    else:
                        return
                
                # Crear el pago
                pay = Payment(
                    date=datetime.now(),
                    amount=amount,
                    category=name,
                    is_provider=True
                )
                session.add(pay)
                session.commit()
                
                # Emitir señal
                self.providerDone.emit(amount)
                
                QMessageBox.information(self, "Pago Registrado", 
                                       f"✅ Pago de ₡{int(amount):,} registrado para '{name}'")
                self.refresh()
                
                # Si el proveedor está seleccionado, actualizar su vista
                self.on_provider_selected()
                
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Error", f"Error registrando pago: {str(e)}")

    def edit_payment(self):
        """✅ EDITAR PAGO EXISTENTE"""
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.information(self, "Seleccionar Pago", 
                                   "Seleccione un pago de la lista para editar")
            return
        
        date_item = self.table.item(r, 0)
        payment_id = date_item.data(Qt.UserRole)
        
        if not payment_id:
            QMessageBox.warning(self, "Error de Datos", "No se pudo obtener el ID del pago")
            self.refresh()
            return
            
        try:
            payment = session.query(Payment).filter_by(id=payment_id).first()
            
            if not payment:
                QMessageBox.warning(self, "Pago No Encontrado", 
                                   "El pago seleccionado no existe en la base de datos")
                self.refresh()
                return

            dlg = QDialog(self)
            dlg.setWindowTitle("Editar Pago a Proveedor")
            dlg.setModal(True)
            
            layout = QFormLayout(dlg)
            layout.setSpacing(15)

            # Autocompletar con nombres de proveedores existentes
            prov_names = [pr.name for pr in session.query(Provider).order_by(Provider.name).all()]
            inp_name = QLineEdit(payment.category or "")
            inp_name.setPlaceholderText("Seleccione o escriba el nombre del proveedor")
            
            if prov_names:
                completer = QCompleter(prov_names, dlg)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                inp_name.setCompleter(completer)

            inp_amount = QDoubleSpinBox()
            inp_amount.setRange(0, 1_000_000_000)
            inp_amount.setDecimals(0)
            inp_amount.setPrefix("₡")
            inp_amount.setValue(payment.amount)

            layout.addRow("🏪 Proveedor:", inp_name)
            layout.addRow("💰 Monto:", inp_amount)
            
            # Mostrar fecha actual (solo informativo)
            date_label = QLabel(payment.date.strftime("%Y-%m-%d %H:%M"))
            date_label.setStyleSheet("color: #666; font-style: italic;")
            layout.addRow("📅 Fecha:", date_label)

            btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btns.button(QDialogButtonBox.Ok).setText("✅ Guardar Cambios")
            btns.button(QDialogButtonBox.Cancel).setText("❌ Cancelar")
            btns.accepted.connect(dlg.accept)
            btns.rejected.connect(dlg.reject)
            layout.addRow(btns)

            if dlg.exec() == QDialog.Accepted:
                new_name = inp_name.text().strip()
                new_amount = inp_amount.value()
                
                if not new_name:
                    QMessageBox.warning(self, "Campo Requerido", "Debe especificar un proveedor")
                    return
                    
                if new_amount <= 0:
                    QMessageBox.warning(self, "Monto Inválido", "El monto debe ser mayor a 0")
                    return
                
                try:
                    # Verificar si el nuevo proveedor existe, si no, crearlo
                    if new_name != payment.category:
                        prov = session.query(Provider).filter_by(name=new_name).first()
                        if not prov:
                            reply = QMessageBox.question(
                                self, "Proveedor Nuevo",
                                f"El proveedor '{new_name}' no existe.\n\n¿Crear automáticamente?",
                                QMessageBox.Yes | QMessageBox.No
                            )
                            if reply == QMessageBox.Yes:
                                prov = Provider(name=new_name, contact="")
                                session.add(prov)
                                session.flush()  # Para obtener el ID
                                self.refresh_providers()
                            else:
                                return
                    
                    # Actualizar el pago
                    old_provider = payment.category
                    old_amount = payment.amount
                    
                    payment.category = new_name
                    payment.amount = new_amount
                    session.commit()
                    
                    QMessageBox.information(self, "Pago Actualizado", 
                                           f"✅ Pago actualizado correctamente\n\n" +
                                           f"Proveedor: '{old_provider}' → '{new_name}'\n" +
                                           f"Monto: ₡{int(old_amount):,} → ₡{int(new_amount):,}")
                    
                    self.refresh()
                    
                    # Si el proveedor está seleccionado, actualizar su vista
                    self.on_provider_selected()
                    
                except Exception as e:
                    session.rollback()
                    QMessageBox.critical(self, "Error", f"Error actualizando pago: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Error editando pago: {e}")
            QMessageBox.critical(self, "Error", f"Error editando pago: {str(e)}")

    def delete_payment(self):
        """✅ ELIMINAR PAGO"""
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.information(self, "Seleccionar Pago", 
                                   "Seleccione un pago de la lista para eliminar")
            return
        
        date_item = self.table.item(r, 0)
        payment_id = date_item.data(Qt.UserRole)
        
        if not payment_id:
            QMessageBox.warning(self, "Error de Datos", "No se pudo obtener el ID del pago")
            self.refresh()
            return
            
        try:
            payment = session.query(Payment).filter_by(id=payment_id).first()
            
            if not payment:
                QMessageBox.warning(self, "Pago No Encontrado", 
                                   "El pago seleccionado no existe en la base de datos")
                self.refresh()
                return
            
            date_str = payment.date.strftime("%Y-%m-%d")
            provider_name = payment.category or "Sin especificar"
            amount_str = f"₡{int(payment.amount):,}"
            
            if QMessageBox.question(
                self, "Confirmar Eliminación", 
                f"¿Eliminar el pago?\n\n" +
                f"📅 Fecha: {date_str}\n" +
                f"🏪 Proveedor: {provider_name}\n" +
                f"💰 Monto: {amount_str}\n\n" +
                "⚠️ Esta acción no se puede deshacer.", 
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            ) != QMessageBox.Yes:
                return
                
            session.delete(payment)
            session.commit()
            
            print(f"✅ Pago eliminado: {provider_name} - ₡{payment.amount} ({date_str})")
            QMessageBox.information(self, "Pago Eliminado", "✅ Pago eliminado correctamente")
            self.refresh()
            
            # Si el proveedor está seleccionado, actualizar su vista
            self.on_provider_selected()
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error eliminando pago: {e}")
            QMessageBox.critical(self, "Error", f"Error eliminando pago: {str(e)}")
            self.refresh()

    def eventFilter(self, obj, event):
        """✅ MANEJO DE EVENTOS"""
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Delete:
            if obj is self.providers_table:
                self.delete_provider()
                return True
            elif obj is self.table:
                self.delete_payment()
                return True
        return super().eventFilter(obj, event)