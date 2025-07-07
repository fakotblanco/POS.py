# tabs/pagos.py - VERSIÓN CON DISEÑO CONSISTENTE
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QLineEdit, QDoubleSpinBox, QAbstractItemView, QFileDialog, QLabel,
    QHeaderView
)
from PySide6.QtCore import Qt, QEvent, Signal
from PySide6.QtGui import QFont
from db import session
from database_setup import Payment
from datetime import datetime
import csv
import re
import unicodedata

class PagosTab(QWidget):
    # Señal emitida tras registrar un pago genérico: monto
    paymentDone = Signal(float)

    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(15)

        # ========== TÍTULO DE SECCIÓN ==========
        title = QLabel("💳 Registro de Pagos Generales")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; margin: 10px 0;")
        self.layout().addWidget(title)

        # ========== INFORMACIÓN DESCRIPTIVA ==========
        info_label = QLabel("📝 Registre aquí los pagos generales del negocio (servicios, gastos operativos, etc.)")
        info_label.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 10px;")
        self.layout().addWidget(info_label)

        # ========== TABLA CON DISEÑO CONSISTENTE ==========
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Fecha y Hora", "Concepto", "Monto"])
        
        # Configuración de columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Fecha
        header.setSectionResizeMode(1, QHeaderView.Stretch)         # Concepto se expande
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Monto
        
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
        
        # Configuración de edición y selección
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.installEventFilter(self)
        
        # Fuente optimizada
        table_font = QFont()
        table_font.setPointSize(14)
        self.table.setFont(table_font)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.verticalHeader().setVisible(False)

        self.layout().addWidget(self.table)

        # ========== BOTONES CON DISEÑO CONSISTENTE ==========
        btns = QHBoxLayout()
        btns.setSpacing(8)
        
        # Botón principal (agregar)
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """
        
        # Botón eliminar con color rojo
        delete_style = """
            QPushButton {
                background-color: #DC3545;
                color: white;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:pressed {
                background-color: #BD2130;
            }
        """
        
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
        
        self.btn_add = QPushButton("➕ Agregar Pago")
        self.btn_add.setStyleSheet(button_style)
        
        self.btn_del = QPushButton("🗑️ Eliminar Pago")
        self.btn_del.setStyleSheet(delete_style)
        
        self.btn_import = QPushButton("📥 Importar CSV")
        self.btn_import.setStyleSheet(secondary_style)
        
        self.btn_export = QPushButton("📤 Exportar CSV")
        self.btn_export.setStyleSheet(secondary_style)
        
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_del)
        btns.addWidget(self.btn_import)
        btns.addWidget(self.btn_export)
        btns.addStretch()  # Empujar botones hacia la izquierda

        self.layout().addLayout(btns)

        # ========== CONEXIONES ==========
        self.btn_add.clicked.connect(self.open_dialog)
        self.btn_del.clicked.connect(self.delete_payment)
        self.btn_import.clicked.connect(self.import_csv)
        self.btn_export.clicked.connect(self.export_csv)

        # Carga inicial
        self.refresh()

    def refresh(self):
        """✅ Cargar pagos con mejor manejo de errores"""
        self.table.setRowCount(0)
        try:
            payments = (
                session.query(Payment)
                       .filter(Payment.is_provider == 0)
                       .order_by(Payment.date.desc())
                       .all()
            )
            
            for p in payments:
                r = self.table.rowCount()
                self.table.insertRow(r)
                
                # Fecha y hora formateada
                date_item = QTableWidgetItem(p.date.strftime("%Y-%m-%d %H:%M"))
                concept_item = QTableWidgetItem(p.category or "Sin concepto")
                amount_item = QTableWidgetItem(f"₡{int(p.amount):,}")
                
                self.table.setItem(r, 0, date_item)
                self.table.setItem(r, 1, concept_item)
                self.table.setItem(r, 2, amount_item)
                
        except Exception as e:
            print(f"❌ Error cargando pagos: {e}")

    def open_dialog(self):
        """✅ DIÁLOGO MEJORADO PARA AGREGAR PAGOS"""
        dlg = QDialog(self)
        dlg.setWindowTitle("Registrar Nuevo Pago")
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
                border: 2px solid #2196F3;
                background-color: white;
            }
            """
        )
        
        form = QFormLayout(dlg)
        form.setSpacing(15)
        
        concept_input = QLineEdit()
        concept_input.setPlaceholderText("Descripción del pago (ej: Servicios públicos, alquiler, etc.)")
        
        amount_input = QDoubleSpinBox()
        amount_input.setRange(0, 1_000_000_000)
        amount_input.setDecimals(0)
        amount_input.setPrefix("₡")
        amount_input.setValue(0)
        
        form.addRow("💳 Concepto:", concept_input)
        form.addRow("💰 Monto:", amount_input)
        
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Save).setText("✅ Registrar Pago")
        bb.button(QDialogButtonBox.Cancel).setText("❌ Cancelar")
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        form.addRow(bb)
        
        if dlg.exec() == QDialog.Accepted:
            concept = concept_input.text().strip()
            amount = amount_input.value()
            
            if not concept:
                QMessageBox.warning(self, "Campo Requerido", 
                                   "El concepto del pago no puede estar vacío")
                return
                
            if amount <= 0:
                QMessageBox.warning(self, "Monto Inválido", 
                                   "El monto debe ser mayor a 0")
                return
                
            try:
                pay = Payment(
                    date=datetime.now(), 
                    amount=amount, 
                    category=concept, 
                    is_provider=0
                )
                session.add(pay)
                session.commit()
                
                self.paymentDone.emit(amount)
                
                QMessageBox.information(self, "Pago Registrado", 
                                       f"✅ Pago registrado correctamente\n\n" +
                                       f"💳 Concepto: {concept}\n" +
                                       f"💰 Monto: ₡{int(amount):,}")
                self.refresh()
                
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Error", f"Error registrando pago: {str(e)}")

    def delete_payment(self):
        """✅ ELIMINAR PAGO CON MEJOR UX"""
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.information(self, "Seleccionar Pago", 
                                   "Seleccione un pago de la lista para eliminar")
            return
            
        # Obtener datos del pago seleccionado
        date_str = self.table.item(r, 0).text()
        concept = self.table.item(r, 1).text()
        amount_str = self.table.item(r, 2).text()
        
        reply = QMessageBox.question(
            self, "Confirmar Eliminación", 
            f"¿Eliminar este pago?\n\n" +
            f"📅 Fecha: {date_str}\n" +
            f"💳 Concepto: {concept}\n" +
            f"💰 Monto: {amount_str}\n\n" +
            "⚠️ Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            # Obtener el pago desde la base de datos
            payments = (session.query(Payment)
                       .filter(Payment.is_provider == 0)
                       .order_by(Payment.date.desc())
                       .all())
            
            if r < len(payments):
                pay = payments[r]
                payment_info = f"{pay.category} - ₡{int(pay.amount):,}"
                
                session.delete(pay)
                session.commit()
                
                print(f"✅ Pago eliminado: {payment_info}")
                QMessageBox.information(self, "Pago Eliminado", 
                                       "✅ Pago eliminado correctamente")
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", "No se pudo encontrar el pago seleccionado")
                self.refresh()
                
        except Exception as e:
            session.rollback()
            print(f"❌ Error eliminando pago: {e}")
            QMessageBox.critical(self, "Error", f"Error eliminando pago: {str(e)}")
            self.refresh()

    def import_csv(self):
        """✅ IMPORTAR CSV CON MEJOR UX Y PROGRESO"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar Pagos desde CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
            
        # Mostrar formato esperado
        QMessageBox.information(self, "Formato de Importación", 
                               "Formato esperado del CSV:\n\n" +
                               "Fecha;Concepto;Monto\n" +
                               "2024-01-15 10:30;Servicios públicos;25000\n\n" +
                               "📝 Formatos de fecha soportados:\n" +
                               "• YYYY-MM-DD HH:MM:SS\n" +
                               "• YYYY-MM-DD\n" +
                               "• DD/MM/YYYY HH:MM:SS\n" +
                               "• DD/MM/YYYY\n" +
                               "• DD/MM/YY")
        
        reply = QMessageBox.question(
            self, "Confirmar Importación",
            "⚠️ Esto reemplazará todos los pagos generales existentes.\n\n¿Continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
            
        # Mostrar progreso
        progress_msg = QMessageBox(self)
        progress_msg.setWindowTitle("Importando...")
        progress_msg.setText("Importando pagos desde CSV...\n\nPor favor espere.")
        progress_msg.setStandardButtons(QMessageBox.NoButton)
        progress_msg.show()
        
        try:
            # Eliminar pagos existentes
            session.query(Payment).filter(Payment.is_provider == 0).delete()
            session.commit()

            new_amounts = []
            imported_count = 0
            
            with open(path, mode='r', encoding='utf-8-sig', newline='') as f:
                # Detectar delimitador automáticamente
                sample = f.read(8192)
                f.seek(0)
                delims = [';', ',', '\t']
                counts = {d: sample.count(d) for d in delims}
                delim = max(counts, key=counts.get)
                
                reader = csv.reader(f, delimiter=delim)
                try:
                    headers = next(reader)
                except StopIteration:
                    progress_msg.close()
                    QMessageBox.warning(self, "Archivo Vacío", "El archivo CSV está vacío")
                    return
                
                # Detectar columnas automáticamente
                norm = [unicodedata.normalize('NFKD', h).encode('ascii','ignore').decode('ascii').lower() 
                       for h in headers]
                
                def idx_match(keys):
                    for i, h in enumerate(norm):
                        for k in keys:
                            if k in h:
                                return i
                    return None
                
                date_i = idx_match(['fecha','date']) or 0
                concept_i = idx_match(['concepto','desc','descr','concept']) or 1
                amt_i = idx_match(['monto','amount','amt']) or 2

                for row_num, row in enumerate(reader, 2):  # Empezar en fila 2
                    if len(row) <= max(date_i, concept_i, amt_i):
                        continue
                        
                    raw_date = row[date_i].strip()
                    concept = row[concept_i].strip()
                    raw_amt = row[amt_i]
                    
                    # Parsear fecha
                    dt = None
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", 
                               "%d/%m/%Y", "%d/%m/%y"): 
                        try:
                            dt = datetime.strptime(raw_date, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if not dt:
                        print(f"⚠️ Fila {row_num}: fecha inválida '{raw_date}'")
                        continue
                        
                    if not concept:
                        print(f"⚠️ Fila {row_num}: concepto vacío")
                        continue
                    
                    # Limpiar monto
                    clean = re.sub(r"[^0-9\.,]", "", raw_amt)
                    if clean.count(',') > 0 and clean.count('.') > 1:
                        clean = clean.replace('.', '')
                    value = clean.replace(',', '.')
                    
                    try:
                        amt = float(value)
                        if amt <= 0:
                            continue
                    except ValueError:
                        print(f"⚠️ Fila {row_num}: monto inválido '{raw_amt}'")
                        continue
                    
                    # Crear pago
                    pay = Payment(date=dt, amount=amt, category=concept, is_provider=0)
                    session.add(pay)
                    new_amounts.append(amt)
                    imported_count += 1

            session.commit()
            progress_msg.close()
            
            # Emitir señales para todos los montos importados
            for amt in new_amounts:
                self.paymentDone.emit(amt)
                
            self.refresh()
            QMessageBox.information(
                self, "Importación Completada", 
                f"✅ Importación completada\n\n" +
                f"📊 {imported_count:,} pagos importados\n" +
                f"💰 Total: ₡{sum(new_amounts):,.0f}"
            )
            
        except Exception as e:
            if 'progress_msg' in locals():
                progress_msg.close()
            session.rollback()
            QMessageBox.critical(self, "Error de Importación", f"Error importando CSV: {str(e)}")

    def export_csv(self):
        """✅ EXPORTAR CSV CON MEJOR UX"""
        # Contar registros
        count = session.query(Payment).filter(Payment.is_provider == 0).count()
        
        if count == 0:
            QMessageBox.information(self, "Sin Datos", "No hay pagos generales para exportar")
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Pagos a CSV", 
            f"pagos_generales_{datetime.now().strftime('%Y%m%d')}.csv", 
            "CSV Files (*.csv)"
        )
        if not path:
            return
            
        # Mostrar progreso para exports grandes
        progress_msg = None
        if count > 500:
            progress_msg = QMessageBox(self)
            progress_msg.setWindowTitle("Exportando...")
            progress_msg.setText(f"Exportando {count:,} pagos...\n\nPor favor espere.")
            progress_msg.setStandardButtons(QMessageBox.NoButton)
            progress_msg.show()
            
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['Fecha', 'Concepto', 'Monto'])
                
                payments = session.query(Payment).filter(
                    Payment.is_provider == 0
                ).order_by(Payment.date.desc()).all()
                
                total_exported = 0
                total_amount = 0
                
                for p in payments:
                    writer.writerow([
                        p.date.strftime("%Y-%m-%d %H:%M:%S"),
                        p.category or "",
                        f"{p.amount:.0f}"
                    ])
                    total_exported += 1
                    total_amount += p.amount
                    
            if progress_msg:
                progress_msg.close()
                
            QMessageBox.information(self, "Exportación Completada", 
                                   f"✅ Exportación completada\n\n" +
                                   f"📁 Archivo: {path}\n" +
                                   f"📊 {total_exported:,} registros exportados\n" +
                                   f"💰 Total: ₡{total_amount:,.0f}")
            
        except Exception as e:
            if progress_msg:
                progress_msg.close()
            QMessageBox.critical(self, "Error de Exportación", f"Error exportando CSV: {str(e)}")

    def eventFilter(self, obj, event):
        """✅ Manejo de eventos del teclado"""
        if (obj is self.table and event.type() == QEvent.KeyPress and 
            event.key() == Qt.Key_Delete):
            self.delete_payment()
            return True
        return super().eventFilter(obj, event)