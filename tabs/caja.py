# tabs/caja.py - VERSIÓN CON DISEÑO CONSISTENTE
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton, 
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QMessageBox,
    QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QFont
from datetime import datetime
from db import session
from database_setup import Payment, Shift
from sqlalchemy import func

class CajaTab(QWidget):
    def __init__(self):
        super().__init__()
        self.active = False
        self.shift_start_time = None
        self.turn_sales = 0.0

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # ========== TÍTULO DE SECCIÓN ==========
        title = QLabel("💰 Control de Caja y Turnos")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; margin: 10px 0;")
        layout.addWidget(title)

        # ========== CONTROLES DE TURNO CON DISEÑO AGRUPADO ==========
        shift_group = QGroupBox("🕐 Control de Turno")
        shift_group.setStyleSheet(
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
        shift_layout = QVBoxLayout(shift_group)
        shift_layout.setSpacing(15)

        # ========== ENTRADAS DE DINERO CON DISEÑO GRID ==========
        money_layout = QGridLayout()
        money_layout.setSpacing(10)

        # Estilo consistente para spinboxes
        spinbox_style = """
            QDoubleSpinBox {
                min-height: 35px;
                font-size: 14px;
                background-color: #FAFAFA;
                padding: 8px 12px;
                border: 2px solid #E0E0E0;
                border-radius: 6px;
                color: #333;
                font-weight: bold;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #2196F3;
                background-color: white;
            }
        """

        # Crear y configurar spinboxes con incremento de ₡1000
        self.caja = QDoubleSpinBox()
        self.caja.setRange(0, 1_000_000)
        self.caja.setDecimals(0)
        self.caja.setPrefix("₡")
        self.caja.setSingleStep(1000)  # ✅ Incremento de ₡1000
        self.caja.setStyleSheet(spinbox_style)

        self.plata = QDoubleSpinBox()
        self.plata.setRange(0, 1_000_000)
        self.plata.setDecimals(0)
        self.plata.setPrefix("₡")
        self.plata.setSingleStep(1000)  # ✅ Incremento de ₡1000
        self.plata.setStyleSheet(spinbox_style)

        self.sinpes = QDoubleSpinBox()
        self.sinpes.setRange(0, 1_000_000)
        self.sinpes.setDecimals(0)
        self.sinpes.setPrefix("₡")
        self.sinpes.setSingleStep(1000)  # ✅ Incremento de ₡1000
        self.sinpes.setStyleSheet(spinbox_style)

        self.dataf = QDoubleSpinBox()
        self.dataf.setRange(0, 1_000_000)
        self.dataf.setDecimals(0)
        self.dataf.setPrefix("₡")
        self.dataf.setSingleStep(1000)  # ✅ Incremento de ₡1000
        self.dataf.setStyleSheet(spinbox_style)

        # Etiquetas con iconos
        label_style = "font-size: 14px; font-weight: bold; color: #495057; padding: 5px;"

        caja_label = QLabel("💵 Efectivo en Caja:")
        caja_label.setStyleSheet(label_style)
        money_layout.addWidget(caja_label, 0, 0)
        money_layout.addWidget(self.caja, 0, 1)

        plata_label = QLabel("🏪 Plata (Cambio):")
        plata_label.setStyleSheet(label_style)
        money_layout.addWidget(plata_label, 0, 2)
        money_layout.addWidget(self.plata, 0, 3)

        sinpes_label = QLabel("📱 SINPE Móvil:")
        sinpes_label.setStyleSheet(label_style)
        money_layout.addWidget(sinpes_label, 1, 0)
        money_layout.addWidget(self.sinpes, 1, 1)

        dataf_label = QLabel("💳 Datafast (Tarjeta):")
        dataf_label.setStyleSheet(label_style)
        money_layout.addWidget(dataf_label, 1, 2)
        money_layout.addWidget(self.dataf, 1, 3)

        shift_layout.addLayout(money_layout)

        # ========== BOTONES DE TURNO CON DISEÑO CONSISTENTE ==========
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        # Botón iniciar turno (verde)
        self.btn_start = QPushButton("🕐 Iniciar Turno")
        self.btn_start.setStyleSheet(
            """
            QPushButton {
                background-color: #28A745;
                color: white;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                min-width: 150px;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1E7E34;
            }
            QPushButton:disabled {
                background-color: #6C757D;
                color: #ADB5BD;
            }
            """
        )

        # Botón cerrar turno (rojo)
        self.btn_close = QPushButton("🔒 Cerrar Turno")
        self.btn_close.setEnabled(False)
        self.btn_close.setStyleSheet(
            """
            QPushButton {
                background-color: #DC3545;
                color: white;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                min-width: 150px;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:pressed {
                background-color: #BD2130;
            }
            QPushButton:disabled {
                background-color: #E0E0E0;
                color: #999;
            }
            """
        )

        buttons_layout.addWidget(self.btn_start)
        buttons_layout.addWidget(self.btn_close)
        buttons_layout.addStretch()

        shift_layout.addLayout(buttons_layout)
        layout.addWidget(shift_group)

        # ========== HISTORIAL CON DISEÑO CONSISTENTE ==========
        history_title = QLabel("📋 Historial de Cierres de Caja")
        history_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin: 20px 0 10px 0;")
        layout.addWidget(history_title)

        # ========== TABLA CON DISEÑO CONSISTENTE ==========
        self.table = QTableWidget()
        headers = [
            "Fecha y Hora", "Efectivo", "Plata", "SINPE", "Datafast", 
            "Ventas", "Pago Proveedores", "Pagos Generales", "Total Final"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        # Configuración de columnas
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Efectivo
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Plata
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # SINPE
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Datafast
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Ventas
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Prov
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Pagos
        header.setSectionResizeMode(8, QHeaderView.Stretch)           # Total se expande

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

        layout.addWidget(self.table)

        # ========== CONEXIONES ==========
        self.btn_start.clicked.connect(self._start)
        self.btn_close.clicked.connect(self._close)

        # ✅ CARGAR HISTORIAL Y ESTADO DEL TURNO AL INICIALIZAR
        self.load_history()
        self.restore_shift_state()

    def load_history(self):
        """✅ Cargar historial desde la base de datos con mejor UX"""
        self.table.setRowCount(0)
        try:
            # Buscar turnos cerrados (que tienen fecha de fin)
            shifts = (
                session.query(Shift)
                .filter(Shift.end.isnot(None))
                .order_by(Shift.end.desc())
                .limit(50)  # Mostrar últimos 50 cierres
                .all()
            )
            
            for shift in shifts:
                # Calcular datos del turno
                shift_start = shift.start
                shift_end = shift.end
                
                # Buscar pagos a proveedores en ese turno
                prov_payments = session.query(func.coalesce(func.sum(Payment.amount), 0.0)) \
                              .filter(
                                  Payment.is_provider == True,
                                  Payment.date >= shift_start,
                                  Payment.date <= shift_end
                              ).scalar() or 0
                
                # Buscar pagos genéricos en ese turno
                generic_payments = session.query(func.coalesce(func.sum(Payment.amount), 0.0)) \
                                 .filter(
                                     Payment.is_provider == False,
                                     Payment.date >= shift_start,
                                     Payment.date <= shift_end
                                 ).scalar() or 0
                
                # Parsear datos guardados en el user field (formato: caja,plata,sinpes,dataf,ventas,total)
                user_data = shift.user.split(',') if ',' in shift.user else ['0','0','0','0','0','0']
                
                try:
                    caja = float(user_data[0])
                    plata = float(user_data[1]) 
                    sinpes = float(user_data[2])
                    dataf = float(user_data[3])
                    ventas = float(user_data[4])
                    total = float(user_data[5])
                except (ValueError, IndexError):
                    # Si hay error en los datos, usar valores por defecto
                    caja = plata = sinpes = dataf = ventas = total = 0
                
                # Insertar fila en la tabla
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                # Formatear valores con colores para totales
                vals = [
                    shift_end.strftime("%Y-%m-%d %H:%M"),
                    f"₡{int(caja):,}",
                    f"₡{int(plata):,}",
                    f"₡{int(sinpes):,}",
                    f"₡{int(dataf):,}",
                    f"₡{int(ventas):,}",
                    f"₡{int(prov_payments):,}",
                    f"₡{int(generic_payments):,}",
                    f"₡{int(total):,}"
                ]
                
                for i, v in enumerate(vals):
                    item = QTableWidgetItem(str(v))
                    
                    # Resaltar columnas importantes
                    if i == 5:  # Ventas
                        item.setBackground(Qt.GlobalColor.green)
                        item.setForeground(Qt.GlobalColor.white)
                    elif i == 8:  # Total final
                        if total >= 0:
                            item.setBackground(Qt.GlobalColor.blue)
                            item.setForeground(Qt.GlobalColor.white)
                        else:
                            item.setBackground(Qt.GlobalColor.yellow)
                            item.setForeground(Qt.GlobalColor.black)
                    
                    self.table.setItem(row, i, item)
                    
        except Exception as e:
            print(f"❌ Error cargando historial de caja: {e}")
            QMessageBox.warning(self, "Error", f"Error cargando historial: {str(e)}")

    def restore_shift_state(self):
        """✅ Restaurar estado del turno al iniciar programa"""
        try:
            # Buscar si hay un turno activo (sin fecha de fin)
            active_shift = (
                session.query(Shift)
                .filter(Shift.end.is_(None))
                .order_by(Shift.start.desc())
                .first()
            )
            
            if active_shift:
                # Hay un turno activo, restaurar estado
                self.active = True
                self.shift_start_time = active_shift.start
                
                # Calcular ventas acumuladas del turno
                from database_setup import Sale, SaleItem
                ventas_turno = (
                    session.query(func.coalesce(func.sum(SaleItem.price * SaleItem.quantity), 0.0))
                    .join(Sale, SaleItem.sale_id == Sale.id)
                    .filter(Sale.date >= active_shift.start.date())
                    .scalar() or 0
                )
                
                self.turn_sales = ventas_turno
                
                # Actualizar interfaz
                self.btn_start.setEnabled(False)
                self.btn_start.setText("🕐 Turno Activo")
                self.btn_close.setEnabled(True)
                
                # Mostrar información del turno activo
                turno_info = f"Turno iniciado: {active_shift.start.strftime('%Y-%m-%d %H:%M')}"
                QMessageBox.information(self, "Turno Activo Detectado", 
                                       f"✅ Se ha restaurado un turno activo\n\n" +
                                       f"🕐 {turno_info}\n" +
                                       f"💰 Ventas acumuladas: ₡{ventas_turno:,.0f}")
                
                print(f"✅ Turno restaurado: iniciado {active_shift.start.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Ventas acumuladas: ₡{ventas_turno:,.0f}")
                
            else:
                # No hay turno activo
                print("ℹ️ No hay turno activo pendiente")
                
        except Exception as e:
            print(f"❌ Error restaurando estado del turno: {e}")
            QMessageBox.warning(self, "Error", f"Error restaurando turno: {str(e)}")

    def save_shift_state(self):
        """✅ Guardar estado del turno activo"""
        try:
            if self.active and self.shift_start_time:
                # Buscar si ya existe un registro del turno activo
                existing_shift = (
                    session.query(Shift)
                    .filter(
                        Shift.start == self.shift_start_time,
                        Shift.end.is_(None)
                    )
                    .first()
                )
                
                if not existing_shift:
                    # Crear nuevo registro de turno activo
                    shift_record = Shift(
                        user="ACTIVE_SHIFT",  # Marcador especial
                        start=self.shift_start_time,
                        end=None  # Sin fecha de fin = turno activo
                    )
                    session.add(shift_record)
                    session.commit()
                    print(f"✅ Estado del turno guardado")
                    
        except Exception as e:
            print(f"❌ Error guardando estado del turno: {e}")

    def clear_active_shift(self):
        """✅ Limpiar registro de turno activo"""
        try:
            # Eliminar cualquier turno activo sin cerrar
            session.query(Shift).filter(Shift.end.is_(None)).delete()
            session.commit()
            print(f"✅ Registro de turno activo eliminado")
        except Exception as e:
            print(f"❌ Error limpiando turno activo: {e}")

    def eventFilter(self, obj, event):
        """✅ Manejo de eventos con confirmación mejorada"""
        if (obj is self.table and event.type() == QEvent.KeyPress and 
            event.key() == Qt.Key_Delete):
            r = self.table.currentRow()
            if r >= 0:
                # Obtener información del cierre
                date_text = self.table.item(r, 0).text()
                total_text = self.table.item(r, 8).text()
                
                reply = QMessageBox.question(
                    self, "Eliminar Cierre de Caja", 
                    f"¿Eliminar este cierre de caja?\n\n" +
                    f"📅 Fecha: {date_text}\n" +
                    f"💰 Total: {total_text}\n\n" +
                    "⚠️ Esta acción no se puede deshacer.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    try:
                        # Buscar y eliminar el shift correspondiente de la base de datos
                        shift_date = datetime.strptime(date_text, "%Y-%m-%d %H:%M")
                        shift = session.query(Shift).filter_by(end=shift_date).first()
                        
                        if shift:
                            session.delete(shift)
                            session.commit()
                            print(f"✅ Cierre eliminado de la base de datos: {date_text}")
                        
                        self.table.removeRow(r)
                        QMessageBox.information(self, "Cierre Eliminado", 
                                               "✅ Cierre de caja eliminado correctamente")
                        
                    except Exception as e:
                        print(f"❌ Error eliminando cierre: {e}")
                        QMessageBox.warning(self, "Error", f"Error eliminando cierre: {str(e)}")
            return True
        return super().eventFilter(obj, event)

    def _start(self):
        """✅ Iniciar turno con confirmación y validaciones"""
        if not self.active:
            reply = QMessageBox.question(
                self, "Iniciar Nuevo Turno",
                "¿Iniciar un nuevo turno de caja?\n\n" +
                "🕐 Se registrará la hora actual como inicio del turno.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.shift_start_time = datetime.now()
                self.turn_sales = 0.0
                self.active = True
                self.btn_start.setEnabled(False)
                self.btn_start.setText("🕐 Turno Activo")
                self.btn_close.setEnabled(True)
                
                # ✅ GUARDAR ESTADO DEL TURNO
                self.save_shift_state()
                
                QMessageBox.information(self, "Turno Iniciado", 
                                       f"✅ Turno iniciado correctamente\n\n" +
                                       f"🕐 Hora de inicio: {self.shift_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                print(f"✅ Turno iniciado: {self.shift_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    def _close(self):
        """✅ Cerrar turno con validaciones y confirmación"""
        if not self.active:
            QMessageBox.information(self, "Sin Turno Activo", 
                                   "No hay un turno activo para cerrar")
            return
            
        # Validar que se hayan ingresado los montos
        if (self.caja.value() == 0 and self.plata.value() == 0 and 
            self.sinpes.value() == 0 and self.dataf.value() == 0):
            reply = QMessageBox.question(
                self, "Montos en Cero",
                "Todos los montos están en cero.\n\n¿Continuar con el cierre?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        shift_end_time = datetime.now()

        # Calcular totales del turno
        try:
            # Sumar sólo los pagos a proveedores del turno
            prov = session.query(func.coalesce(func.sum(Payment.amount), 0.0)) \
                          .filter(
                              Payment.is_provider == True,
                              Payment.date >= self.shift_start_time,
                              Payment.date <= shift_end_time
                          ).scalar() or 0

            # Sumar sólo los pagos genéricos del turno
            pagos = session.query(func.coalesce(func.sum(Payment.amount), 0.0)) \
                            .filter(
                                Payment.is_provider == False,
                                Payment.date >= self.shift_start_time,
                                Payment.date <= shift_end_time
                            ).scalar() or 0

            ventas = self.turn_sales

            fe = {
                'c': self.caja.value(),
                'p': self.plata.value(),
                's': self.sinpes.value(),
                'd': self.dataf.value()
            }

            total = fe['c'] + fe['p'] - fe['s'] - fe['d'] + ventas - prov - pagos
            ts = shift_end_time.strftime("%Y-%m-%d %H:%M")

            # Mostrar resumen antes de confirmar
            resumen = (
                f"💰 RESUMEN DEL CIERRE\n\n" +
                f"🕐 Duración del turno:\n" +
                f"   Inicio: {self.shift_start_time.strftime('%Y-%m-%d %H:%M')}\n" +
                f"   Fin: {ts}\n\n" +
                f"💵 Dinero en caja:\n" +
                f"   Efectivo: ₡{int(fe['c']):,}\n" +
                f"   Plata: ₡{int(fe['p']):,}\n" +
                f"   SINPE: ₡{int(fe['s']):,}\n" +
                f"   Datafast: ₡{int(fe['d']):,}\n\n" +
                f"📊 Movimientos del turno:\n" +
                f"   Ventas: ₡{int(ventas):,}\n" +
                f"   Pagos proveedores: ₡{int(prov):,}\n" +
                f"   Pagos generales: ₡{int(pagos):,}\n\n" +
                f"🎯 TOTAL FINAL: ₡{int(total):,}"
            )

            reply = QMessageBox.question(
                self, "Confirmar Cierre de Turno",
                f"{resumen}\n\n¿Confirmar el cierre?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return

            # ✅ GUARDAR EN BASE DE DATOS
            try:
                # Formatear datos para guardar: caja,plata,sinpes,dataf,ventas,total
                user_data = f"{fe['c']},{fe['p']},{fe['s']},{fe['d']},{ventas},{total}"
                
                shift_record = Shift(
                    user=user_data,  # Guardamos los datos en este campo
                    start=self.shift_start_time,
                    end=shift_end_time
                )
                session.add(shift_record)
                session.commit()
                print(f"✅ Cierre de caja guardado: {ts}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error guardando cierre: {str(e)}")
                return

            # Reset de inputs y estado
            for w in (self.caja, self.plata, self.sinpes, self.dataf):
                w.setValue(0)
            self.active = False
            self.btn_start.setEnabled(True)
            self.btn_start.setText("🕐 Iniciar Turno")
            self.btn_close.setEnabled(False)
            
            # ✅ LIMPIAR REGISTRO DE TURNO ACTIVO
            self.clear_active_shift()
            
            # Recargar historial para mostrar el nuevo cierre
            self.load_history()
            
            QMessageBox.information(self, "Turno Cerrado", 
                                   f"✅ Turno cerrado correctamente\n\n" +
                                   f"💰 Total final: ₡{int(total):,}")
            
            print(f"✅ Turno cerrado correctamente")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cerrando turno: {str(e)}")

    def on_sale(self, ventas, compras, pagos, saldo):
        """✅ Callback cuando se realiza una venta"""
        if self.active:
            self.turn_sales += ventas
            print(f"🛒 Venta registrada: ₡{ventas:,} (Total turno: ₡{self.turn_sales:,})")

    # Cálculo directo en BD, slots vacíos
    def on_provider_payment(self, amount):
        """Se llama cuando se AGREGA un pago a proveedor"""
        if self.active:
            print(f"🏪 Pago a proveedor registrado: ₡{amount:,}")

    def on_generic_payment(self, amount):
        """Se llama cuando se AGREGA un pago genérico"""
        if self.active:
            print(f"💳 Pago genérico registrado: ₡{amount:,}")
    
    def on_payment_deleted(self, amount, is_provider=True):
        """✅ Se llama cuando se ELIMINA un pago"""
        if self.active and self.shift_start_time:
            tipo = 'proveedor' if is_provider else 'genérico'
            print(f"🔄 Pago eliminado durante turno activo: ₡{amount:,} ({tipo})")
            # Los pagos se recalcularán automáticamente al cerrar porque 
            # consultamos la base de datos en tiempo real