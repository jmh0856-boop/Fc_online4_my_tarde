from datetime import datetime
from typing import Any
import traceback

import httpx

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from app.services.nexon_client import NexonAPIError, NexonClient
from app.services.trade_service import TradeService


class ImageLoader(QThread):
    """시즌 이미지를 비동기로 불러온다."""

    loaded = Signal(str, bytes)

    def __init__(
        self,
        url: str,
    ) -> None:
        super().__init__()

        self.url = url

    def run(self) -> None:
        try:
            response = httpx.get(
                self.url,
                timeout=10.0,
            )

            if response.status_code == 200:
                self.loaded.emit(
                    self.url,
                    response.content,
                )

        except Exception:
            pass


class MainWindow(QMainWindow):
    """FC Online 거래 내역 메인 화면."""

    def __init__(
        self,
        api_key: str,
    ) -> None:
        super().__init__()

        self.api_key = api_key

        self.nexon_client = NexonClient(
            api_key
        )

        self.trade_service = TradeService(
            self.nexon_client
        )

        self.image_loaders: list[ImageLoader] = []

        self.setWindowTitle(
            "FC Online Personal Tool"
        )

        self.setMinimumSize(
            1100,
            700,
        )

        self.resize(
            1300,
            800,
        )

        self._setup_ui()
        self._setup_status_bar()

    # =========================================================
    # UI
    # =========================================================

    def _setup_ui(self) -> None:
        central_widget = QWidget()

        self.setCentralWidget(
            central_widget
        )

        main_layout = QVBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        main_layout.setSpacing(
            18
        )

        # -----------------------------------------------------
        # 제목
        # -----------------------------------------------------

        title_label = QLabel(
            "FC Online 거래 내역"
        )

        title_label.setObjectName(
            "titleLabel"
        )

        description_label = QLabel(
            "구매 및 판매 거래 내역을 확인합니다."
        )

        description_label.setObjectName(
            "descriptionLabel"
        )

        main_layout.addWidget(
            title_label
        )

        main_layout.addWidget(
            description_label
        )

        # -----------------------------------------------------
        # 버튼
        # -----------------------------------------------------

        button_layout = QHBoxLayout()

        self.refresh_button = QPushButton(
            "거래 내역 새로고침"
        )

        self.refresh_button.setObjectName(
            "refreshButton"
        )

        self.refresh_button.setMinimumSize(
            150,
            42,
        )

        self.refresh_button.clicked.connect(
            self._on_refresh_clicked
        )

        button_layout.addWidget(
            self.refresh_button
        )

        button_layout.addStretch()

        main_layout.addLayout(
            button_layout
        )

        # -----------------------------------------------------
        # 통계
        # -----------------------------------------------------

        self.statistics_frame = QFrame()

        self.statistics_frame.setObjectName(
            "statisticsFrame"
        )

        statistics_layout = QHBoxLayout(
            self.statistics_frame
        )

        statistics_layout.setContentsMargins(
            18,
            14,
            18,
            14,
        )

        self.total_label = QLabel(
            "전체: -"
        )

        self.buy_label = QLabel(
            "구매: -"
        )

        self.sell_label = QLabel(
            "판매: -"
        )

        self.buy_amount_label = QLabel(
            "구매 금액: -"
        )

        self.sell_amount_label = QLabel(
            "판매 금액: -"
        )

        self.difference_label = QLabel(
            "차액: -"
        )

        for label in [
            self.total_label,
            self.buy_label,
            self.sell_label,
            self.buy_amount_label,
            self.sell_amount_label,
            self.difference_label,
        ]:
            label.setObjectName(
                "statisticsLabel"
            )

            statistics_layout.addWidget(
                label
            )

        main_layout.addWidget(
            self.statistics_frame
        )

        # -----------------------------------------------------
        # 거래 테이블
        # -----------------------------------------------------

        table_frame = QFrame()

        table_frame.setObjectName(
            "tableFrame"
        )

        table_layout = QVBoxLayout(
            table_frame
        )

        table_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        self.trade_table = QTableWidget()

        self.trade_table.setColumnCount(
            6
        )

        self.trade_table.setHorizontalHeaderLabels(
            [
                "거래일시",
                "구분",
                "선수",
                "시즌",
                "강화",
                "거래금액",
            ]
        )

        self.trade_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.trade_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.trade_table.setAlternatingRowColors(
            True
        )

        self.trade_table.verticalHeader().setVisible(
            False
        )

        header = (
            self.trade_table
            .horizontalHeader()
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )

        # -----------------------------------------------------
        # 시즌 컬럼
        # -----------------------------------------------------

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.Fixed,
        )

        self.trade_table.setColumnWidth(
            3,
            75,
        )

        # -----------------------------------------------------
        # 강화 컬럼
        # -----------------------------------------------------

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.Fixed,
        )

        self.trade_table.setColumnWidth(
            4,
            85,
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        table_layout.addWidget(
            self.trade_table
        )

        main_layout.addWidget(
            table_frame,
            1,
        )

        self._apply_style()

    # =========================================================
    # Status bar
    # =========================================================

    def _setup_status_bar(self) -> None:
        status_bar = QStatusBar()

        self.setStatusBar(
            status_bar
        )

        status_bar.showMessage(
            "로그인 완료"
        )

    # =========================================================
    # 조회
    # =========================================================

    def _on_refresh_clicked(self) -> None:
        """거래 내역을 조회한다."""

        self.refresh_button.setEnabled(
            False
        )

        self.trade_table.setRowCount(
            0
        )

        self.statusBar().showMessage(
            "거래 내역을 불러오는 중..."
        )

        try:
            trades = (
                self.trade_service
                .get_all_history(
                    0,
                    100,
                )
            )

            self._display_trades(
                trades
            )

            statistics = (
                self.trade_service
                .calculate_statistics(
                    trades
                )
            )

            self._display_statistics(
                statistics
            )

            self.statusBar().showMessage(
                f"거래 내역 {len(trades)}건 조회 완료"
            )

        except NexonAPIError as error:
            self.trade_table.setRowCount(
                0
            )

            self.statusBar().showMessage(
                "조회 실패"
            )

            QMessageBox.critical(
                self,
                "조회 오류",
                "거래 내역을 불러오는 중 오류가 발생했습니다.\n\n"
                f"{error}",
            )

        except Exception as error:
            print()
            print("=" * 70)
            print("거래 내역 조회 중 예외 발생")
            print("=" * 70)

            traceback.print_exc()

            print("=" * 70)
            print()

            self.trade_table.setRowCount(
                0
            )

            self.statusBar().showMessage(
                "조회 실패"
            )

            QMessageBox.critical(
                self,
                "프로그램 오류",
                "거래 내역을 불러오는 중 오류가 발생했습니다.\n\n"
                f"{type(error).__name__}: {error}",
            )

        finally:
            self.refresh_button.setEnabled(
                True
            )

    # =========================================================
    # 거래 표시
    # =========================================================

    def _display_trades(
        self,
        trades: list[dict[str, Any]],
    ) -> None:
        """거래 내역을 테이블에 표시한다."""

        self.trade_table.setRowCount(
            len(trades)
        )

        for row, trade in enumerate(
            trades
        ):
            # -------------------------------------------------
            # 거래일시
            # -------------------------------------------------

            trade_date = self._format_date(
                trade.get(
                    "trade_date"
                )
            )

            date_item = QTableWidgetItem(
                trade_date
            )

            date_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.trade_table.setItem(
                row,
                0,
                date_item,
            )

            # -------------------------------------------------
            # 거래 구분
            # -------------------------------------------------

            trade_type = trade.get(
                "trade_type",
                "-",
            )

            type_item = QTableWidgetItem(
                str(trade_type)
            )

            type_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.trade_table.setItem(
                row,
                1,
                type_item,
            )

            # -------------------------------------------------
            # 선수명
            # -------------------------------------------------

            player_name = trade.get(
                "player_name"
            )

            if not player_name:
                player_name = "알 수 없는 선수"

            player_item = QTableWidgetItem(
                str(player_name)
            )

            player_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.trade_table.setItem(
                row,
                2,
                player_item,
            )

            # -------------------------------------------------
            # 시즌 이미지
            # -------------------------------------------------

            season_url = trade.get(
                "season_img"
            )

            season_label = QLabel()

            season_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            season_label.setFixedSize(
                55,
                32,
            )

            season_label.setScaledContents(
                False
            )

            season_label.setToolTip(
                str(
                    trade.get(
                        "season_name",
                        "",
                    )
                )
            )

            self.trade_table.setCellWidget(
                row,
                3,
                season_label,
            )

            if season_url:
                self._load_season_image(
                    str(season_url),
                    season_label,
                )

            else:
                season_label.setText(
                    "-"
                )

            # -------------------------------------------------
            # 강화
            # -------------------------------------------------

            grade = trade.get(
                "grade"
            )

            if grade is None:
                grade_level = 0
                grade_text = "-"

            else:
                try:
                    grade_level = int(
                        str(grade)
                        .replace("+", "")
                        .strip()
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    grade_level = 0

                if 1 <= grade_level <= 13:
                    grade_text = (
                        f"+{grade_level}"
                    )
                else:
                    grade_text = "-"

            grade_widget = self._create_grade_widget(
                grade_level,
                grade_text,
            )

            self.trade_table.setCellWidget(
                row,
                4,
                grade_widget,
            )

            # -------------------------------------------------
            # 거래 금액
            # -------------------------------------------------

            value = trade.get(
                "value"
            )

            value_item = QTableWidgetItem(
                self._format_price(
                    value
                )
            )

            value_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

            self.trade_table.setItem(
                row,
                5,
                value_item,
            )

        self.trade_table.resizeRowsToContents()

    # =========================================================
    # 강화 UI
    # =========================================================

    def _create_grade_widget(
        self,
        grade_level: int,
        grade_text: str,
    ) -> QWidget:
        """
        강화 표시 전용 위젯을 만든다.

        숫자는 검정색으로 유지하고,
        강화 단계에 따라 메탈 계열의
        배경과 테두리를 적용한다.
        """

        # -----------------------------------------------------
        # 바깥 컨테이너
        # -----------------------------------------------------

        container = QFrame()

        container.setObjectName(
            "gradeContainer"
        )

        container.setFixedSize(
            64,
            34,
        )

        container_layout = QHBoxLayout(
            container
        )

        container_layout.setContentsMargins(
            2,
            2,
            2,
            2,
        )

        container_layout.setSpacing(
            0
        )

        # -----------------------------------------------------
        # 실제 강화 뱃지
        # -----------------------------------------------------

        badge = QLabel(
            grade_text
        )

        badge.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        badge.setFixedSize(
            58,
            28,
        )

        # -----------------------------------------------------
        # 단계별 색상
        # -----------------------------------------------------

        if grade_level == 1:

            background = "#34495E"
            border = "#17212B"
            inner = "#62778A"

        elif 2 <= grade_level <= 4:

            background = "#B87333"
            border = "#663A1D"
            inner = "#D59A67"

        elif 5 <= grade_level <= 7:

            background = "#BFC5CB"
            border = "#737B83"
            inner = "#F4F6F8"

        elif 8 <= grade_level <= 10:

            background = "#D6A72C"
            border = "#775400"
            inner = "#F6D96A"

        elif 11 <= grade_level <= 13:

            background = "#DCE6EE"
            border = "#71899B"
            inner = "#FFFFFF"

        else:

            background = "#E5E7EB"
            border = "#9CA3AF"
            inner = "#F8FAFC"

        # -----------------------------------------------------
        # 바깥 프레임
        # -----------------------------------------------------

        container.setStyleSheet(
            f"""
            QFrame#gradeContainer {{
                background-color: {background};
                border: 1px solid {border};
                border-radius: 7px;
            }}
            """
        )

        # -----------------------------------------------------
        # 내부 뱃지
        # -----------------------------------------------------

        badge.setStyleSheet(
            f"""
            QLabel {{
                background-color: {background};
                color: #111111;
                border: 1px solid {inner};
                border-radius: 5px;
                padding: 0px;
                margin: 0px;
                font-size: 13px;
                font-weight: 900;
            }}
            """
        )

        container_layout.addWidget(
            badge,
            0,
            Qt.AlignmentFlag.AlignCenter,
        )

        return container

    # =========================================================
    # 시즌 이미지
    # =========================================================

    def _load_season_image(
        self,
        url: str,
        label: QLabel,
    ) -> None:
        """시즌 이미지를 다운로드한다."""

        loader = ImageLoader(
            url
        )

        loader.loaded.connect(
            lambda loaded_url, data:
            self._set_season_image(
                loaded_url,
                data,
                label,
            )
        )

        self.image_loaders.append(
            loader
        )

        loader.finished.connect(
            lambda:
            self._remove_image_loader(
                loader
            )
        )

        loader.start()

    def _set_season_image(
        self,
        url: str,
        data: bytes,
        label: QLabel,
    ) -> None:
        """다운로드한 시즌 이미지를 표시한다."""

        pixmap = QPixmap()

        if not pixmap.loadFromData(
            data
        ):
            label.setText(
                "-"
            )
            return

        scaled = pixmap.scaled(
            label.width(),
            label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        label.setPixmap(
            scaled
        )

    def _remove_image_loader(
        self,
        loader: ImageLoader,
    ) -> None:
        if loader in self.image_loaders:
            self.image_loaders.remove(
                loader
            )

        loader.deleteLater()

    # =========================================================
    # 통계
    # =========================================================

    def _display_statistics(
        self,
        statistics: dict[str, Any],
    ) -> None:
        """거래 통계를 표시한다."""

        self.total_label.setText(
            f"전체: {statistics.get('total_count', 0)}건"
        )

        self.buy_label.setText(
            f"구매: {statistics.get('buy_count', 0)}건"
        )

        self.sell_label.setText(
            f"판매: {statistics.get('sell_count', 0)}건"
        )

        self.buy_amount_label.setText(
            "구매 금액: "
            + self._format_price(
                statistics.get(
                    "buy_amount"
                )
            )
        )

        self.sell_amount_label.setText(
            "판매 금액: "
            + self._format_price(
                statistics.get(
                    "sell_amount"
                )
            )
        )

        self.difference_label.setText(
            "차액: "
            + self._format_price(
                statistics.get(
                    "difference"
                )
            )
        )

    # =========================================================
    # 금액
    # =========================================================

    @staticmethod
    def _format_price(
        value: Any,
    ) -> str:
        """BP를 조 단위로 표시한다."""

        if value is None:
            return "-"

        try:
            value = int(value)

        except (
            TypeError,
            ValueError,
        ):
            return "-"

        trillion = value / 1_000_000_000_000

        return f"{trillion:,.2f}조"

    # =========================================================
    # 날짜
    # =========================================================

    @staticmethod
    def _format_date(
        value: Any,
    ) -> str:
        """거래일시를 보기 좋게 표시한다."""

        if not value:
            return "-"

        try:
            dt = datetime.fromisoformat(
                str(value)
            )

            return dt.strftime(
                "%m-%d %H:%M"
            )

        except (
            ValueError,
            TypeError,
        ):
            return str(value)

    # =========================================================
    # 스타일
    # =========================================================

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f5f6f8;
            }

            QLabel#titleLabel {
                font-size: 28px;
                font-weight: bold;
                color: #202124;
            }

            QLabel#descriptionLabel {
                font-size: 14px;
                color: #6b7280;
            }

            QFrame#statisticsFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }

            QLabel#statisticsLabel {
                font-size: 13px;
                font-weight: bold;
                color: #374151;
            }

            QFrame#tableFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
            }

            QPushButton#refreshButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton#refreshButton:hover {
                background-color: #1d4ed8;
            }

            QPushButton#refreshButton:disabled {
                background-color: #93c5fd;
            }

            QTableWidget {
                background-color: white;
                alternate-background-color: #f9fafb;
                border: none;
                gridline-color: #e5e7eb;
                font-size: 13px;
            }

            QTableWidget::item {
                padding: 6px;
            }

            QHeaderView::section {
                background-color: #f3f4f6;
                color: #374151;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #d1d5db;
                padding: 10px;
            }

            QStatusBar {
                color: #6b7280;
            }
            """
        )

    # =========================================================
    # 종료
    # =========================================================

    def closeEvent(
        self,
        event,
    ) -> None:
        self.api_key = ""

        self.nexon_client = None

        self.trade_service = None

        event.accept()