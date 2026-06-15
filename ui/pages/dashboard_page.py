from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QComboBox, QMessageBox,
    QFileDialog
)
from PyQt5.QtCore import Qt, QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from datetime import datetime
from fpdf import FPDF
import os
import tempfile
import shutil

from locales.locale_manager import tr
from utils.resource_path import resource_path


class DashboardPage(QWidget):
    # =========================================================
    # INIT
    # =========================================================
    def __init__(self, analyzer, db, user_id, settings_service=None):
        super().__init__()

        self.db = db
        self.user_id = user_id
        self.analyzer = analyzer
        self.settings_service = settings_service

        self.sessions = []
        self.pose_cache = {}

        self.init_ui()

        QTimer.singleShot(100, self.load_sessions)

        self.timer = QTimer()
        self.timer.timeout.connect(self.load_sessions)
        self.timer.start(15000)

    # =========================================================
    # UI
    # =========================================================
    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # --- TITLE ---
        self.title = QLabel()
        self.title.setProperty("class", "title-main")
        self.main_layout.addWidget(self.title)

        # --- FILTER PANEL ---
        filter_card = QFrame()
        filter_card.setObjectName("card")
        filter_layout = QHBoxLayout()

        self.filter_label = QLabel()
        filter_layout.addWidget(self.filter_label)

        self.period_combo = QComboBox()
        self.period_combo.currentIndexChanged.connect(self.update_dashboard)
        filter_layout.addWidget(self.period_combo)

        self.session_label = QLabel()
        filter_layout.addWidget(self.session_label)

        self.session_combo = QComboBox()
        self.session_combo.setFixedWidth(180)
        self.session_combo.currentIndexChanged.connect(self.on_session_changed)
        filter_layout.addWidget(self.session_combo)

        self.pdf_btn = QPushButton()
        self.pdf_btn.clicked.connect(self.export_pdf_report)
        filter_layout.addWidget(self.pdf_btn)

        filter_layout.addStretch()
        filter_card.setLayout(filter_layout)
        self.main_layout.addWidget(filter_card)

        # --- STATS CARDS ---
        stats_layout = QHBoxLayout()
        self.avg_card = self._create_stat_card()
        self.sessions_card = self._create_stat_card()
        self.best_card = self._create_stat_card()

        stats_layout.addWidget(self.avg_card)
        stats_layout.addWidget(self.sessions_card)
        stats_layout.addWidget(self.best_card)

        self.main_layout.addLayout(stats_layout)

        # --- GRAPH ---
        self.figure, self.ax = plt.subplots(figsize=(10, 4))
        self.canvas = Canvas(self.figure)
        self.canvas.setMinimumHeight(320)

        graph_card = QFrame()
        graph_card.setObjectName("card")
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.canvas)
        graph_card.setLayout(graph_layout)

        self.main_layout.addWidget(graph_card)

        self.setLayout(self.main_layout)
        self.retranslate_ui()

    def _create_stat_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout()

        title = QLabel()
        value = QLabel("0")
        value.setProperty("class", "value-large")
        value.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(value)

        card.title_label = title
        card.value_label = value
        card.setLayout(layout)
        return card

    # =========================================================
    # CACHE
    # =========================================================
    def get_pose_cached(self, session_id):
        if session_id not in self.pose_cache:
            self.pose_cache[session_id] = self.db.get_pose_data(session_id)
        return self.pose_cache[session_id]

    def invalidate_cache(self, session_id=None):
        if session_id:
            self.pose_cache.pop(session_id, None)
        else:
            self.pose_cache.clear()

    # =========================================================
    # SESSIONS LOADING
    # =========================================================
    def load_sessions(self):
        try:
            new_sessions = self.db.get_user_sessions(self.user_id)

            # Удаляем из кэша сессии, которых больше нет
            valid_ids = {
                s['sessionid'] for s in new_sessions
                if s.get('status') == 'completed'
            }
            for sid in list(self.pose_cache.keys()):
                if sid not in valid_ids:
                    self.pose_cache.pop(sid, None)

            self.sessions = new_sessions

            # Сохраняем текущий выбор
            current_data = self.session_combo.currentData()

            self.session_combo.blockSignals(True)
            self.session_combo.clear()
            self.session_combo.addItem(tr("all_sessions"), None)

            sorted_sessions = sorted(
                self.sessions,
                key=lambda x: x['starttime'],
                reverse=True
            )

            for s in sorted_sessions:
                if s.get('status') == 'completed':
                    label = s['starttime'].strftime('%d.%m %H:%M')
                    self.session_combo.addItem(label, s['sessionid'])

            # Восстанавливаем выбор
            if current_data is not None:
                for i in range(self.session_combo.count()):
                    if self.session_combo.itemData(i) == current_data:
                        self.session_combo.setCurrentIndex(i)
                        break

            self.session_combo.blockSignals(False)
            self.update_dashboard()

        except Exception as e:
            print("load_sessions error:", e)

    # =========================================================
    # FILTERS
    # =========================================================
    def filter_sessions(self):
        selected_id = self.session_combo.currentData()

        # Конкретная сессия
        if selected_id is not None:
            for s in self.sessions:
                if (s['sessionid'] == selected_id
                        and s.get('status') == 'completed'):
                    return [s]
            return []

        # По периоду
        period = self.period_combo.currentData()
        now = datetime.now()
        result = []

        for s in self.sessions:
            if s.get('status') != 'completed':
                continue

            t = s['starttime']

            if period == "all":
                result.append(s)
            elif period == "today" and t.date() == now.date():
                result.append(s)
            elif period == "week" and t.isocalendar()[1] == now.isocalendar()[1] and t.year == now.year:
                result.append(s)
            elif period == "month" and t.month == now.month and t.year == now.year:
                result.append(s)
            elif period == "year" and t.year == now.year:
                result.append(s)

        return result

    def on_session_changed(self):
        """При выборе конкретной сессии отключаем фильтр периода"""
        selected = self.session_combo.currentData()
        self.period_combo.setEnabled(selected is None)
        self.update_dashboard()

    # =========================================================
    # SCORES UTILS
    # =========================================================
    def _extract_scores(self, data):
        """neck_angle в БД — это уже готовый балл 0–100"""
        return [max(0, min(100, r[1])) for r in data if r[1] is not None]

    def _status_by_score(self, score):
        if score >= 85:
            return tr("posture_excellent"), "#16a34a"
        elif score >= 70:
            return tr("posture_good"), "#eab308"
        elif score >= 55:
            return tr("posture_slight"), "#f97316"
        elif score >= 40:
            return tr("posture_slouch"), "#ea580c"
        else:
            return tr("posture_bad"), "#dc2626"

    def _color_stat_card(self, card, value):
        _, color = self._status_by_score(value)
        card.value_label.setStyleSheet(f"color: {color};")

    # =========================================================
    # CORE
    # =========================================================
    def update_dashboard(self):
        sessions = self.filter_sessions()

        if not sessions:
            self.clear_dashboard()
            return

        sessions = sorted(sessions, key=lambda x: x['starttime'])

        stats = []
        for s in sessions:
            data = self.get_pose_cached(s['sessionid'])
            if not data:
                continue

            scores = self._extract_scores(data)
            if not scores:
                continue

            stats.append({
                "datetime": s['starttime'],
                "session_id": s['sessionid'],
                "avg": sum(scores) / len(scores),
                "max": max(scores),
                "min": min(scores),
            })

        if not stats:
            self.clear_dashboard()
            return

        # Cards
        avg_all = int(round(sum(s["avg"] for s in stats) / len(stats)))
        best = int(round(max(s["max"] for s in stats)))

        self.avg_card.value_label.setText(str(avg_all))
        self.sessions_card.value_label.setText(str(len(stats)))
        self.best_card.value_label.setText(str(best))

        self._color_stat_card(self.avg_card, avg_all)
        self._color_stat_card(self.best_card, best)

        # Chart
        self._draw_chart(stats)

    # =========================================================
    # CHART
    # =========================================================
    def _draw_chart(self, stats):
        self.ax.clear()

        x = list(range(len(stats)))
        values = [s["avg"] for s in stats]

        labels = [
            s["datetime"].strftime("%d.%m\n%H:%M")
            for s in stats
        ]

        # Цветные точки в зависимости от балла
        point_colors = [self._status_by_score(v)[1] for v in values]

        # Линия
        self.ax.plot(
            x,
            values,
            linewidth=2.2,
            color="#3b82f6",
            zorder=2,
            alpha=0.85
        )

        # Точки (цветные)
        self.ax.scatter(
            x,
            values,
            s=90,
            c=point_colors,
            edgecolors="white",
            linewidths=2,
            zorder=3
        )

        # Подписи значений
        for xi, yi in zip(x, values):
            self.ax.annotate(
                f"{int(yi)}",
                (xi, yi),
                textcoords="offset points",
                xytext=(0, 12),
                ha='center',
                fontsize=9,
                fontweight='bold'
            )

        # Средняя линия
        avg_line = sum(values) / len(values)
        self.ax.axhline(
            avg_line,
            linestyle='--',
            linewidth=1.2,
            color="#94a3b8",
            label=f"{tr('avg_score')}: {int(avg_line)}",
            zorder=1
        )

        # Оси
        self.ax.set_ylim(0, 115)

        if len(x) > 1:
            self.ax.set_xlim(-0.6, len(x) - 0.4)
        else:
            self.ax.set_xlim(-1, 1)

        self.ax.set_xticks(x)
        rotation = 45 if len(stats) > 8 else 0
        ha = 'right' if rotation else 'center'
        self.ax.set_xticklabels(labels, rotation=rotation, ha=ha)

        self.ax.grid(True, linestyle='--', alpha=0.35, zorder=0)
        self.ax.set_title(tr("avg_score_by_sessions"), pad=15)
        self.ax.set_ylabel(tr("avg_score"))

        self.ax.legend(fontsize=10, loc='lower right')

        self._apply_chart_theme()
        self.figure.tight_layout()
        self.canvas.draw()

    def _apply_chart_theme(self):
        self.ax.title.set_fontsize(16)
        self.ax.xaxis.label.set_fontsize(12)
        self.ax.yaxis.label.set_fontsize(12)

        for label in self.ax.get_xticklabels():
            label.set_fontsize(10)
        for label in self.ax.get_yticklabels():
            label.set_fontsize(10)

        dark = (
            self.settings_service
            and self.settings_service.get_theme() == "dark"
        )

        if dark:
            bg = "#161b22"
            text = "#e6edf3"
            grid = "#30363d"
        else:
            bg = "#f6f8fa"
            text = "#000000"
            grid = "#d0d7de"

        self.figure.patch.set_facecolor(bg)
        self.ax.set_facecolor(bg)

        self.ax.tick_params(colors=text)
        self.ax.yaxis.label.set_color(text)
        self.ax.xaxis.label.set_color(text)
        self.ax.title.set_color(text)

        for spine in self.ax.spines.values():
            spine.set_color(grid)

        legend = self.ax.get_legend()
        if legend:
            legend.get_frame().set_facecolor(bg)
            legend.get_frame().set_edgecolor(grid)
            for t in legend.get_texts():
                t.set_color(text)

    # =========================================================
    # PDF EXPORT
    # =========================================================
    def export_pdf_report(self):
        try:
            sessions = self.filter_sessions()

            if not sessions:
                QMessageBox.warning(self, "PDF", tr("pdf_no_data"))
                return

            sessions = sorted(sessions, key=lambda x: x['starttime'])

            pdf = FPDF()
            pdf.add_page()

            # Шрифт
            original_font = resource_path("assets/fonts/DejaVuSans.ttf")
            temp_font = os.path.join(tempfile.gettempdir(), "DejaVuSans.ttf")
            shutil.copyfile(original_font, temp_font)
            pdf.add_font("DejaVu", "", temp_font, uni=True)

            # Заголовок
            pdf.set_font("DejaVu", size=14)
            pdf.cell(200, 10, txt=tr("pdf_report"), ln=True, align="C")

            pdf.ln(3)
            pdf.set_font("DejaVu", size=10)
            pdf.cell(
                200, 8,
                txt=f"{tr('pdf_created')} {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                ln=True
            )

            pdf.ln(3)

            # Таблица
            pdf.set_font("DejaVu", size=10)
            pdf.cell(60, 8, tr("pdf_date_header"), border=1)
            pdf.cell(40, 8, tr("pdf_avg_score_header"), border=1)
            pdf.cell(50, 8, tr("pdf_status_header"), border=1)
            pdf.ln()

            total_avg = 0
            valid_sessions = 0

            for s in sessions:
                data = self.get_pose_cached(s['sessionid'])
                if not data:
                    continue

                scores = self._extract_scores(data)
                if not scores:
                    continue

                avg = sum(scores) / len(scores)
                status, _ = self._status_by_score(avg)

                pdf.cell(60, 8, s['starttime'].strftime("%d.%m %H:%M"), border=1)
                pdf.cell(40, 8, str(int(avg)), border=1)
                pdf.cell(50, 8, status, border=1)
                pdf.ln()

                total_avg += avg
                valid_sessions += 1

            pdf.ln(5)
            if valid_sessions > 0:
                pdf.set_font("DejaVu", size=11)
                pdf.cell(
                    200, 8,
                    txt=f"{tr('pdf_overall_avg')}: {int(total_avg / valid_sessions)}",
                    ln=True
                )

            # Сохранение
            path, _ = QFileDialog.getSaveFileName(
                self,
                tr("pdf_save_title"),
                "posture_report.pdf",
                "PDF Files (*.pdf)"
            )

            if not path:
                return

            if not path.endswith(".pdf"):
                path += ".pdf"

            pdf.output(path)
            QMessageBox.information(self, "PDF", tr("pdf_saved"))

        except Exception as e:
            QMessageBox.critical(self, "PDF Error", str(e))
            print("PDF ERROR:", e)

    # =========================================================
    # CLEAR / TRANSLATE
    # =========================================================
    def clear_dashboard(self):
        self.avg_card.value_label.setText("0")
        self.avg_card.value_label.setStyleSheet("")
        self.sessions_card.value_label.setText("0")
        self.best_card.value_label.setText("0")
        self.best_card.value_label.setStyleSheet("")

        self.ax.clear()
        self._apply_chart_theme()
        self.canvas.draw()

    def retranslate_ui(self):
        self.title.setText(tr("dashboard_title"))
        self.filter_label.setText(tr("filter"))
        self.session_label.setText(tr("session"))
        self.pdf_btn.setText(tr("save_pdf"))

        self.avg_card.title_label.setText(tr("avg_score"))
        self.sessions_card.title_label.setText(tr("total_sessions"))
        self.best_card.title_label.setText(tr("best_score"))

        # Период — сохраняем выбранное значение
        self.period_combo.blockSignals(True)
        current = self.period_combo.currentData()
        self.period_combo.clear()
        self.period_combo.addItem(tr("all_sessions"), "all")
        self.period_combo.addItem(tr("today"), "today")
        self.period_combo.addItem(tr("this_week"), "week")
        self.period_combo.addItem(tr("this_month"), "month")
        self.period_combo.addItem(tr("this_year"), "year")

        if current:
            for i in range(self.period_combo.count()):
                if self.period_combo.itemData(i) == current:
                    self.period_combo.setCurrentIndex(i)
                    break

        self.period_combo.blockSignals(False)