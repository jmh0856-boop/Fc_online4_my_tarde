from datetime import datetime
from typing import Any
import traceback

import httpx

from PySide6.QtCore import Qt, QThread, Signal, QDate
from PySide6.QtGui import QPixmap, QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QDateEdit,
    QComboBox,
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

        self.image_loaders: list[
            ImageLoader
        ] = []

        # =====================================================
        # 거래 데이터
        # =====================================================

        self.all_trades: list[
            dict[str, Any]
        ] = []

        self.filtered_trades: list[
            dict[str, Any]
        ] = []

        # =====================================================
        # 페이지
        # =====================================================

        self.current_page = 1
        self.page_size = 10

        self.setWindowTitle(
            "FC Online Personal Tool"
        )

        self.setMinimumSize(
            1200,
            750,
        )

        self.resize(
            1500,
            850,
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
            14
        )

        # =====================================================
        # 제목
        # =====================================================

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

        # =====================================================
        # 검색 / 필터
        # =====================================================

        filter_frame = QFrame()

        filter_frame.setObjectName(
            "filterFrame"
        )

        filter_layout = QVBoxLayout(
            filter_frame
        )

        filter_layout.setContentsMargins(
            14,
            12,
            14,
            12,
        )

        filter_layout.setSpacing(
            10
        )

        # -----------------------------------------------------
        # 첫 번째 필터 줄
        # -----------------------------------------------------

        filter_row_1 = QHBoxLayout()

        trade_label = QLabel(
            "거래:"
        )

        filter_row_1.addWidget(
            trade_label
        )

        self.trade_button_group = QButtonGroup(
            self
        )

        self.all_radio = QRadioButton(
            "전체"
        )

        self.buy_radio = QRadioButton(
            "구매"
        )

        self.sell_radio = QRadioButton(
            "판매"
        )

        self.all_radio.setChecked(
            True
        )

        self.trade_button_group.addButton(
            self.all_radio
        )

        self.trade_button_group.addButton(
            self.buy_radio
        )

        self.trade_button_group.addButton(
            self.sell_radio
        )

        filter_row_1.addWidget(
            self.all_radio
        )

        filter_row_1.addWidget(
            self.buy_radio
        )

        filter_row_1.addWidget(
            self.sell_radio
        )

        filter_row_1.addSpacing(
            20
        )

        player_label = QLabel(
            "선수:"
        )

        filter_row_1.addWidget(
            player_label
        )

        self.player_search = QLineEdit()

        self.player_search.setPlaceholderText(
            "선수 이름 검색"
        )

        self.player_search.setFixedWidth(
            220
        )

        filter_row_1.addWidget(
            self.player_search
        )

        filter_row_1.addStretch()

        filter_layout.addLayout(
            filter_row_1
        )

        # -----------------------------------------------------
        # 두 번째 필터 줄
        # -----------------------------------------------------

        filter_row_2 = QHBoxLayout()

        period_label = QLabel(
            "기간:"
        )

        filter_row_2.addWidget(
            period_label
        )

        self.start_date = QDateEdit()

        self.start_date.setCalendarPopup(
            True
        )

        self.start_date.setDisplayFormat(
            "yyyy-MM-dd"
        )

        # =====================================================
        # 오늘 기준 한 달 전
        # =====================================================

        self.start_date.setDate(
            QDate.currentDate().addMonths(
                -1
            )
        )

        self.start_date.setFixedWidth(
            120
        )

        filter_row_2.addWidget(
            self.start_date
        )

        separator_label = QLabel(
            "~"
        )

        filter_row_2.addWidget(
            separator_label
        )

        self.end_date = QDateEdit()

        self.end_date.setCalendarPopup(
            True
        )

        self.end_date.setDisplayFormat(
            "yyyy-MM-dd"
        )

        # =====================================================
        # 오늘 날짜
        # =====================================================

        self.end_date.setDate(
            QDate.currentDate()
        )

        self.end_date.setFixedWidth(
            120
        )

        filter_row_2.addWidget(
            self.end_date
        )

        self.search_button = QPushButton(
            "검색"
        )

        self.search_button.setObjectName(
            "searchButton"
        )

        self.search_button.setFixedWidth(
            80
        )

        filter_row_2.addWidget(
            self.search_button
        )

        filter_row_2.addStretch()

        filter_layout.addLayout(
            filter_row_2
        )

        main_layout.addWidget(
            filter_frame
        )

        # =====================================================
        # 버튼
        # =====================================================

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

        # -----------------------------------------------------
        # 표시 개수
        # -----------------------------------------------------

        button_layout.addSpacing(
            12
        )

        page_size_label = QLabel(
            "표시:"
        )

        button_layout.addWidget(
            page_size_label
        )

        self.page_size_combo = QComboBox()

        self.page_size_combo.addItems(
            [
                "10",
                "30",
                "50",
            ]
        )

        self.page_size_combo.setCurrentText(
            "10"
        )

        self.page_size_combo.setFixedWidth(
            75
        )

        self.page_size_combo.currentTextChanged.connect(
            self._on_page_size_changed
        )

        button_layout.addWidget(
            self.page_size_combo
        )

        button_layout.addWidget(
            QLabel("개")
        )

        button_layout.addStretch()

        main_layout.addLayout(
            button_layout
        )

        # =====================================================
        # 통계
        # =====================================================

        self.statistics_frame = QFrame()

        self.statistics_frame.setObjectName(
            "statisticsFrame"
        )

        statistics_layout = QHBoxLayout(
            self.statistics_frame
        )

        statistics_layout.setContentsMargins(
            18,
            12,
            18,
            12,
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

        # =====================================================
        # 거래 테이블
        # =====================================================

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
            9
        )

        self.trade_table.setHorizontalHeaderLabels(
            [
                "거래일시",
                "구분",
                "선수",
                "시즌",
                "강화",
                "구매가",
                "판매가",
                "현재가",
                "차액",
            ]
        )

        self.trade_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.trade_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.trade_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.trade_table.setAlternatingRowColors(
            True
        )

        self.trade_table.verticalHeader().setVisible(
            False
        )

        self.trade_table.setWordWrap(
            False
        )

        header = (
            self.trade_table
            .horizontalHeader()
        )

        for index in range(9):
            header.setSectionResizeMode(
                index,
                QHeaderView.ResizeMode.Fixed,
            )

        self.trade_table.setColumnWidth(
            0,
            125,
        )

        self.trade_table.setColumnWidth(
            1,
            60,
        )

        self.trade_table.setColumnWidth(
            2,
            170,
        )

        self.trade_table.setColumnWidth(
            3,
            85,
        )

        self.trade_table.setColumnWidth(
            4,
            80,
        )

        self.trade_table.setColumnWidth(
            5,
            125,
        )

        self.trade_table.setColumnWidth(
            6,
            125,
        )

        self.trade_table.setColumnWidth(
            7,
            125,
        )

        self.trade_table.setColumnWidth(
            8,
            175,
        )

        table_layout.addWidget(
            self.trade_table
        )

        main_layout.addWidget(
            table_frame,
            1,
        )

        # =====================================================
        # 페이지네이션
        # =====================================================

        pagination_frame = QFrame()

        pagination_layout = QHBoxLayout(
            pagination_frame
        )

        pagination_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        pagination_layout.addStretch()

        self.previous_button = QPushButton(
            "‹ 이전"
        )

        self.previous_button.setFixedWidth(
            85
        )

        self.previous_button.clicked.connect(
            self._previous_page
        )

        pagination_layout.addWidget(
            self.previous_button
        )

        self.page_label = QLabel(
            "1 / 1"
        )

        self.page_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.page_label.setMinimumWidth(
            90
        )

        pagination_layout.addWidget(
            self.page_label
        )

        self.next_button = QPushButton(
            "다음 ›"
        )

        self.next_button.setFixedWidth(
            85
        )

        self.next_button.clicked.connect(
            self._next_page
        )

        pagination_layout.addWidget(
            self.next_button
        )

        pagination_layout.addStretch()

        main_layout.addWidget(
            pagination_frame
        )

        # =====================================================
        # 필터 Signal
        # =====================================================

        self.all_radio.toggled.connect(
            self._on_filter_changed
        )

        self.buy_radio.toggled.connect(
            self._on_filter_changed
        )

        self.sell_radio.toggled.connect(
            self._on_filter_changed
        )

        self.search_button.clicked.connect(
            self._on_filter_changed
        )

        self.player_search.returnPressed.connect(
            self._on_filter_changed
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

        QApplication = __import__(
            "PySide6.QtWidgets",
            fromlist=["QApplication"],
        ).QApplication

        QApplication.processEvents()

        try:
            self.trade_service.clear_price_cache()

            trades = (
                self.trade_service
                .get_all_history(
                    0,
                    100,
                )
            )

            # -------------------------------------------------
            # 현재가 적용
            # -------------------------------------------------

            for trade in trades:
                self.trade_service.apply_current_price(
                    trade
                )

            self.all_trades = trades

            self.current_page = 1

            self._apply_filters(
                reset_page=False
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
            print(
                "=" * 70
            )
            print(
                "거래 내역 조회 중 예외 발생"
            )
            print(
                "=" * 70
            )

            traceback.print_exc()

            print(
                "=" * 70
            )
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
    # 필터
    # =========================================================

    def _on_filter_changed(
        self,
        checked: bool = False,
    ) -> None:
        """검색 조건이 변경되면 필터링한다."""

        if isinstance(
            checked,
            bool,
        ) and not checked:
            return

        self._apply_filters(
            reset_page=True
        )

    def _apply_filters(
        self,
        reset_page: bool = True,
    ) -> None:
        """거래내역에 검색 조건을 적용한다."""

        if reset_page:
            self.current_page = 1

        player_keyword = (
            self.player_search.text()
            .strip()
            .lower()
        )

        selected_type = "전체"

        if self.buy_radio.isChecked():
            selected_type = "구매"

        elif self.sell_radio.isChecked():
            selected_type = "판매"

        start_date = (
            self.start_date.date()
            .toPython()
        )

        end_date = (
            self.end_date.date()
            .toPython()
        )

        filtered: list[
            dict[str, Any]
        ] = []

        for trade in self.all_trades:
            trade_type = trade.get(
                "trade_type"
            )

            if (
                selected_type != "전체"
                and trade_type != selected_type
            ):
                continue

            player_name = str(
                trade.get(
                    "player_name"
                )
                or ""
            )

            if player_keyword:
                if (
                    player_keyword
                    not in player_name.lower()
                ):
                    continue

            trade_date = self._parse_date(
                trade.get(
                    "trade_date"
                )
            )

            if trade_date is not None:
                trade_day = (
                    trade_date.date()
                )

                if trade_day < start_date:
                    continue

                if trade_day > end_date:
                    continue

            filtered.append(
                trade
            )

        self.filtered_trades = filtered

        self._update_statistics(
            filtered
        )

        self._display_current_page()

    # =========================================================
    # 현재 페이지 표시
    # =========================================================

    def _display_current_page(
        self,
    ) -> None:
        """현재 페이지에 해당하는 거래만 표시한다."""

        total_count = len(
            self.filtered_trades
        )

        if total_count == 0:
            self.trade_table.setRowCount(
                0
            )

            self.page_label.setText(
                "0 / 0"
            )

            self.previous_button.setEnabled(
                False
            )

            self.next_button.setEnabled(
                False
            )

            return

        total_pages = (
            total_count
            + self.page_size
            - 1
        ) // self.page_size

        if self.current_page > total_pages:
            self.current_page = (
                total_pages
            )

        start_index = (
            self.current_page - 1
        ) * self.page_size

        end_index = min(
            start_index
            + self.page_size,
            total_count,
        )

        page_trades = (
            self.filtered_trades[
                start_index:end_index
            ]
        )

        self._display_trades(
            page_trades
        )

        self.page_label.setText(
            f"{self.current_page} / {total_pages}"
        )

        self.previous_button.setEnabled(
            self.current_page > 1
        )

        self.next_button.setEnabled(
            self.current_page < total_pages
        )

    # =========================================================
    # 페이지 크기
    # =========================================================

    def _on_page_size_changed(
        self,
        value: str,
    ) -> None:
        try:
            self.page_size = int(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            self.page_size = 10

        self.current_page = 1

        self._display_current_page()

    # =========================================================
    # 이전 페이지
    # =========================================================

    def _previous_page(
        self,
    ) -> None:
        if self.current_page <= 1:
            return

        self.current_page -= 1

        self._display_current_page()

    # =========================================================
    # 다음 페이지
    # =========================================================

    def _next_page(
        self,
    ) -> None:
        total_count = len(
            self.filtered_trades
        )

        if total_count == 0:
            return

        total_pages = (
            total_count
            + self.page_size
            - 1
        ) // self.page_size

        if self.current_page >= total_pages:
            return

        self.current_page += 1

        self._display_current_page()

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
            # =================================================
            # 거래일시
            # =================================================

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

            # =================================================
            # 구분
            # =================================================

            trade_type = str(
                trade.get(
                    "trade_type",
                    "-",
                )
            )

            type_item = QTableWidgetItem(
                trade_type
            )

            type_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            if trade_type == "구매":
                type_item.setForeground(
                    QColor("#2980B9")
                )

            elif trade_type == "판매":
                type_item.setForeground(
                    QColor("#C0392B")
                )

            self.trade_table.setItem(
                row,
                1,
                type_item,
            )

            # =================================================
            # 선수
            # =================================================

            player_name = trade.get(
                "player_name"
            )

            if not player_name:
                player_name = "알 수 없는 선수"

            player_item = QTableWidgetItem(
                str(player_name)
            )

            player_item.setTextAlignment(
                Qt.AlignmentFlag.AlignVCenter
                | Qt.AlignmentFlag.AlignLeft
            )

            self.trade_table.setItem(
                row,
                2,
                player_item,
            )

            # =================================================
            # 시즌 이미지
            # =================================================

            season_url = trade.get(
                "season_img"
            )

            season_label = QLabel()

            season_label.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            season_label.setFixedSize(
                70,
                40,
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

            # =================================================
            # 강화
            # =================================================

            grade = trade.get(
                "grade"
            )

            try:
                grade_level = int(
                    str(grade)
                    .replace(
                        "+",
                        "",
                    )
                    .strip()
                )

            except (
                TypeError,
                ValueError,
            ):
                grade_level = 0

            if (
                1
                <= grade_level
                <= 13
            ):
                grade_text = (
                    f"+{grade_level}"
                )
            else:
                grade_text = "-"

            grade_widget = (
                self._create_grade_widget(
                    grade_level,
                    grade_text,
                )
            )

            self.trade_table.setCellWidget(
                row,
                4,
                grade_widget,
            )

            # =================================================
            # 구매가
            # =================================================

            buy_price = trade.get(
                "buy_price"
            )

            buy_item = QTableWidgetItem(
                self._format_price(
                    buy_price
                )
            )

            buy_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

            self.trade_table.setItem(
                row,
                5,
                buy_item,
            )

            # =================================================
            # 판매가
            # =================================================

            sell_price = trade.get(
                "sell_price"
            )

            sell_item = QTableWidgetItem(
                self._format_price(
                    sell_price
                )
            )

            sell_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

            self.trade_table.setItem(
                row,
                6,
                sell_item,
            )

            # =================================================
            # 현재가
            # =================================================

            current_price = trade.get(
                "current_price"
            )

            current_item = QTableWidgetItem(
                self._format_price(
                    current_price
                )
            )

            current_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

            self.trade_table.setItem(
                row,
                7,
                current_item,
            )

            # =================================================
            # 차액
            # =================================================

            difference = trade.get(
                "difference"
            )

            is_unsold = bool(
                trade.get(
                    "is_unsold",
                    False,
                )
            )

            difference_text = (
                self._format_difference(
                    difference,
                    is_unsold,
                )
            )

            difference_item = QTableWidgetItem(
                difference_text
            )

            difference_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )

            if difference is not None:
                try:
                    difference_value = int(
                        difference
                    )

                    if difference_value > 0:
                        difference_item.setForeground(
                            QColor(
                                "#16A34A"
                            )
                        )

                        difference_item.setFont(
                            self._bold_font()
                        )

                    elif difference_value < 0:
                        difference_item.setForeground(
                            QColor(
                                "#DC2626"
                            )
                        )

                        difference_item.setFont(
                            self._bold_font()
                        )

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

            self.trade_table.setItem(
                row,
                8,
                difference_item,
            )

        for row in range(
            self.trade_table.rowCount()
        ):
            self.trade_table.setRowHeight(
                row,
                50,
            )

    # =========================================================
    # 강화 UI
    # =========================================================

    def _create_grade_widget(
        self,
        grade_level: int,
        grade_text: str,
    ) -> QWidget:
        """
        강화 표시 전용 위젯.

        1강:
            어두운 청색/검정

        2~4강:
            동색

        5~7강:
            은색

        8~10강:
            금색

        11~13강:
            백금색
        """

        container = QFrame()

        container.setObjectName(
            "gradeContainer"
        )

        container.setFixedSize(
            70,
            40,
        )

        container_layout = QHBoxLayout(
            container
        )

        container_layout.setContentsMargins(
            3,
            3,
            3,
            3,
        )

        container_layout.setSpacing(
            0
        )

        badge = QLabel(
            grade_text
        )

        badge.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        badge.setFixedSize(
            64,
            34,
        )

        if grade_level == 1:
            background = "#263746"
            border = "#111820"
            inner = "#52687A"

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

        container.setStyleSheet(
            f"""
            QFrame#gradeContainer {{
                background-color: {background};
                border: 1px solid {border};
                border-radius: 7px;
            }}
            """
        )

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
        try:
            pixmap = QPixmap()

            if not pixmap.loadFromData(
                data
            ):
                label.setText(
                    "-"
                )

                return

            scaled = pixmap.scaled(
                70,
                40,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        
            label.setPixmap(
                scaled
            )
        except RuntimeError:
            # 화면이 새로 그려지면서 QLabel이 삭제된 경우
            # 이미지 표시를 무시한다.
            return

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

    def _update_statistics(
        self,
        trades: list[
            dict[str, Any]
        ],
    ) -> None:
        """현재 필터 결과의 통계를 표시한다."""

        statistics = (
            self.trade_service
            .calculate_statistics(
                trades
            )
        )

        self._display_statistics(
            statistics
        )

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

        difference = statistics.get(
            "difference"
        )

        difference_text = (
            self._format_price(
                difference
            )
        )

        if (
            difference is not None
        ):
            try:
                difference_value = int(
                    difference
                )

                if difference_value > 0:
                    self.difference_label.setStyleSheet(
                        "color: #16A34A;"
                    )

                    difference_text = (
                        "+"
                        + difference_text
                    )

                elif difference_value < 0:
                    self.difference_label.setStyleSheet(
                        "color: #DC2626;"
                    )

            except (
                TypeError,
                ValueError,
            ):
                pass

        self.difference_label.setText(
            "차액: "
            + difference_text
        )

    # =========================================================
    # 금액
    # =========================================================

    @staticmethod
    def _format_price(
        value: Any,
    ) -> str:
        """BP를 보기 좋게 표시한다."""

        if value is None:
            return "-"

        try:
            value = int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return "-"

        if value == 0:
            return "0"

        if value >= 1_000_000_000_000:
            trillion = (
                value
                / 1_000_000_000_000
            )

            return f"{trillion:,.2f}조"

        if value >= 100_000_000:
            hundred_million = (
                value
                / 100_000_000
            )

            return (
                f"{hundred_million:,.2f}억"
            )

        return f"{value:,}"

    # =========================================================
    # 차액
    # =========================================================

    @classmethod
    def _format_difference(
        cls,
        value: Any,
        unsold: bool = False,
    ) -> str:
        """차액을 표시한다."""

        if value is None:
            return "-"

        try:
            value = int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return "-"

        if value > 0:
            result = (
                "+"
                + cls._format_price(
                    value
                )
            )

        elif value < 0:
            result = (
                "-"
                + cls._format_price(
                    abs(value)
                )
            )

        else:
            result = "0"

        if unsold:
            result += " (현재 팔면)"

        return result

    # =========================================================
    # 날짜
    # =========================================================

    @staticmethod
    def _parse_date(
        value: Any,
    ) -> datetime | None:
        """거래일시를 datetime으로 변환한다."""

        if isinstance(
            value,
            datetime,
        ):
            return value

        if not value:
            return None

        value = str(value)

        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(
                    value,
                    fmt,
                )

            except ValueError:
                continue

        try:
            return datetime.fromisoformat(
                value.replace(
                    "Z",
                    "+00:00",
                )
            )

        except ValueError:
            return None

    @staticmethod
    def _format_date(
        value: Any,
    ) -> str:
        """거래일시를 보기 좋게 표시한다."""

        if not value:
            return "-"

        dt = MainWindow._parse_date(
            value
        )

        if dt is None:
            return str(value)

        return dt.strftime(
            "%m-%d %H:%M"
        )

    # =========================================================
    # Font
    # =========================================================

    @staticmethod
    def _bold_font() -> QFont:
        font = QFont()

        font.setBold(
            True
        )

        return font

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

            QFrame#filterFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
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

            QPushButton#searchButton {
                background-color: #374151;
                color: white;
                border: none;
                border-radius: 6px;
                min-height: 30px;
                font-weight: bold;
            }

            QPushButton#searchButton:hover {
                background-color: #1f2937;
            }

            QLineEdit {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 5px;
                padding: 6px 8px;
                min-height: 28px;
            }

            QLineEdit:focus {
                border: 1px solid #2563eb;
            }

            QComboBox {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 5px;
                padding: 5px 8px;
                min-height: 28px;
            }

            QDateEdit {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 5px;
                padding: 5px 8px;
                min-height: 28px;
            }

            QRadioButton {
                spacing: 5px;
                color: #374151;
            }

            QRadioButton::indicator {
                width: 14px;
                height: 14px;
            }

            QTableWidget {
                background-color: white;
                alternate-background-color: #f9fafb;
                border: none;
                gridline-color: #e5e7eb;
                font-size: 13px;
            }

            QTableWidget::item {
                padding: 5px;
            }

            QTableWidget::item:selected {
                background-color: #dbeafe;
                color: #111827;
            }

            QHeaderView::section {
                background-color: #f3f4f6;
                color: #374151;
                font-size: 13px;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #d1d5db;
                padding: 9px;
            }

            QStatusBar {
                color: #6b7280;
            }

            QFrame#gradeContainer {
                margin: 0px;
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

        for loader in self.image_loaders:
            try:
                loader.quit()
                loader.wait(1000)
            except Exception:
                pass

        self.image_loaders.clear()

        event.accept()