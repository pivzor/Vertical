from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QPushButton, QComboBox, QMessageBox,
                             QFileDialog, QProgressBar)
from PyQt5.QtCore import Qt, QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from datetime import datetime
from fpdf import FPDF
from locales.locale_manager import tr
import os
from utils.resource_path import resource_path


class DashboardPage(QWidget):
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

    # ---------------- UI ----------------
    def init_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        self.title = QLabel()
        self.title.setProperty("class", "title-main")
        self.main_layout.addWidget(self.title)

        # --- FILTER ---
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
        self.session_combo.currentIndexChanged.connect(self.update_dashboard)
        filter_layout.addWidget(self.session_combo)

        self.refresh_btn = QPushButton()
        self.refresh_btn.clicked.connect(self.load_sessions)
        filter_layout.addWidget(self.refresh_btn)

        self.pdf_btn = QPushButton()
        self.pdf_btn.clicked.connect(self.export_pdf_report)
        filter_layout.addWidget(self.pdf_btn)

        filter_layout.addStretch()
        filter_card.setLayout(filter_layout)
        self.main_layout.addWidget(filter_card)

        # --- STATS ---
        stats_layout = QHBoxLayout()
        self.avg_card = self.create_stat_card()
        self.bad_card = self.create_stat_card()
        self.sessions_card = self.create_stat_card()
        self.best_card = self.create_stat_card()

        stats_layout.addWidget(self.avg_card)
        stats_layout.addWidget(self.bad_card)
        stats_layout.addWidget(self.sessions_card)
        stats_layout.addWidget(self.best_card)

        self.main_layout.addLayout(stats_layout)

        # --- GRAPH ---
        self.figure, self.ax = plt.subplots(figsize=(10, 4))
        self.canvas = Canvas(self.figure)
        self.canvas.setMinimumHeight(300)
        graph_card = QFrame()
        graph_card.setObjectName("card")
        graph_layout = QVBoxLayout()

        graph_layout.addWidget(self.canvas)
        graph_card.setLayout(graph_layout)

        self.main_layout.addWidget(graph_card)

        # --- PROGRESS ---
        self.good_progress = QProgressBar()
        self.bad_progress = QProgressBar()

        progress_card = QFrame()
        progress_card.setObjectName("card")
        progress_layout = QVBoxLayout()

        progress_layout.addWidget(self.good_progress)
        progress_layout.addWidget(self.bad_progress)

        progress_card.setLayout(progress_layout)
        self.main_layout.addWidget(progress_card)

        self.setLayout(self.main_layout)

        self.retranslate_ui()

    def create_stat_card(self):
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout()

        title = QLabel()
        value = QLabel("0")
        value.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(value)

        card.title_label = title
        card.value_label = value
        card.setLayout(layout)

        return card

    # ---------------- DATA ----------------

    def get_pose_cached(self, session_id):
        if session_id not in self.pose_cache:
            self.pose_cache[session_id] = self.db.get_pose_data(session_id)
        return self.pose_cache[session_id]

    def load_sessions(self):
        try:
            self.sessions = self.db.get_user_sessions(self.user_id)

            self.session_combo.blockSignals(True)
            self.session_combo.clear()
            self.session_combo.addItem(tr("all_sessions"), None)

            for s in self.sessions:
                if s.get('status') == 'completed':
                    text = f"{s['starttime'].strftime('%d.%m %H:%M')}"
                    self.session_combo.addItem(text, s['sessionid'])

            self.session_combo.blockSignals(False)

            self.update_dashboard()

        except Exception as e:
            print(e)

    def filter_sessions(self):
        period = self.period_combo.currentData()
        now = datetime.now()

        result = []
        for s in self.sessions:
            if s.get('status') != 'completed':
                continue

            t = s['starttime']

            if period == "today" and t.date() == now.date():
                result.append(s)
            elif period == "week" and t.isocalendar()[1] == now.isocalendar()[1]:
                result.append(s)
            elif period == "month" and t.month == now.month:
                result.append(s)
            elif period == "year" and t.year == now.year:
                result.append(s)
            elif period == "all":
                result.append(s)

        return result

    # ---------------- CORE ----------------

    def update_dashboard(self):
        sessions = self.filter_sessions()

        if not sessions:
            self.clear_dashboard()
            return

        stats = []

        for s in sessions:
            data = self.get_pose_cached(s['sessionid'])
            if not data:
                continue

            scores = [max(0, 100 - (r[1] * 2)) for r in data]

            stats.append({
                "date": s['starttime'].strftime("%d.%m"),
                "avg": sum(scores) / len(scores),
                "max": max(scores),
                "bad": sum(1 for x in scores if x < 60)
            })

        if not stats:
            self.clear_dashboard()
            return

        # --- вычисления ---
        avg_all = int(sum(s["avg"] for s in stats) / len(stats))
        best = int(max(s["max"] for s in stats))
        bad_total = sum(s["bad"] for s in stats)

        self.avg_card.value_label.setText(str(avg_all))
        self.best_card.value_label.setText(str(best))
        self.sessions_card.value_label.setText(str(len(stats)))
        self.bad_card.value_label.setText(str(bad_total))

        # --- график ---
        self.ax.clear()
        self.ax.bar([s["date"] for s in stats], [s["avg"] for s in stats])
        self.canvas.draw()

        # --- прогресс ---
        good = sum(1 for s in stats if s["avg"] >= 80)
        bad = sum(1 for s in stats if s["avg"] < 60)
        total = good + bad

        if total:
            self.good_progress.setValue(int(good / total * 100))
            self.bad_progress.setValue(int(bad / total * 100))
        else:
            self.good_progress.setValue(0)
            self.bad_progress.setValue(0)

    # ---------------- PDF ----------------

    def export_pdf_report(self):
        try:
            from datetime import datetime
            from fpdf import FPDF
            from locales.locale_manager import tr
            from utils.resource_path import resource_path

            sessions = self.filter_sessions()

            if not sessions:
                QMessageBox.warning(self, "PDF", tr("pdf_no_data"))
                return

            pdf = FPDF()
            pdf.add_page()

            pdf.add_font(
                "DejaVu",
                "",
                resource_path("assets/fonts/DejaVuSans.ttf"),
                uni=True
            )

            pdf.set_font("DejaVu", size=14)
            pdf.cell(200, 10, txt=tr("pdf_report"), ln=True, align="C")

            pdf.ln(5)
            pdf.set_font("DejaVu", size=10)
            pdf.cell(
                200,
                8,
                txt=f"{tr('pdf_created')} {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                ln=True
            )

            pdf.ln(5)

            total_avg = 0
            valid_sessions = 0

            pdf.set_font("DejaVu", size=10)

            # ===== HEADER (ЛОКАЛИЗАЦИЯ) =====
            pdf.cell(60, 8, tr("pdf_date_header"), border=1)
            pdf.cell(40, 8, tr("pdf_avg_score_header"), border=1)
            pdf.cell(40, 8, tr("pdf_bad_frames_header"), border=1)
            pdf.cell(50, 8, tr("pdf_status_header"), border=1)
            pdf.ln()

            for s in sessions:
                data = self.get_pose_cached(s['sessionid'])
                if not data:
                    continue

                scores = [max(0, 100 - (r[1] * 2)) for r in data]

                avg = sum(scores) / len(scores)
                bad = sum(1 for x in scores if x < 60)

                # ===== STATUS (ЛОКАЛИЗАЦИЯ) =====
                if avg >= 80:
                    status = tr("posture_excellent")
                elif avg >= 60:
                    status = tr("posture_good")
                else:
                    status = tr("posture_slouch")

                pdf.cell(60, 8, s['starttime'].strftime("%d.%m %H:%M"), border=1)
                pdf.cell(40, 8, str(int(avg)), border=1)
                pdf.cell(40, 8, str(bad), border=1)
                pdf.cell(50, 8, status, border=1)
                pdf.ln()

                total_avg += avg
                valid_sessions += 1

            # ===== SUMMARY =====
            pdf.ln(5)

            if valid_sessions > 0:
                pdf.set_font("DejaVu", size=11)
                pdf.cell(
                    200,
                    8,
                    txt=f"{tr('pdf_overall_avg')}: {int(total_avg / valid_sessions)}",
                    ln=True
                )

            # ===== SAVE =====
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
    # ---------------- UI ----------------

    def retranslate_ui(self):
        self.title.setText(tr("dashboard_title"))

        self.filter_label.setText(tr("filter"))
        self.session_label.setText(tr("session"))

        self.refresh_btn.setText(tr("refresh"))
        self.pdf_btn.setText(tr("save_pdf"))

        self.avg_card.title_label.setText(tr("avg_score"))
        self.bad_card.title_label.setText(tr("violations"))
        self.sessions_card.title_label.setText(tr("total_sessions"))
        self.best_card.title_label.setText(tr("best_score"))

        self.period_combo.clear()
        self.period_combo.addItem(tr("all_sessions"), "all")
        self.period_combo.addItem(tr("today"), "today")
        self.period_combo.addItem(tr("this_week"), "week")
        self.period_combo.addItem(tr("this_month"), "month")
        self.period_combo.addItem(tr("this_year"), "year")

    def clear_dashboard(self):
        self.avg_card.value_label.setText("0")
        self.bad_card.value_label.setText("0")
        self.sessions_card.value_label.setText("0")
        self.best_card.value_label.setText("0")

        self.ax.clear()
        self.canvas.draw()

        self.good_progress.setValue(0)
        self.bad_progress.setValue(0)