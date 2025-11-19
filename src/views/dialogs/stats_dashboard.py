"""
Stats Dashboard - Dashboard completo de estadísticas con gráficos
Autor: Widget Sidebar Team
Fecha: 2025-01-23
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QTabWidget, QWidget, QFrame,
                              QTableWidget, QTableWidgetItem, QMessageBox,
                              QFileDialog, QTextEdit, QComboBox, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import sys
from pathlib import Path
from datetime import datetime

# Matplotlib imports
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.stats_manager import StatsManager
from core.favorites_manager import FavoritesManager
import logging

logger = logging.getLogger(__name__)

# Configurar estilo de matplotlib
plt.style.use('dark_background')


class StatsDashboard(QDialog):
    """Dashboard completo de estadísticas con gráficos"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stats_manager = StatsManager()
        self.favorites_manager = FavoritesManager()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Inicializar UI"""
        self.setWindowTitle("📊 Dashboard de Estadísticas")
        self.setMinimumSize(1000, 700)

        layout = QVBoxLayout(self)

        # Header
        header = QLabel("📊 Dashboard de Estadísticas")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)

        # Tabs principales
        self.tabs = QTabWidget()

        # Tab 1: Resumen
        self.summary_tab = self.create_summary_tab()
        self.tabs.addTab(self.summary_tab, "📋 Resumen")

        # Tab 2: Uso en el Tiempo
        self.usage_tab = self.create_usage_tab()
        self.tabs.addTab(self.usage_tab, "📈 Uso en el Tiempo")

        # Tab 3: Categorías
        self.categories_tab = self.create_categories_tab()
        self.tabs.addTab(self.categories_tab, "📁 Por Categoría")

        # Tab 4: Rendimiento
        self.performance_tab = self.create_performance_tab()
        self.tabs.addTab(self.performance_tab, "⚡ Rendimiento")

        # Tab 5: Salud del Widget
        self.health_tab = self.create_health_tab()
        self.tabs.addTab(self.health_tab, "🏥 Salud del Widget")

        layout.addWidget(self.tabs)

        # Botones
        btn_layout = QHBoxLayout()

        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.refresh_btn)

        self.export_btn = QPushButton("💾 Exportar Reporte")
        self.export_btn.clicked.connect(self.export_report)
        btn_layout.addWidget(self.export_btn)

        btn_layout.addStretch()

        self.close_btn = QPushButton("Cerrar")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        # Estilos
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #cccccc;
                padding: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #3e3e42;
                background-color: #252526;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 10px 20px;
                border: 1px solid #3e3e42;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: #252526;
                color: #007acc;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #3e3e42;
            }
            QPushButton {
                background-color: #0e639c;
                color: #ffffff;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5a8f;
            }
            QTableWidget {
                background-color: #252526;
                color: #cccccc;
                gridline-color: #3e3e42;
                border: 1px solid #3e3e42;
                alternate-background-color: #2d2d2d;
            }
            QTableWidget::item {
                padding: 5px;
                background-color: #252526;
            }
            QTableWidget::item:alternate {
                background-color: #2d2d2d;
            }
            QTableWidget::item:selected {
                background-color: #3e3e42;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #cccccc;
                padding: 5px;
                border: 1px solid #3e3e42;
                font-weight: bold;
            }
        """)

    def create_summary_tab(self) -> QWidget:
        """Crear tab de resumen"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Cards de métricas principales
        metrics_layout = QHBoxLayout()

        # Total ejecuciones
        self.total_executions_card = self.create_metric_card(
            "Total Ejecuciones", "0", "📊"
        )
        metrics_layout.addWidget(self.total_executions_card)

        # Esta semana
        self.week_executions_card = self.create_metric_card(
            "Esta Semana", "0", "📅"
        )
        metrics_layout.addWidget(self.week_executions_card)

        # Hoy
        self.today_executions_card = self.create_metric_card(
            "Hoy", "0", "🕐"
        )
        metrics_layout.addWidget(self.today_executions_card)

        # Tasa de éxito
        self.success_rate_card = self.create_metric_card(
            "Tasa Éxito", "0%", "✅"
        )
        metrics_layout.addWidget(self.success_rate_card)

        layout.addLayout(metrics_layout)

        # Top 10 más usados (gráfico de barras horizontal)
        self.top_items_figure = Figure(figsize=(10, 5), facecolor='#252526')
        self.top_items_canvas = FigureCanvas(self.top_items_figure)
        layout.addWidget(self.top_items_canvas)

        return widget

    def create_usage_tab(self) -> QWidget:
        """Crear tab de uso en el tiempo"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Selector de período
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Período:"))

        self.period_combo = QComboBox()
        self.period_combo.addItems(["Últimos 7 días", "Últimos 30 días", "Últimos 90 días"])
        self.period_combo.currentTextChanged.connect(self.update_usage_chart)
        period_layout.addWidget(self.period_combo)

        period_layout.addStretch()
        layout.addLayout(period_layout)

        # Gráfico de línea: Uso por día
        self.usage_timeline_figure = Figure(figsize=(10, 4), facecolor='#252526')
        self.usage_timeline_canvas = FigureCanvas(self.usage_timeline_figure)
        layout.addWidget(self.usage_timeline_canvas)

        # Gráfico de barras: Uso por hora del día
        self.usage_by_hour_figure = Figure(figsize=(10, 3), facecolor='#252526')
        self.usage_by_hour_canvas = FigureCanvas(self.usage_by_hour_figure)
        layout.addWidget(self.usage_by_hour_canvas)

        return widget

    def create_categories_tab(self) -> QWidget:
        """Crear tab de categorías"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Gráfico de torta: Uso por categoría
        self.categories_pie_figure = Figure(figsize=(8, 6), facecolor='#252526')
        self.categories_pie_canvas = FigureCanvas(self.categories_pie_figure)
        layout.addWidget(self.categories_pie_canvas)

        # Tabla con detalle de categorías
        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(4)
        self.categories_table.setHorizontalHeaderLabels([
            "Categoría", "Items", "Ejecuciones", "% del Total"
        ])
        self.categories_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.categories_table)

        return widget

    def create_performance_tab(self) -> QWidget:
        """Crear tab de rendimiento"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Items más lentos
        slow_group = QGroupBox("🐌 Items Más Lentos")
        slow_layout = QVBoxLayout(slow_group)

        self.slow_items_table = QTableWidget()
        self.slow_items_table.setColumnCount(3)
        self.slow_items_table.setHorizontalHeaderLabels([
            "Item", "Tiempo Promedio (s)", "Ejecuciones"
        ])
        self.slow_items_table.horizontalHeader().setStretchLastSection(True)
        slow_layout.addWidget(self.slow_items_table)

        layout.addWidget(slow_group)

        # Items con más errores
        errors_group = QGroupBox("❌ Items con Más Errores")
        errors_layout = QVBoxLayout(errors_group)

        self.error_items_table = QTableWidget()
        self.error_items_table.setColumnCount(4)
        self.error_items_table.setHorizontalHeaderLabels([
            "Item", "Total", "Errores", "Tasa Error (%)"
        ])
        self.error_items_table.horizontalHeader().setStretchLastSection(True)
        errors_layout.addWidget(self.error_items_table)

        layout.addWidget(errors_group)

        return widget

    def create_health_tab(self) -> QWidget:
        """Crear tab de salud del widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Reporte de salud
        health_label = QLabel("📋 Reporte de Salud del Sistema")
        health_label_font = QFont()
        health_label_font.setPointSize(11)
        health_label_font.setBold(True)
        health_label.setFont(health_label_font)
        layout.addWidget(health_label)

        self.health_text = QTextEdit()
        self.health_text.setReadOnly(True)
        self.health_text.setMinimumHeight(300)
        layout.addWidget(self.health_text)

        # Botones de acción
        actions_layout = QHBoxLayout()

        cleanup_btn = QPushButton("🧹 Limpiar Items No Usados")
        cleanup_btn.clicked.connect(self.show_cleanup_dialog)
        actions_layout.addWidget(cleanup_btn)

        optimize_btn = QPushButton("⚡ Optimizar Base de Datos")
        optimize_btn.clicked.connect(self.optimize_database)
        actions_layout.addWidget(optimize_btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        return widget

    def create_metric_card(self, title: str, value: str, icon: str) -> QFrame:
        """Crear card de métrica"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3e3e42;
                border-radius: 6px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(card)

        # Icono
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 28px; background: transparent; border: none;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Valor
        value_label = QLabel(value)
        value_label.setObjectName("value_label")
        value_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #007acc;
            background: transparent;
            border: none;
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)

        # Título
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 10px;
            color: #858585;
            background: transparent;
            border: none;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        return card

    def load_data(self):
        """Cargar todos los datos"""
        try:
            logger.info("Loading dashboard data...")
            self.load_summary_data()
            self.load_usage_data()
            self.load_categories_data()
            self.load_performance_data()
            self.load_health_data()
            logger.info("Dashboard data loaded successfully")
        except Exception as e:
            logger.error(f"Error loading dashboard data: {e}")
            QMessageBox.critical(self, "Error", f"Error al cargar datos:\n{str(e)}")

    def load_summary_data(self):
        """Cargar datos del resumen"""
        try:
            stats = self.stats_manager.get_dashboard_stats()

            # Actualizar cards
            self.update_metric_card(self.total_executions_card, str(stats.get('total_executions', 0)))
            self.update_metric_card(self.week_executions_card, str(stats.get('executions_week', 0)))
            self.update_metric_card(self.today_executions_card, str(stats.get('executions_today', 0)))
            self.update_metric_card(self.success_rate_card, f"{stats.get('success_rate', 0):.1f}%")

            # Gráfico top 10
            most_used = self.stats_manager.get_most_used_items(limit=10)
            self.plot_top_items(most_used)

        except Exception as e:
            logger.error(f"Error loading summary data: {e}")

    def plot_top_items(self, items: list):
        """Graficar top items"""
        self.top_items_figure.clear()
        ax = self.top_items_figure.add_subplot(111)

        if not items:
            ax.text(0.5, 0.5, 'No hay datos disponibles',
                   ha='center', va='center', fontsize=14, color='#858585')
            self.top_items_canvas.draw()
            return

        labels = []
        values = []
        for item in items:
            badge = item.get('badge', '')
            label = f"{badge} {item['label']}" if badge else item['label']
            # Truncar labels largos
            if len(label) > 30:
                label = label[:27] + "..."
            labels.append(label)
            values.append(item.get('use_count', 0))

        # Crear gráfico de barras horizontal
        bars = ax.barh(labels, values, color='#007acc', edgecolor='#005a9e')
        ax.set_xlabel('Cantidad de Usos', color='#cccccc')
        ax.set_title('Top 10 Items Más Usados', fontsize=14, fontweight='bold', color='#cccccc', pad=15)
        ax.invert_yaxis()  # Mayor uso arriba
        ax.tick_params(colors='#cccccc')
        ax.set_facecolor('#252526')

        # Agregar valores en las barras
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2,
                   f' {int(width)}',
                   ha='left', va='center', color='#cccccc', fontsize=9)

        self.top_items_figure.tight_layout()
        self.top_items_canvas.draw()

    def update_metric_card(self, card: QFrame, value: str):
        """Actualizar valor de card"""
        value_label = card.findChild(QLabel, "value_label")
        if value_label:
            value_label.setText(value)

    def load_usage_data(self):
        """Cargar datos de uso en el tiempo"""
        try:
            # Obtener días según selector
            period_text = self.period_combo.currentText()
            if "7" in period_text:
                days = 7
            elif "30" in period_text:
                days = 30
            else:
                days = 90

            # Uso por día
            usage_by_day = self.stats_manager.get_usage_by_day(days=days)
            self.plot_usage_timeline(usage_by_day, days)

            # Uso por hora
            usage_by_hour = self.stats_manager.get_usage_by_hour(days=7)
            self.plot_usage_by_hour(usage_by_hour)

        except Exception as e:
            logger.error(f"Error loading usage data: {e}")

    def plot_usage_timeline(self, data: list, days: int):
        """Graficar línea de tiempo de uso"""
        self.usage_timeline_figure.clear()
        ax = self.usage_timeline_figure.add_subplot(111)

        if not data:
            ax.text(0.5, 0.5, 'No hay datos disponibles',
                   ha='center', va='center', fontsize=12, color='#858585')
            self.usage_timeline_canvas.draw()
            return

        dates = [item['date'] for item in data]
        counts = [item['count'] for item in data]

        ax.plot(dates, counts, marker='o', color='#007acc', linewidth=2, markersize=6)
        ax.fill_between(dates, counts, alpha=0.3, color='#007acc')
        ax.set_xlabel('Fecha', color='#cccccc')
        ax.set_ylabel('Ejecuciones', color='#cccccc')
        ax.set_title(f'Uso en los Últimos {days} Días', fontsize=12, fontweight='bold', color='#cccccc')
        ax.tick_params(colors='#cccccc')
        ax.set_facecolor('#252526')
        ax.grid(True, alpha=0.2, color='#3e3e42')

        # Rotar labels de fecha
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        self.usage_timeline_figure.tight_layout()
        self.usage_timeline_canvas.draw()

    def plot_usage_by_hour(self, data: list):
        """Graficar uso por hora del día"""
        self.usage_by_hour_figure.clear()
        ax = self.usage_by_hour_figure.add_subplot(111)

        if not data:
            ax.text(0.5, 0.5, 'No hay datos disponibles',
                   ha='center', va='center', fontsize=12, color='#858585')
            self.usage_by_hour_canvas.draw()
            return

        hours = [item['hour'] for item in data]
        counts = [item['count'] for item in data]

        bars = ax.bar(hours, counts, color='#4EC9B0', edgecolor='#3a9b87')
        ax.set_xlabel('Hora del Día', color='#cccccc')
        ax.set_ylabel('Ejecuciones', color='#cccccc')
        ax.set_title('Uso por Hora del Día (Últimos 7 Días)', fontsize=12, fontweight='bold', color='#cccccc')
        ax.tick_params(colors='#cccccc')
        ax.set_facecolor('#252526')
        ax.set_xticks(range(0, 24))
        ax.grid(True, alpha=0.2, color='#3e3e42', axis='y')

        self.usage_by_hour_figure.tight_layout()
        self.usage_by_hour_canvas.draw()

    def update_usage_chart(self):
        """Actualizar gráfico de uso al cambiar período"""
        self.load_usage_data()

    def load_categories_data(self):
        """Cargar datos de categorías"""
        try:
            usage_by_category = self.stats_manager.get_usage_by_category()
            self.plot_categories_pie(usage_by_category)
            self.populate_categories_table(usage_by_category)

        except Exception as e:
            logger.error(f"Error loading categories data: {e}")

    def plot_categories_pie(self, data: list):
        """Graficar torta de categorías"""
        self.categories_pie_figure.clear()
        ax = self.categories_pie_figure.add_subplot(111)

        if not data or len(data) == 0:
            ax.text(0.5, 0.5, 'No hay datos disponibles',
                   ha='center', va='center', fontsize=12, color='#858585')
            self.categories_pie_canvas.draw()
            return

        labels = [item['category_name'] for item in data]
        sizes = [item['total_uses'] for item in data]

        # Colores
        colors = ['#007acc', '#4EC9B0', '#cc7a00', '#c42b1c', '#00897b',
                 '#9e5e00', '#0e639c', '#F39C12', '#8e44ad', '#27ae60']

        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                          startangle=90, colors=colors[:len(labels)],
                                          textprops={'color': '#cccccc'})

        # Mejorar texto
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax.set_title('Uso por Categoría', fontsize=12, fontweight='bold', color='#cccccc', pad=15)
        ax.set_facecolor('#252526')

        self.categories_pie_figure.tight_layout()
        self.categories_pie_canvas.draw()

    def populate_categories_table(self, data: list):
        """Poblar tabla de categorías"""
        self.categories_table.setRowCount(0)

        if not data:
            return

        total_uses = sum(item['total_uses'] for item in data)

        for row, item in enumerate(data):
            self.categories_table.insertRow(row)

            # Categoría
            self.categories_table.setItem(row, 0, QTableWidgetItem(item['category_name']))

            # Items
            self.categories_table.setItem(row, 1, QTableWidgetItem(str(item['item_count'])))

            # Ejecuciones
            self.categories_table.setItem(row, 2, QTableWidgetItem(str(item['total_uses'])))

            # Porcentaje
            percentage = (item['total_uses'] / total_uses * 100) if total_uses > 0 else 0
            self.categories_table.setItem(row, 3, QTableWidgetItem(f"{percentage:.1f}%"))

    def load_performance_data(self):
        """Cargar datos de rendimiento"""
        try:
            # Items lentos
            slow_items = self.stats_manager.get_slowest_items(limit=10, min_executions=5)
            self.populate_slow_items_table(slow_items)

            # Items con errores
            failing_items = self.stats_manager.get_most_failing_items(limit=10, min_executions=5)
            self.populate_error_items_table(failing_items)

        except Exception as e:
            logger.error(f"Error loading performance data: {e}")

    def populate_slow_items_table(self, items: list):
        """Poblar tabla de items lentos"""
        self.slow_items_table.setRowCount(0)

        for row, item in enumerate(items):
            self.slow_items_table.insertRow(row)

            # Item
            badge = item.get('badge', '')
            label = f"{badge} {item['label']}" if badge else item['label']
            self.slow_items_table.setItem(row, 0, QTableWidgetItem(label))

            # Tiempo promedio
            avg_time = item.get('avg_time_seconds', 0)
            self.slow_items_table.setItem(row, 1, QTableWidgetItem(f"{avg_time:.2f}"))

            # Ejecuciones
            self.slow_items_table.setItem(row, 2, QTableWidgetItem(str(item.get('executions', 0))))

    def populate_error_items_table(self, items: list):
        """Poblar tabla de items con errores"""
        self.error_items_table.setRowCount(0)

        for row, item in enumerate(items):
            self.error_items_table.insertRow(row)

            # Item
            badge = item.get('badge', '')
            label = f"{badge} {item['label']}" if badge else item['label']
            self.error_items_table.setItem(row, 0, QTableWidgetItem(label))

            # Total
            self.error_items_table.setItem(row, 1, QTableWidgetItem(str(item.get('total_executions', 0))))

            # Errores
            self.error_items_table.setItem(row, 2, QTableWidgetItem(str(item.get('error_count', 0))))

            # Tasa error
            error_rate = item.get('error_rate', 0)
            self.error_items_table.setItem(row, 3, QTableWidgetItem(f"{error_rate:.1f}%"))

    def load_health_data(self):
        """Cargar datos de salud"""
        try:
            health_report = self.stats_manager.get_health_report()
            self.display_health_report(health_report)

        except Exception as e:
            logger.error(f"Error loading health data: {e}")

    def display_health_report(self, report: dict):
        """Mostrar reporte de salud"""
        html = """
        <div style='font-family: Consolas, monospace; font-size: 11pt; color: #cccccc;'>
        <h2 style='color: #007acc;'>📋 Reporte de Salud del Sistema</h2>
        <p>Generado: {}</p>
        <hr style='border-color: #3e3e42;'>

        <h3 style='color: #4EC9B0;'>📊 Métricas Generales</h3>
        <ul>
            <li><b>Total de Items:</b> {}</li>
            <li><b>Items Activos:</b> {} ({:.1f}%)</li>
            <li><b>Items Favoritos:</b> {}</li>
            <li><b>Items Sin Usar:</b> {} ({:.1f}%)</li>
        </ul>

        <h3 style='color: #4EC9B0;'>⚡ Rendimiento</h3>
        <ul>
            <li><b>Ejecuciones Hoy:</b> {}</li>
            <li><b>Ejecuciones Esta Semana:</b> {}</li>
            <li><b>Tasa de Éxito Hoy:</b> {:.1f}%</li>
        </ul>

        <h3 style='color: {}'>🏥 Estado de Salud: {}</h3>
        <p>{}</p>

        <h3 style='color: #cc7a00;'>💡 Recomendaciones</h3>
        <ul>
        {}
        </ul>
        </div>
        """.format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            report.get('total_items', 0),
            report.get('active_items', 0),
            (report.get('active_items', 0) / report.get('total_items', 1) * 100),
            report.get('favorites_count', 0),
            report.get('never_used_count', 0),
            (report.get('never_used_count', 0) / report.get('total_items', 1) * 100),
            report.get('executions_today', 0),
            report.get('executions_week', 0),
            report.get('success_rate_today', 0),
            '#4EC9B0' if report.get('health_score', 0) >= 70 else '#cc7a00' if report.get('health_score', 0) >= 50 else '#c42b1c',
            report.get('health_status', 'Desconocido'),
            report.get('health_message', ''),
            '\n'.join([f"<li>{rec}</li>" for rec in report.get('recommendations', [])])
        )

        self.health_text.setHtml(html)

    def show_cleanup_dialog(self):
        """Mostrar diálogo de limpieza"""
        from views.dialogs.forgotten_items_dialog import ForgottenItemsDialog
        dialog = ForgottenItemsDialog(self)
        if dialog.exec():
            # Recargar datos
            self.load_data()

    def optimize_database(self):
        """Optimizar base de datos"""
        try:
            import sqlite3
            conn = sqlite3.connect("widget_sidebar.db")
            cursor = conn.cursor()

            # VACUUM para optimizar
            cursor.execute("VACUUM")

            # Analizar para actualizar estadísticas
            cursor.execute("ANALYZE")

            conn.commit()
            conn.close()

            QMessageBox.information(
                self,
                "Éxito",
                "Base de datos optimizada correctamente"
            )

        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al optimizar base de datos:\n{str(e)}"
            )

    def export_report(self):
        """Exportar reporte a archivo"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Reporte",
                f"reporte_estadisticas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )

            if not file_path:
                return

            # Generar reporte
            report_lines = []
            report_lines.append("=" * 60)
            report_lines.append("REPORTE DE ESTADÍSTICAS - WIDGET SIDEBAR")
            report_lines.append(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("=" * 60)
            report_lines.append("")

            # Dashboard stats
            stats = self.stats_manager.get_dashboard_stats()
            report_lines.append("RESUMEN GENERAL")
            report_lines.append("-" * 60)
            report_lines.append(f"Total Ejecuciones: {stats.get('total_executions', 0)}")
            report_lines.append(f"Ejecuciones Esta Semana: {stats.get('executions_week', 0)}")
            report_lines.append(f"Ejecuciones Hoy: {stats.get('executions_today', 0)}")
            report_lines.append(f"Tasa de Éxito: {stats.get('success_rate', 0):.1f}%")
            report_lines.append("")

            # Top items
            most_used = self.stats_manager.get_most_used_items(limit=10)
            report_lines.append("TOP 10 ITEMS MÁS USADOS")
            report_lines.append("-" * 60)
            for i, item in enumerate(most_used, 1):
                badge = item.get('badge', '')
                label = f"{badge} {item['label']}" if badge else item['label']
                report_lines.append(f"  {i}. {label}: {item.get('use_count', 0)} usos")
            report_lines.append("")

            # Health report
            health_report = self.stats_manager.get_health_report()
            report_lines.append("REPORTE DE SALUD")
            report_lines.append("-" * 60)
            report_lines.append(f"Estado: {health_report.get('health_status', 'Desconocido')}")
            report_lines.append(f"Puntuación: {health_report.get('health_score', 0)}/100")
            report_lines.append("")

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))

            QMessageBox.information(
                self,
                "Éxito",
                f"Reporte exportado correctamente:\n{file_path}"
            )

        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al exportar reporte:\n{str(e)}"
            )
