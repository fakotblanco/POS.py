# tabs/inventario.py - VERSIÓN COMPLETA CORREGIDA
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
    QFormLayout, QDialogButtonBox, QSpinBox, QDoubleSpinBox, QFileDialog,
    QHeaderView, QComboBox, QLabel, QCheckBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from db import session
from database_setup import Product, SaleItem, Sale, Entry, Provider
from datetime import date, timedelta
import csv

class InventoryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.current_page = 0
        self.items_per_page = 100  # ✅ PAGINACIÓN: Solo 100 productos por página
        self.search_timer = QTimer()  # ✅ BÚSQUEDA CON DELAY
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        # ========== CONTROLES SUPERIORES MEJORADOS ==========
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # Barra de búsqueda con estilo consistente
        controls_layout.addWidget(QLabel("🔍 Buscar:"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Código, nombre o proveedor (mín. 3 caracteres)")
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
        controls_layout.addWidget(self.search, 3)
        
        # Checkbox limpio
        self.auto_cleanup = QCheckBox("Auto-cleanup")
        self.auto_cleanup.setChecked(False)
        self.auto_cleanup.setToolTip("Limpieza automática de productos obsoletos (lento)")
        self.auto_cleanup.setStyleSheet(
            """
            QCheckBox {
                font-size: 14px;
                color: #666;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #E0E0E0;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border: 2px solid #2196F3;
            }
            """
        )
        controls_layout.addWidget(self.auto_cleanup)
        controls_layout.addStretch()
        self.layout().addLayout(controls_layout)

        # ========== CONTROLES DE PAGINACIÓN MEJORADOS ==========
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(10)
        
        # Botones de navegación con estilo consistente
        self.btn_prev = QPushButton("◀ Anterior")
        self.btn_prev.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: #999;
            }
            """
        )
        
        self.btn_next = QPushButton("Siguiente ▶")
        self.btn_next.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: #999;
            }
            """
        )
        
        # Labels informativos
        self.lbl_page = QLabel("Página 1")
        self.lbl_page.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        
        self.lbl_total = QLabel("Total: 0 productos")
        self.lbl_total.setStyleSheet("font-size: 14px; color: #666;")
        
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)
        self.btn_prev.setEnabled(False)
        
        pagination_layout.addWidget(self.btn_prev)
        pagination_layout.addWidget(self.lbl_page)
        pagination_layout.addWidget(self.btn_next)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.lbl_total)
        self.layout().addLayout(pagination_layout)

        # ========== TABLA MEJORADA CON DISEÑO CONSISTENTE ==========
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Código", "Producto", "Precio", "Stock", "Proveedor"])
        
        # Configuración de columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Código
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Nombre se expande
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Precio
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Stock
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Proveedor
        
        # Estilo consistente con factura
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
            """
        )

        # Fuente optimizada
        table_font = QFont()
        table_font.setPointSize(14)
        self.table.setFont(table_font)
        self.table_font = table_font
        self.table.verticalHeader().setDefaultSectionSize(40)

        self.layout().addWidget(self.table)

        # ========== BOTONES CON DISEÑO CONSISTENTE ==========
        btns = QHBoxLayout()
        btns.setSpacing(8)
        
        # Botones principales
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 16px;
                font-size: 14px;
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
        
        self.btn_add = QPushButton("➕ Agregar")
        self.btn_add.setStyleSheet(button_style)
        
        self.btn_edit = QPushButton("✏️ Editar")
        self.btn_edit.setStyleSheet(button_style)
        
        # Botón eliminar con color rojo
        self.btn_del = QPushButton("🗑️ Eliminar")
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
        
        # Botones secundarios con color gris
        secondary_style = """
            QPushButton {
                background-color: #6C757D;
                color: white;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
            QPushButton:pressed {
                background-color: #545B62;
            }
        """
        
        self.btn_import = QPushButton("📥 Importar CSV")
        self.btn_import.setStyleSheet(secondary_style)
        
        self.btn_export = QPushButton("📤 Exportar CSV")
        self.btn_export.setStyleSheet(secondary_style)
        
        self.btn_assign_provider = QPushButton("🏪 Asignar Proveedor")
        self.btn_assign_provider.setStyleSheet(secondary_style)
        
        # Botón cleanup con color naranja
        self.btn_cleanup = QPushButton("🧹 Limpiar Obsoletos")
        self.btn_cleanup.setStyleSheet(
            """
            QPushButton {
                background-color: #FD7E14;
                color: white;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 130px;
            }
            QPushButton:hover {
                background-color: #E8681A;
            }
            QPushButton:pressed {
                background-color: #DC5912;
            }
            """
        )
        
        # ✅ BOTÓN DE DEBUG TEMPORAL (PUEDES QUITARLO DESPUÉS)
        self.btn_debug = QPushButton("🔍 Verificar BD")
        self.btn_debug.setStyleSheet(
            """
            QPushButton {
                background-color: #17A2B8;
                color: white;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
            QPushButton:pressed {
                background-color: #117A8B;
            }
            """
        )
        
        # Agregar botones con espaciado
        for w in (self.btn_add, self.btn_edit, self.btn_del, self.btn_import, 
                  self.btn_export, self.btn_assign_provider, self.btn_cleanup, self.btn_debug):
            btns.addWidget(w)
            
        btns.addStretch()  # Empujar botones hacia la izquierda
        self.layout().addLayout(btns)

        # ========== CONEXIONES ==========
        self.btn_add.clicked.connect(self.add_item)
        self.btn_edit.clicked.connect(self.edit_item)
        self.btn_del.clicked.connect(self.delete_item)
        self.btn_import.clicked.connect(self.import_csv)
        self.btn_export.clicked.connect(self.export_csv)
        self.btn_assign_provider.clicked.connect(self.assign_provider)
        self.btn_cleanup.clicked.connect(self.manual_cleanup)
        self.btn_debug.clicked.connect(self.verify_database_connection)  # ✅ DEBUG

        # ✅ CARGA INICIAL OPTIMIZADA
        self.load_optimized()

    def on_search_changed(self, text):
        """✅ BÚSQUEDA CON DELAY: Evita lag al escribir"""
        self.search_timer.stop()
        if len(text) >= 3 or len(text) == 0:  # Buscar solo con 3+ caracteres o vacío
            self.search_timer.start(300)  # Esperar 300ms antes de buscar

    def perform_search(self):
        """✅ EJECUTAR BÚSQUEDA"""
        self.current_page = 0
        self.load_optimized()

    def get_base_query(self):
        """✅ QUERY BASE OPTIMIZADA"""
        text = self.search.text().lower().strip()
        
        # Query base con LEFT JOIN para proveedores
        query = session.query(Product).outerjoin(Provider)
        
        # Solo filtrar si hay texto de búsqueda
        if text:
            query = query.filter(
                (Product.code.ilike(f'%{text}%')) |
                (Product.name.ilike(f'%{text}%')) |
                (Provider.name.ilike(f'%{text}%'))
            )
        
        return query.order_by(Product.id)

    def debug_providers(self):
        """✅ FUNCIÓN DE DEBUG PARA VERIFICAR PROVEEDORES"""
        try:
            total_providers = session.query(Provider).count()
            providers = session.query(Provider).order_by(Provider.name).all()
            
            print(f"\n🔍 DEBUG PROVEEDORES:")
            print(f"📊 Total en base de datos: {total_providers}")
            print(f"📋 Proveedores encontrados:")
            
            for i, prov in enumerate(providers[:10], 1):  # Mostrar primeros 10
                product_count = session.query(Product).filter_by(provider_id=prov.id).count()
                print(f"  {i}. {prov.name} (ID: {prov.id}) - {product_count} productos")
                
            if len(providers) > 10:
                print(f"  ... y {len(providers) - 10} más")
                
            return len(providers)
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error en debug: {e}")
            return 0

    def assign_provider(self):
        """✅ ASIGNAR PROVEEDOR - TODOS LOS PROVEEDORES"""
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.information(self, "Asignar Proveedor", 
                                   "Seleccione un producto de la tabla")
            return
        
        # Obtener información del producto seleccionado
        code = self.table.item(r, 0).text()
        product_name = self.table.item(r, 1).text()
        
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Asignar Proveedor a: {product_name}")
        dlg.setModal(True)
        dlg.setStyleSheet(
            """
            QDialog {
                background-color: white;
            }
            QComboBox {
                padding: 8px 12px;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                background-color: #FAFAFA;
                min-height: 20px;
            }
            QComboBox:focus {
                border: 2px solid #2196F3;
                background-color: white;
            }
            """
        )
        
        form = QFormLayout(dlg)
        form.setSpacing(15)
        
        # Label informativo
        info_label = QLabel(f"📦 Producto: {product_name}")
        info_label.setStyleSheet("font-weight: bold; color: #333; padding: 5px;")
        form.addRow(info_label)
        
        combo_provider = QComboBox()
        combo_provider.addItem("Sin asignar", None)
        
        try:
            # ✅ CARGAR TODOS LOS PROVEEDORES SIN LÍMITE
            providers = session.query(Provider).order_by(Provider.name).all()
            print(f"📊 Cargando {len(providers)} proveedores para asignación")
            
            for prov in providers:
                # Contar productos de este proveedor
                product_count = session.query(Product).filter_by(provider_id=prov.id).count()
                display_text = f"🏪 {prov.name} ({product_count} productos)"
                combo_provider.addItem(display_text, prov.id)
            
            if len(providers) == 0:
                QMessageBox.warning(self, "Sin Proveedores", 
                                   "No hay proveedores registrados.\n\n" +
                                   "Vaya a la pestaña de Proveedores para crear uno.")
                return
                
        except Exception as e:
            print(f"❌ Error cargando proveedores: {e}")
            QMessageBox.critical(self, "Error", f"Error cargando proveedores: {str(e)}")
            return
        
        form.addRow("🏪 Seleccionar Proveedor:", combo_provider)
        
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("✅ Asignar")
        bb.button(QDialogButtonBox.Cancel).setText("❌ Cancelar")
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)
        
        if dlg.exec() == QDialog.Accepted:
            provider_id = combo_provider.currentData()
            selected_text = combo_provider.currentText()
            
            try:
                prod = session.query(Product).filter_by(code=code).first()
                if prod:
                    old_provider = prod.provider.name if prod.provider else "Sin asignar"
                    prod.provider_id = provider_id
                    session.commit()
                    
                    new_provider = selected_text.replace("🏪 ", "").split(" (")[0] if provider_id else "Sin asignar"
                    
                    self.load_optimized()  # Recargar tabla
                    
                    QMessageBox.information(self, "Proveedor Asignado", 
                                           f"✅ Proveedor asignado correctamente\n\n" +
                                           f"📦 Producto: {product_name}\n" +
                                           f"🏪 Proveedor: {old_provider} → {new_provider}")
                else:
                    QMessageBox.warning(self, "Error", "Producto no encontrado")
                    
            except Exception as e:
                session.rollback()
                print(f"❌ Error asignando proveedor: {e}")
                QMessageBox.critical(self, "Error", f"Error asignando proveedor: {str(e)}")

    def delete_item(self):
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.information(self, "Seleccionar Producto", 
                                   "Seleccione un producto de la tabla para eliminar")
            return
            
        product_name = self.table.item(r, 1).text()
        
        if QMessageBox.question(self, "Eliminar Producto", 
                               f"¿Eliminar el producto '{product_name}'?\n\n" +
                               "⚠️ Esta acción no se puede deshacer.", 
                               QMessageBox.Yes | QMessageBox.No,
                               QMessageBox.No) != QMessageBox.Yes:
            return
            
        try:
            code = self.table.item(r, 0).text()
            prod = session.query(Product).filter_by(code=code).first()
            if prod:
                session.delete(prod)
                session.commit()
                QMessageBox.information(self, "Producto Eliminado", 
                                       f"✅ Producto '{product_name}' eliminado correctamente")
                self.load_optimized()
            else:
                QMessageBox.warning(self, "Error", "Producto no encontrado")
                
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Error eliminando producto: {str(e)}")

    def import_csv(self):
        """✅ IMPORTAR CON PROGRESO"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return

        QMessageBox.information(self, "Formato CSV", 
                               "Formato esperado:\nCódigo;Nombre;Precio;Stock;Proveedor\n\n" +
                               "El proveedor es opcional.")

        reply = QMessageBox.question(self, "Confirmar Importación",
                                    "⚠️ Esto reemplazará todos los productos existentes.\n\n¿Continuar?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        # Mostrar progreso
        progress_msg = QMessageBox(self)
        progress_msg.setWindowTitle("Importando...")
        progress_msg.setText("Importando productos...\n\nPor favor espere.")
        progress_msg.setStandardButtons(QMessageBox.NoButton)
        progress_msg.show()

        try:
            session.query(Product).delete()
            session.commit()

            seen_codes = set()
            imported_count = 0
            
            with open(path, mode='r', encoding='utf-8-sig', newline='') as f:
                reader = csv.reader(f, delimiter=';')
                try:
                    next(reader)  # Saltar encabezado
                except StopIteration:
                    progress_msg.close()
                    QMessageBox.warning(self, "Importar", "El archivo está vacío")
                    return

                for row in reader:
                    if len(row) < 4:
                        continue

                    code = row[0].strip()
                    name = row[1].strip()
                    raw_price = row[2].strip().replace(',', '.')
                    raw_stock = row[3].strip()
                    provider_name = row[4].strip() if len(row) > 4 else ""

                    if not code or code in seen_codes:
                        continue
                    seen_codes.add(code)

                    try:
                        price = float(raw_price)
                        stock = int(float(raw_stock))
                    except ValueError:
                        continue

                    # Buscar o crear proveedor
                    provider_id = None
                    if provider_name:
                        provider = session.query(Provider).filter_by(name=provider_name).first()
                        if not provider:
                            provider = Provider(name=provider_name, contact="")
                            session.add(provider)
                            session.commit()
                        provider_id = provider.id

                    session.add(Product(
                        code=code, name=name, price=price, 
                        stock=stock, provider_id=provider_id
                    ))
                    imported_count += 1

            session.commit()
            progress_msg.close()
            
            QMessageBox.information(self, "Importar", 
                                   f"Importación completada.\n{imported_count:,} productos importados.")
            
            # Solo hacer cleanup si está habilitado
            if self.auto_cleanup.isChecked():
                self.cleanup_old_products()
                
            self.load_optimized()

        except Exception as e:
            progress_msg.close()
            session.rollback()
            QMessageBox.critical(self, "Error", f"Error en importación: {str(e)}")

    def export_csv(self):
        """✅ EXPORTAR OPTIMIZADO"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar CSV", "inventario_completo.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        
        try:
            # Contar total para mostrar progreso
            total = session.query(Product).count()
            
            if total > 1000:
                reply = QMessageBox.question(self, "Exportación Grande",
                                           f"Se exportarán {total:,} productos.\n\n" +
                                           "Esto puede tardar varios minutos. ¿Continuar?",
                                           QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
            
            # Mostrar progreso
            progress_msg = QMessageBox(self)
            progress_msg.setWindowTitle("Exportando...")
            progress_msg.setText(f"Exportando {total:,} productos...\n\nPor favor espere.")
            progress_msg.setStandardButtons(QMessageBox.NoButton)
            progress_msg.show()
            
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['Código','Nombre','Precio','Stock','Proveedor'])
                
                # Exportar en lotes para no saturar memoria
                batch_size = 1000
                offset = 0
                
                while True:
                    items = (session.query(Product)
                            .outerjoin(Provider)
                            .offset(offset)
                            .limit(batch_size)
                            .all())
                    
                    if not items:
                        break
                        
                    for p in items:
                        provider_name = p.provider.name if p.provider else ""
                        writer.writerow([p.code, p.name, p.price, p.stock, provider_name])
                    
                    offset += batch_size
            
            progress_msg.close()
            QMessageBox.information(self, "Exportar", 
                                   f"Exportación completada.\n{total:,} productos exportados.")
            
        except Exception as e:
            if 'progress_msg' in locals():
                progress_msg.close()
            QMessageBox.critical(self, "Error", f"Error en exportación: {str(e)}")

    def eventFilter(self, obj, event):
        if (obj is self.table and event.type() == Qt.QEvent.KeyPress and 
            event.key() == Qt.Key_Backspace):
            self.delete_item()
            return True
        return super().eventFilter(obj, event)

    # ✅ FUNCIÓN LEGACY PARA COMPATIBILIDAD - CORREGIDA
    def load(self):
        """Función para compatibilidad con otras pestañas"""
        try:
            self.load_optimized()
        except Exception as e:
            print(f"❌ Error en debug: {e}")
            return 0

    def load_optimized(self):
        """✅ CARGA ULTRA-OPTIMIZADA CON DEBUG"""
        try:
            # Debug de proveedores
            provider_count = self.debug_providers()
            
            # Limpiar tabla
            self.table.setRowCount(0)
            
            # Obtener query base
            base_query = self.get_base_query()
            
            # Contar total (para paginación)
            total_count = base_query.count()
            
            # Aplicar paginación
            offset = self.current_page * self.items_per_page
            items = base_query.offset(offset).limit(self.items_per_page).all()
            
            print(f"📊 Mostrando {len(items)} productos de {total_count} totales")
            
            # Llenar tabla
            self.table.setRowCount(len(items))
            for r, p in enumerate(items):
                provider_name = p.provider.name if p.provider else "Sin asignar"
                values = [p.code, p.name, f"₡{int(p.price):,}", f"{p.stock:,}", provider_name]
                
                for c, v in enumerate(values):
                    item = QTableWidgetItem(v)
                    item.setFont(self.table_font)
                    # Resaltar productos sin proveedor
                    if c == 4 and provider_name == "Sin asignar":
                        item.setBackground(Qt.GlobalColor.yellow)
                    self.table.setItem(r, c, item)
            
            # Actualizar controles de paginación
            self.update_pagination_controls(total_count)
            
            print(f"✅ Inventario cargado: {len(items)} productos, {provider_count} proveedores disponibles")
            
        except Exception as e:
            print(f"❌ Error cargando inventario: {e}")
            QMessageBox.warning(self, "Error", f"Error cargando inventario: {str(e)}")

    def verify_database_connection(self):
        """✅ VERIFICAR CONEXIÓN Y DATOS"""
        try:
            # Verificar conexión básica
            total_products = session.query(Product).count()
            total_providers = session.query(Provider).count()
            
            # Verificar productos con proveedores
            products_with_providers = session.query(Product).filter(Product.provider_id.isnot(None)).count()
            products_without_providers = total_products - products_with_providers
            
            # Obtener ejemplos de proveedores
            sample_providers = session.query(Provider).limit(5).all()
            provider_examples = "\n".join([f"• {p.name} (ID: {p.id})" for p in sample_providers])
            
            info_text = (
                f"📊 ESTADO DE LA BASE DE DATOS:\n\n" +
                f"📦 Total productos: {total_products:,}\n" +
                f"🏪 Total proveedores: {total_providers:,}\n" +
                f"✅ Productos con proveedor: {products_with_providers:,}\n" +
                f"⚠️ Productos sin proveedor: {products_without_providers:,}\n\n"
            )
            
            if total_providers == 0:
                info_text += "❌ No hay proveedores en la base de datos"
            else:
                info_text += f"📋 Ejemplos de proveedores:\n{provider_examples}"
            
            QMessageBox.information(self, "Estado de la Base de Datos", info_text)
            
            # Debug en consola
            print(f"\n{info_text}")
            
        except Exception as e:
            error_msg = f"❌ Error verificando base de datos: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Error de Base de Datos", error_msg)

    def update_pagination_controls(self, total_count):
        """✅ ACTUALIZAR CONTROLES DE PAGINACIÓN"""
        total_pages = (total_count + self.items_per_page - 1) // self.items_per_page
        current_display = self.current_page + 1
        
        self.lbl_page.setText(f"Página {current_display} de {total_pages}")
        self.lbl_total.setText(f"Total: {total_count:,} productos")
        
        self.btn_prev.setEnabled(self.current_page > 0)
        self.btn_next.setEnabled(self.current_page < total_pages - 1)

    def prev_page(self):
        """✅ PÁGINA ANTERIOR"""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_optimized()

    def next_page(self):
        """✅ PÁGINA SIGUIENTE"""
        self.current_page += 1
        self.load_optimized()

    def manual_cleanup(self):
        """✅ LIMPIEZA MANUAL DE PRODUCTOS OBSOLETOS - SIN CONGELAMIENTO"""
        reply = QMessageBox.question(
            self, "Limpiar Productos Obsoletos",
            "¿Eliminar productos sin actividad en los últimos 4 meses?\n\n" +
            "⚠️ Esta operación puede tardar varios minutos con muchos productos.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            # Primero verificar si hay productos obsoletos SIN eliminar
            cutoff = date.today() - timedelta(days=120)  # 4 meses
            
            print(f"🔍 Verificando productos obsoletos desde: {cutoff}")
            
            # Contar productos obsoletos primero (más eficiente)
            obsolete_count = self.count_obsolete_products(cutoff)
            
            if obsolete_count == 0:
                QMessageBox.information(self, "Limpieza Completada", 
                                       "No se encontraron productos obsoletos.\n\n" +
                                       "Todos los productos tienen actividad reciente.")
                return
            
            # Confirmar eliminación específica
            final_reply = QMessageBox.question(
                self, "Confirmar Eliminación",
                f"Se encontraron {obsolete_count} productos obsoletos.\n\n" +
                f"¿Eliminar estos {obsolete_count} productos?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if final_reply != QMessageBox.Yes:
                return
            
            # Mostrar progreso real
            progress_msg = QMessageBox(self)
            progress_msg.setWindowTitle("Eliminando...")
            progress_msg.setText(f"Eliminando {obsolete_count} productos obsoletos...\n\n" +
                               "Por favor espere, esto puede tardar unos minutos.")
            progress_msg.setStandardButtons(QMessageBox.NoButton)
            progress_msg.show()
            
            # Forzar actualización de UI
            progress_msg.repaint()
            self.repaint()
            
            # Ejecutar limpieza eficiente
            deleted_count = self.cleanup_old_products_efficient(cutoff)
            
            progress_msg.close()
            
            if deleted_count > 0:
                QMessageBox.information(self, "Limpieza Completada", 
                                       f"✅ Se eliminaron {deleted_count} productos obsoletos.\n\n" +
                                       f"Inventario actualizado correctamente.")
                self.load_optimized()
            else:
                QMessageBox.information(self, "Limpieza Completada", 
                                       "⚠️ No se pudieron eliminar productos.")
                
        except Exception as e:
            if 'progress_msg' in locals():
                progress_msg.close()
            error_msg = f"Error en limpieza: {str(e)}"
            print(f"❌ {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)

    def count_obsolete_products(self, cutoff_date):
        """✅ CONTAR PRODUCTOS OBSOLETOS SIN CARGARLOS"""
        try:
            # Query más eficiente usando subconsultas
            subquery_sales = (
                session.query(Product.id)
                       .join(SaleItem, Product.id == SaleItem.product_id)
                       .join(Sale, SaleItem.sale_id == Sale.id)
                       .filter(Sale.date >= cutoff_date)
            )
            
            subquery_entries = (
                session.query(Product.id)
                       .join(Entry, Product.id == Entry.product_id)
                       .filter(Entry.date >= cutoff_date)
            )
            
            # Productos con actividad reciente
            active_products = subquery_sales.union(subquery_entries).subquery()
            
            # Contar productos SIN actividad reciente
            obsolete_count = (
                session.query(Product.id)
                       .filter(~Product.id.in_(session.query(active_products.c.id)))
                       .count()
            )
            
            print(f"📊 Productos obsoletos encontrados: {obsolete_count}")
            return obsolete_count
            
        except Exception as e:
            print(f"❌ Error contando obsoletos: {e}")
            return 0

    def cleanup_old_products_efficient(self, cutoff_date):
        """✅ LIMPIEZA ULTRA-EFICIENTE SIN CONGELAMIENTO"""
        try:
            deleted_count = 0
            
            # Obtener IDs de productos obsoletos en una sola query
            subquery_sales = (
                session.query(Product.id)
                       .join(SaleItem, Product.id == SaleItem.product_id)
                       .join(Sale, SaleItem.sale_id == Sale.id)
                       .filter(Sale.date >= cutoff_date)
            )
            
            subquery_entries = (
                session.query(Product.id)
                       .join(Entry, Product.id == Entry.product_id)
                       .filter(Entry.date >= cutoff_date)
            )
            
            # Productos con actividad reciente
            active_products = subquery_sales.union(subquery_entries)
            
            # Eliminar productos obsoletos en lotes pequeños
            batch_size = 50  # Lotes más pequeños para evitar congelamiento
            
            while True:
                # Obtener IDs de productos obsoletos
                obsolete_ids = (
                    session.query(Product.id)
                           .filter(~Product.id.in_(active_products))
                           .limit(batch_size)
                           .all()
                )
                
                if not obsolete_ids:
                    break
                
                # Eliminar lote actual
                ids_to_delete = [pid[0] for pid in obsolete_ids]
                
                session.query(Product).filter(Product.id.in_(ids_to_delete)).delete(synchronize_session=False)
                session.commit()  # Commit después de cada lote
                
                deleted_count += len(ids_to_delete)
                print(f"🗑️ Eliminados {len(ids_to_delete)} productos, total: {deleted_count}")
                
                # Pequeña pausa para no saturar la UI
                self.repaint()
            
            print(f"✅ Limpieza completada: {deleted_count} productos eliminados")
            return deleted_count
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error en limpieza eficiente: {e}")
            raise e

    def cleanup_old_products(self):
        """✅ FUNCIÓN LEGACY - REDIRIGE A LA EFICIENTE"""
        cutoff = date.today() - timedelta(days=120)  # 4 meses
        return self.cleanup_old_products_efficient(cutoff)

    # ========== FUNCIONES CRUD CORREGIDAS ==========
    def show_dialog(self, prod=None):
        """✅ DIÁLOGO OPTIMIZADO - TODOS LOS PROVEEDORES"""
        dlg = QDialog(self)
        dlg.setWindowTitle("Agregar/Editar Producto")
        dlg.setStyleSheet(
            """
            QDialog {
                background-color: white;
            }
            QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {
                padding: 8px 12px;
                font-size: 14px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                background-color: #FAFAFA;
                min-height: 20px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {
                border: 2px solid #2196F3;
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
        inp_price.setDecimals(2)
        inp_price.setMaximum(1e9)
        inp_price.setPrefix("₡")
        inp_price.setValue(prod.price if prod else 0)
        
        inp_stock = QSpinBox()
        inp_stock.setMaximum(10**6)
        inp_stock.setValue(prod.stock if prod else 0)
        
        # ✅ SELECTOR DE PROVEEDOR - CARGAR TODOS SIN LÍMITE
        inp_provider = QComboBox()
        inp_provider.addItem("Sin asignar", None)
        
        try:
            # ✅ QUITAR LÍMITE - CARGAR TODOS LOS PROVEEDORES
            providers = session.query(Provider).order_by(Provider.name).all()
            print(f"📊 Cargando {len(providers)} proveedores en el diálogo")
            
            for prov in providers:
                inp_provider.addItem(f"🏪 {prov.name}", prov.id)
                
            if len(providers) == 0:
                print("⚠️ No se encontraron proveedores en la base de datos")
                QMessageBox.information(dlg, "Sin Proveedores", 
                                       "No hay proveedores registrados.\n\n" +
                                       "Vaya a la pestaña de Proveedores para crear uno.")
                
        except Exception as e:
            print(f"❌ Error cargando proveedores: {e}")
            QMessageBox.warning(dlg, "Error", f"Error cargando proveedores: {str(e)}")
        
        # Seleccionar proveedor actual
        if prod and prod.provider:
            for i in range(inp_provider.count()):
                if inp_provider.itemData(i) == prod.provider.id:
                    inp_provider.setCurrentIndex(i)
                    print(f"✅ Proveedor seleccionado: {prod.provider.name}")
                    break
        
        form.addRow("🏷️ Nombre:", inp_name)
        form.addRow("💰 Precio:", inp_price)
        form.addRow("📊 Stock:", inp_stock)
        form.addRow("🏪 Proveedor:", inp_provider)
        form.addRow("📦 Código:", inp_code)
        
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
            stock = inp_stock.value()
            provider_id = inp_provider.currentData()
            
            if not code or not name:
                QMessageBox.warning(dlg, "Campos Requeridos", "Código y nombre son obligatorios")
                return None
                
            return code, name, price, stock, provider_id
        return None

    def add_item(self):
        data = self.show_dialog()
        if not data:
            return
        code, name, price, stock, provider_id = data
        if session.query(Product).filter_by(code=code).first():
            QMessageBox.warning(self, "Error", "Código duplicado")
            return
        
        try:
            session.add(Product(
                code=code, name=name, price=price, 
                stock=stock, provider_id=provider_id
            ))
            session.commit()
            QMessageBox.information(self, "Producto Agregado", 
                                   f"✅ Producto '{name}' agregado correctamente")
            self.load_optimized()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Error agregando producto: {str(e)}")

    def edit_item(self):
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.information(self, "Seleccionar Producto", 
                                   "Seleccione un producto de la tabla para editar")
            return
            
        code = self.table.item(r, 0).text()
        prod = session.query(Product).filter_by(code=code).first()
        
        if not prod:
            QMessageBox.warning(self, "Producto No Encontrado", 
                               "El producto seleccionado no existe")
            self.load_optimized()
            return
            
        data = self.show_dialog(prod)
        if not data:
            return
            
        new_code, name, price, stock, provider_id = data
        
        if new_code != prod.code and session.query(Product).filter_by(code=new_code).first():
            QMessageBox.warning(self, "Error", "Código duplicado")
            return
            
        try:
            old_name = prod.name
            prod.code = new_code
            prod.name = name
            prod.price = price
            prod.stock = stock
            prod.provider_id = provider_id
            session.commit()
            
            QMessageBox.information(self, "Producto Actualizado", 
                                   f"✅ Producto actualizado correctamente\n" +
                                   f"'{old_name}' → '{name}'")
            self.load_optimized()
            
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Error editando producto: {str(e)}")