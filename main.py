import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtCore import Qt
from database_setup import init_db
from modules import (
    InventoryTab, FacturaTab, EntradasTab,
    ProveedoresTab, PagosTab, CajaTab, BalanceTab, AgranelTab
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configuración básica de la ventana
        self.setWindowTitle("POS Py - Dual Factura")
        self.resize(950, 650)
        
        # Configurar ícono
        try:
            self.setWindowIcon(QIcon("mi_icono.ico"))
        except:
            pass
        
        # Crear pestañas
        self.tabs = QTabWidget()
        self.setup_tabs()
        self.setup_connections()
        self.setup_keyboard_shortcuts()
        
        # Establecer widget central
        self.setCentralWidget(self.tabs)
        
    def setup_tabs(self):
        """✅ CONFIGURAR TODAS LAS PESTAÑAS CON NUMERACIÓN"""
        
        # ========== CREAR INSTANCIAS ==========
        self.factura1 = FacturaTab()
        self.factura1.setObjectName("Cliente 1")
        
        self.factura2 = FacturaTab() 
        self.factura2.setObjectName("Cliente 2")
        
        self.inventory = InventoryTab()
        self.entradas_tab = EntradasTab()
        self.proveedores = ProveedoresTab()
        self.pagos_tab = PagosTab()
        self.caja_tab = CajaTab()
        self.balance_tab = BalanceTab()
        self.agranel_tab = AgranelTab()
        
        # ========== AGREGAR PESTAÑAS NUMERADAS ==========
        self.tabs.addTab(self.factura1,    "1. Cliente 1")
        self.tabs.addTab(self.factura2,    "2. Cliente 2")
        self.tabs.addTab(self.inventory,   "3. Inventario")
        self.tabs.addTab(self.agranel_tab, "4. A granel")
        self.tabs.addTab(self.entradas_tab,"5. Entradas")
        self.tabs.addTab(self.proveedores, "6. Proveedores")
        self.tabs.addTab(self.pagos_tab,   "7. Pagos")
        self.tabs.addTab(self.caja_tab,    "8. Caja")
        self.tabs.addTab(self.balance_tab, "9. Balance")
        
        # Configurar tooltip con información de atajos
        shortcuts_info = (
            "⌨️ Atajos de teclado disponibles:\n\n"
            "F1 o Ctrl+1 → Cliente 1\n"
            "F2 o Ctrl+2 → Cliente 2\n"
            "F3 o Ctrl+3 → Inventario\n"
            "F4 o Ctrl+4 → A granel\n"
            "F5 o Ctrl+5 → Entradas\n"
            "F6 o Ctrl+6 → Proveedores\n"
            "F7 o Ctrl+7 → Pagos\n"
            "F8 o Ctrl+8 → Caja\n"
            "F9 o Ctrl+9 → Balance\n\n"
            "Tecla Del → Eliminar elemento seleccionado"
        )
        self.tabs.setToolTip(shortcuts_info)
        
    def setup_connections(self):
        """✅ CONFIGURAR CONEXIONES ENTRE PESTAÑAS"""
        
        # Conexiones para ambas facturas
        for factura in [self.factura1, self.factura2]:
            factura.saleDone.connect(self.balance_tab.on_sale)
            factura.saleDone.connect(self.caja_tab.on_sale)
            factura.saleDone.connect(self.inventory.load)
        
        # Conectar señal de pagos a Caja
        self.proveedores.providerDone.connect(self.caja_tab.on_provider_payment)
        self.pagos_tab.paymentDone.connect(self.caja_tab.on_generic_payment)
        
    def setup_keyboard_shortcuts(self):
        """✅ CONFIGURAR ATAJOS DE TECLADO GLOBALES"""
        
        # Lista de atajos F1-F9 y Ctrl+1-9
        shortcuts_data = [
            ("F1", "Ctrl+1", 0),   # Cliente 1
            ("F2", "Ctrl+2", 1),   # Cliente 2
            ("F3", "Ctrl+3", 2),   # Inventario
            ("F4", "Ctrl+4", 3),   # A granel
            ("F5", "Ctrl+5", 4),   # Entradas
            ("F6", "Ctrl+6", 5),   # Proveedores
            ("F7", "Ctrl+7", 6),   # Pagos
            ("F8", "Ctrl+8", 7),   # Caja
            ("F9", "Ctrl+9", 8),   # Balance
        ]
        
        # Crear atajos para cada pestaña
        for f_key, ctrl_key, tab_index in shortcuts_data:
            # Atajo con tecla F
            f_shortcut = QShortcut(QKeySequence(f_key), self)
            f_shortcut.activated.connect(lambda idx=tab_index: self.switch_to_tab(idx))
            
            # Atajo con Ctrl+número
            ctrl_shortcut = QShortcut(QKeySequence(ctrl_key), self)
            ctrl_shortcut.activated.connect(lambda idx=tab_index: self.switch_to_tab(idx))
        
        # Atajos adicionales útiles
        self.setup_additional_shortcuts()
        
    def setup_additional_shortcuts(self):
        """✅ ATAJOS ADICIONALES ÚTILES"""
        
        # Ctrl+Tab → Siguiente pestaña
        next_tab_shortcut = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_tab_shortcut.activated.connect(self.next_tab)
        
        # Ctrl+Shift+Tab → Pestaña anterior
        prev_tab_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_tab_shortcut.activated.connect(self.previous_tab)
        
        # Alt+Left → Pestaña anterior
        alt_left_shortcut = QShortcut(QKeySequence("Alt+Left"), self)
        alt_left_shortcut.activated.connect(self.previous_tab)
        
        # Alt+Right → Siguiente pestaña
        alt_right_shortcut = QShortcut(QKeySequence("Alt+Right"), self)
        alt_right_shortcut.activated.connect(self.next_tab)
        
    def switch_to_tab(self, index):
        """✅ CAMBIAR A PESTAÑA ESPECÍFICA"""
        if 0 <= index < self.tabs.count():
            self.tabs.setCurrentIndex(index)
            current_tab_name = self.tabs.tabText(index)
            print(f"📋 Cambiando a: {current_tab_name}")
            
    def next_tab(self):
        """✅ IR A LA SIGUIENTE PESTAÑA"""
        current = self.tabs.currentIndex()
        next_index = (current + 1) % self.tabs.count()
        self.switch_to_tab(next_index)
        
    def previous_tab(self):
        """✅ IR A LA PESTAÑA ANTERIOR"""
        current = self.tabs.currentIndex()
        prev_index = (current - 1) % self.tabs.count()
        self.switch_to_tab(prev_index)
        
    def keyPressEvent(self, event):
        """✅ MANEJO ADICIONAL DE EVENTOS DE TECLADO"""
        # Permitir que las pestañas manejen sus propios eventos
        super().keyPressEvent(event)

def main():
    # Inicializar la base de datos (crea tablas si no existen)
    init_db()
    
    app = QApplication(sys.argv)
    
    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar la aplicación
    sys.exit(app.exec())

if __name__ == "__main__":
    main()