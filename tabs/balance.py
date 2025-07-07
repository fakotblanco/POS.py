# tabs/balance.py - VERSIÓN CON DISEÑO CONSISTENTE
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDateEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QAbstractItemView,
    QFileDialog, QMessageBox, QHeaderView, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, QDate, QEvent
from PySide6.QtGui import QFont, QColor
from db import session
from database_setup import Balance, Sale, SaleItem, Payment
from datetime import datetime
from sqlalchemy import func
import csv
import re

class BalanceTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(15)

        # ========== TÍTULO DE SECCIÓN ==========
        title = QLabel("📊 Balance y Resumen Financiero")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; margin: 10px 0;")
        self.layout().addWidget(title)

        # ========== CONTROLES DE RESUMEN DIARIO ==========
        summary_group = QGroupBox("📅 Resumen del Día Seleccionado")
        summary_group.setStyleSheet(
            """
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #495057;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                background-color: white;
            }
            """
        )
        summary_layout = QVBoxLayout(summary_group)
        summary_layout.setSpacing(15)

        # ========== SELECTOR DE FECHA Y MÉTRICAS ==========
        controls_layout = QGridLayout()
        controls_layout.setSpacing(15)

        # Selector de fecha con estilo consistente
        date_label = QLabel("📅 Fecha:")
        date_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057; padding: 5px;")
        
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet(
            """
            QDateEdit {
                min-height: 35px;
                font-size: 14px;
                background-color: #FAFAFA;
                padding: 8px 12px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                color: #333;
                font-weight: bold;
            }
            QDateEdit:focus {
                border: 2px solid #2196F3;
                background-color: white;
            }
            QDateEdit::drop-down {
                border: none;
                padding-right: 8px;
            }
            """
        )
        self.date_edit.dateChanged.connect(self._recompute)

        controls_layout.addWidget(date_label, 0, 0)
        controls_layout.addWidget(self.date_edit, 0, 1)

        # ========== MÉTRICAS CON DISEÑO MEJORADO ==========
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(10)

        # Estilo para labels de métricas
        metric_label_style = "font-size: 14px; font-weight: bold; color: #495057; padding: 8px;"
        metric_value_style = """
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px 15px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                background-color: #F8F9FA;
                color: #333;
                min-width: 120px;
            }
        """

        # Métricas con iconos y colores
        ventas_label = QLabel("💰 Ventas del Día:")
        ventas_label.setStyleSheet(metric_label_style)
        self.lbl_sales = QLabel("₡0")
        self.lbl_sales.setStyleSheet(metric_value_style.replace("#F8F9FA", "#E8F5E8"))  # Verde claro
        metrics_layout.addWidget(ventas_label, 0, 0)
        metrics_layout.addWidget(self.lbl_sales, 0, 1)

        compras_label = QLabel("🏪 Pagos a Proveedores:")
        compras_label.setStyleSheet(metric_label_style)
        self.lbl_entries = QLabel("₡0")
        self.lbl_entries.setStyleSheet(metric_value_style.replace("#F8F9FA", "#FFF3E0"))  # Amarillo claro
        metrics_layout.addWidget(compras_label, 0, 2)
        metrics_layout.addWidget(self.lbl_entries, 0, 3)

        pagos_label = QLabel("💳 Pagos Generales:")
        pagos_label.setStyleSheet(metric_label_style)
        self.lbl_payments = QLabel("₡0")
        self.lbl_payments.setStyleSheet(metric_value_style.replace("#F8F9FA", "#FFEBEE"))  # Rojo claro
        metrics_layout.addWidget(pagos_label, 1, 0)
        metrics_layout.addWidget(self.lbl_payments, 1, 1)

        saldo_label = QLabel("📈 Saldo Neto:")
        saldo_label.setStyleSheet(metric_label_style)
        self.lbl_balance = QLabel("₡0")
        self.lbl_balance.setStyleSheet(metric_value_style.replace("#F8F9FA", "#E3F2FD"))  # Azul claro
        metrics_layout.addWidget(saldo_label, 1, 2)
        metrics_layout.addWidget(self.lbl_balance, 1, 3)

        summary_layout.addLayout(controls_layout)
        summary_layout.addLayout(metrics_layout)

        # ========== BOTONES CON DISEÑO CONSISTENTE ==========
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        # Botón guardar (azul)
        self.btn_save = QPushButton("💾 Guardar Registro")
        self.btn_save.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 130px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            """
        )

        # Botones secundarios (grises)
        secondary_style = """
            QPushButton {
                background-color: #6C757D;
                color: white;
                padding: 10px 16px;
                font-size: 14px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                min-width: 130px;
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

        buttons_layout.addWidget(self.btn_save)
        buttons_layout.addWidget(self.btn_import)
        buttons_layout.addWidget(self.btn_export)
        buttons_layout.addStretch()

        summary_layout.addLayout(buttons_layout)
        self.layout().addWidget(summary_group)

        # ========== HISTORIAL CON DISEÑO CONSISTENTE ==========
        history_title = QLabel("📋 Historial de Balances")
        history_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin: 20px 0 10px 0;")
        self.layout().addWidget(history_title)

        # ========== TABLA CON DISEÑO CONSISTENTE ==========
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Fecha", "Ventas", "Pagos Proveedores", "Pagos Generales", "Saldo Neto"
        ])

        # Configuración de columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Ventas
        header.setSectionResizeMode(2, QHeaderView.Stretch)          # Proveedores
        header.setSectionResizeMode(3, QHeaderView.Stretch)          # Pagos
        header.setSectionResizeMode(4, QHeaderView.Stretch)          # Saldo

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

        # Configuración de edición y selección
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.installEventFilter(self)
        
        # Fuente optimizada
        table_font = QFont()
        table_font.setPointSize(14)
        self.table.setFont(table_font)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setHighlightSections(False)

        self.layout().addWidget(self.table)

        # ========== CONEXIONES ==========
        self.btn_save.clicked.connect(self._save_record)
        self.btn_import.clicked.connect(self._import_csv)
        self.btn_export.clicked.connect(self._export_csv)

        # ========== INICIALIZACIÓN ==========
        Balance.__table__.create(session.bind, checkfirst=True)
        self._recompute()
        self._load_history()

    def _recompute(self):
        """✅ Recalcular métricas del día seleccionado"""
        try:
            d = self.date_edit.date().toPython()

            # Calcular ventas del día
            ventas = (
                session.query(func.coalesce(func.sum(SaleItem.price * SaleItem.quantity), 0))
                       .select_from(SaleItem)
                       .join(Sale, SaleItem.sale_id == Sale.id)
                       .filter(func.date(Sale.date) == d)
                       .scalar() or 0
            )

            # Calcular pagos a proveedores del día
            compras = (
                session.query(func.coalesce(func.sum(Payment.amount), 0))
                       .filter(func.date(Payment.date) == d,
                               Payment.is_provider == True)
                       .scalar() or 0
            )

            # Calcular pagos generales del día
            pagos = (
                session.query(func.coalesce(func.sum(Payment.amount), 0))
                       .filter(func.date(Payment.date) == d,
                               Payment.is_provider == False)
                       .scalar() or 0
            )

            # Calcular saldo neto
            saldo = ventas - compras - pagos

            # Formatear y actualizar labels
            self.lbl_sales.setText(f"₡{int(ventas):,}")
            self.lbl_entries.setText(f"₡{int(compras):,}")
            self.lbl_payments.setText(f"₡{int(pagos):,}")
            
            # Cambiar color del saldo según si es positivo o negativo
            if saldo >= 0:
                self.lbl_balance.setStyleSheet(
                    self.lbl_balance.styleSheet().replace("#E3F2FD", "#E8F5E8")  # Verde si positivo
                )
            else:
                self.lbl_balance.setStyleSheet(
                    self.lbl_balance.styleSheet().replace("#E8F5E8", "#FFEBEE")  # Rojo si negativo
                )
            
            self.lbl_balance.setText(f"₡{int(saldo):,}")

        except Exception as e:
            print(f"❌ Error recalculando métricas: {e}")

    def on_sale(self, ventas, compras, pagos, saldo):
        """✅ Callback cuando se realiza una venta"""
        self._recompute()

    def on_payment(self, amount):
        """✅ Callback cuando se realiza un pago"""
        self._recompute()

    def _save_record(self):
        """✅ Guardar registro con validaciones y confirmación"""
        try:
            d = self.date_edit.date().toPython()
            
            # Verificar si ya existe un registro para esta fecha
            existing = session.query(Balance).filter_by(date=d).first()
            
            if existing:
                reply = QMessageBox.question(
                    self, "Registro Existente",
                    f"Ya existe un registro para {d.strftime('%Y-%m-%d')}.\n\n¿Sobrescribir?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
                session.delete(existing)

            # Extraer valores de los labels
            ventas = int(self.lbl_sales.text().replace('₡','').replace(',',''))
            compras = int(self.lbl_entries.text().replace('₡','').replace(',',''))
            pagos = int(self.lbl_payments.text().replace('₡','').replace(',',''))
            saldo = ventas - compras - pagos

            # Crear nuevo registro
            rec = Balance(
                date=d,
                total_sales=ventas,
                total_entries=compras,
                total_payments=pagos,
                total_providers=0,  # Campo legacy
                balance=saldo
            )
            session.add(rec)
            session.commit()
            
            QMessageBox.information(self, "Registro Guardado", 
                                   f"✅ Balance guardado correctamente\n\n" +
                                   f"📅 Fecha: {d.strftime('%Y-%m-%d')}\n" +
                                   f"💰 Saldo: ₡{int(saldo):,}")
            
            self._load_history()
            print(f"✅ Registro de balance guardado: {d.strftime('%Y-%m-%d')}")

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Error guardando registro: {str(e)}")

    def _load_history(self):
        """✅ Cargar historial con resaltado visual"""
        self.table.setRowCount(0)
        try:
            records = session.query(Balance).order_by(Balance.date.desc()).all()
            
            for rec in records:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Crear items con formato
                date_item = QTableWidgetItem(rec.date.strftime("%Y-%m-%d"))
                sales_item = QTableWidgetItem(f"₡{int(rec.total_sales):,}")
                entries_item = QTableWidgetItem(f"₡{int(rec.total_entries):,}")
                payments_item = QTableWidgetItem(f"₡{int(rec.total_payments):,}")
                balance_item = QTableWidgetItem(f"₡{int(rec.balance):,}")
                
                # Resaltar saldo según si es positivo o negativo
                if rec.balance >= 0:
                    balance_item.setBackground(QColor("#E8F5E8"))  # Verde claro
                    balance_item.setForeground(QColor("#2E7D2E"))  # Verde oscuro
                else:
                    balance_item.setBackground(QColor("#FFEBEE"))  # Rojo claro
                    balance_item.setForeground(QColor("#C62828"))  # Rojo oscuro
                
                # Resaltar ventas altas
                if rec.total_sales > 100000:  # Más de 100k
                    sales_item.setBackground(QColor("#E8F5E8"))
                    sales_item.setForeground(QColor("#2E7D2E"))
                
                self.table.setItem(row, 0, date_item)
                self.table.setItem(row, 1, sales_item)
                self.table.setItem(row, 2, entries_item)
                self.table.setItem(row, 3, payments_item)
                self.table.setItem(row, 4, balance_item)

        except Exception as e:
            print(f"❌ Error cargando historial: {e}")

    def _import_csv(self):
        """✅ Importar CSV con mejor UX y progreso"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar Balance desde CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return

        # Mostrar formato esperado
        QMessageBox.information(self, "Formato de Importación", 
                               "Formato esperado del CSV:\n\n" +
                               "Fecha;Ventas;Compras;Pagos;Saldo\n" +
                               "2024-01-15;150000;25000;10000;115000\n\n" +
                               "📝 Formatos de fecha soportados:\n" +
                               "• YYYY-MM-DD\n" +
                               "• DD/MM/YYYY\n" +
                               "• DD/MM/YY")

        reply = QMessageBox.question(
            self, "Confirmar Importación",
            "⚠️ Esto reemplazará todos los registros de balance existentes.\n\n¿Continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # Mostrar progreso
        progress_msg = QMessageBox(self)
        progress_msg.setWindowTitle("Importando...")
        progress_msg.setText("Importando registros de balance...\n\nPor favor espere.")
        progress_msg.setStandardButtons(QMessageBox.NoButton)
        progress_msg.show()

        try:
            # Borrar registros existentes
            session.query(Balance).delete()
            session.commit()

            imported = 0
            with open(path, mode='r', encoding='utf-8-sig', newline='') as f:
                # Detectar delimitador automáticamente
                sample = f.read(8192)
                f.seek(0)
                delims = [';', ',', '\t']
                counts = {d: sample.count(d) for d in delims}
                delim = max(counts, key=counts.get)
                
                reader = csv.reader(f, delimiter=delim)
                try:
                    next(reader)  # Saltar encabezado
                except StopIteration:
                    progress_msg.close()
                    QMessageBox.warning(self, "Archivo Vacío", "El archivo CSV está vacío")
                    return

                for row_num, row in enumerate(reader, 2):
                    if len(row) < 5:
                        continue
                        
                    raw_date, raw_sales, raw_entries, raw_payments, raw_balance = row[:5]
                    
                    # Parsear fecha
                    d = None
                    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
                        try:
                            d = datetime.strptime(raw_date.strip(), fmt).date()
                            break
                        except ValueError:
                            continue
                    
                    if not d:
                        print(f"⚠️ Fila {row_num}: fecha inválida '{raw_date}'")
                        continue

                    # Función para limpiar números
                    def clean_num(s):
                        s = re.sub(r"[^0-9\.,]", "", s)
                        if s.count(',') > 0 and s.count('.') > 1:
                            s = s.replace('.', '')
                        return float(s.replace(',', '.')) if s else 0

                    try:
                        s = clean_num(raw_sales)
                        e = clean_num(raw_entries)
                        p = clean_num(raw_payments)
                        b = clean_num(raw_balance)
                    except ValueError:
                        print(f"⚠️ Fila {row_num}: valores numéricos inválidos")
                        continue

                    # Crear registro
                    session.add(Balance(
                        date=d,
                        total_sales=s,
                        total_entries=e,
                        total_payments=p,
                        total_providers=0,
                        balance=b
                    ))
                    imported += 1

            session.commit()
            progress_msg.close()
            
            self._load_history()
            QMessageBox.information(
                self, "Importación Completada", 
                f"✅ Importación completada\n\n" +
                f"📊 {imported:,} registros importados"
            )

        except Exception as e:
            if 'progress_msg' in locals():
                progress_msg.close()
            session.rollback()
            QMessageBox.critical(self, "Error de Importación", f"Error importando CSV: {str(e)}")

    def _export_csv(self):
        """✅ Exportar CSV con mejor UX"""
        # Contar registros
        count = session.query(Balance).count()
        
        if count == 0:
            QMessageBox.information(self, "Sin Datos", "No hay registros de balance para exportar")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Balance a CSV", 
            f"balance_{datetime.now().strftime('%Y%m%d')}.csv", 
            "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['Fecha', 'Ventas', 'Compras', 'Pagos', 'Saldo'])
                
                total_sales = total_entries = total_payments = total_balance = 0
                
                for rec in session.query(Balance).order_by(Balance.date.desc()).all():
                    writer.writerow([
                        rec.date.strftime("%Y-%m-%d"),
                        f"{rec.total_sales:.0f}",
                        f"{rec.total_entries:.0f}",
                        f"{rec.total_payments:.0f}",
                        f"{rec.balance:.0f}"
                    ])
                    total_sales += rec.total_sales
                    total_entries += rec.total_entries
                    total_payments += rec.total_payments
                    total_balance += rec.balance

            QMessageBox.information(self, "Exportación Completada", 
                                   f"✅ Exportación completada\n\n" +
                                   f"📁 Archivo: {path}\n" +
                                   f"📊 {count:,} registros exportados\n" +
                                   f"💰 Total ventas: ₡{total_sales:,.0f}\n" +
                                   f"📈 Balance acumulado: ₡{total_balance:,.0f}")

        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"Error exportando CSV: {str(e)}")

    def eventFilter(self, obj, event):
        """✅ Manejo de eventos con confirmación mejorada"""
        if (obj is self.table and event.type() == QEvent.KeyPress and 
            event.key() == Qt.Key_Delete):
            row = self.table.currentRow()
            if row >= 0:
                # Obtener información del registro
                date_text = self.table.item(row, 0).text()
                balance_text = self.table.item(row, 4).text()
                
                reply = QMessageBox.question(
                    self, "Eliminar Registro de Balance", 
                    f"¿Eliminar este registro?\n\n" +
                    f"📅 Fecha: {date_text}\n" +
                    f"💰 Saldo: {balance_text}\n\n" +
                    "⚠️ Esta acción no se puede deshacer.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    try:
                        recs = session.query(Balance).order_by(Balance.date.desc()).all()
                        if row < len(recs):
                            rec = recs[row]
                            session.delete(rec)
                            session.commit()
                            self._load_history()
                            
                            QMessageBox.information(self, "Registro Eliminado", 
                                                   "✅ Registro eliminado correctamente")
                            print(f"✅ Registro de balance eliminado: {date_text}")
                        
                    except Exception as e:
                        session.rollback()
                        QMessageBox.critical(self, "Error", f"Error eliminando registro: {str(e)}")
            return True
        return super().eventFilter(obj, event)