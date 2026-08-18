from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.api_key_storage import APIKeyStorage
from app.services.nexon_client import NexonAPIError, NexonClient


class LoginWindow(QWidget):
    """FC Online 로그인 화면."""

    def __init__(self) -> None:
        super().__init__()

        self.api_key_storage = APIKeyStorage()
        self.authenticated_api_key: str | None = None
        self.main_window = None

        self.setWindowTitle(
            "FC Online Personal Tool - 로그인"
        )
        self.setFixedSize(500, 450)

        self._setup_ui()
        self._apply_style()
        self._load_saved_api_key()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            50,
            40,
            50,
            40,
        )

        main_layout.setSpacing(12)

        # 제목
        title_label = QLabel("FC Online")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        subtitle_label = QLabel("Personal Tool")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)

        main_layout.addSpacing(20)

        # 로그인 영역
        login_frame = QFrame()
        login_frame.setObjectName("loginFrame")

        login_layout = QVBoxLayout(login_frame)

        login_layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        login_layout.setSpacing(10)

        # API KEY
        api_key_label = QLabel("NEXON API KEY")
        api_key_label.setObjectName("inputLabel")

        self.api_key_input = QLineEdit()
        self.api_key_input.setObjectName(
            "apiKeyInput"
        )

        self.api_key_input.setPlaceholderText(
            "NEXON Open API KEY를 입력하세요"
        )

        self.api_key_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.api_key_input.setMinimumHeight(42)

        login_layout.addWidget(api_key_label)
        login_layout.addWidget(
            self.api_key_input
        )

        # 닉네임
        nickname_label = QLabel(
            "FC Online 닉네임"
        )

        nickname_label.setObjectName(
            "inputLabel"
        )

        self.nickname_input = QLineEdit()
        self.nickname_input.setObjectName(
            "nicknameInput"
        )

        self.nickname_input.setPlaceholderText(
            "FC Online 닉네임을 입력하세요"
        )

        self.nickname_input.setMinimumHeight(42)

        login_layout.addSpacing(8)

        login_layout.addWidget(
            nickname_label
        )

        login_layout.addWidget(
            self.nickname_input
        )

        # 로그인 버튼
        self.login_button = QPushButton(
            "로그인"
        )

        self.login_button.setObjectName(
            "loginButton"
        )

        self.login_button.setMinimumHeight(42)

        login_layout.addSpacing(8)

        login_layout.addWidget(
            self.login_button
        )

        # API KEY 삭제
        self.delete_key_button = QPushButton(
            "저장된 API KEY 삭제"
        )

        self.delete_key_button.setObjectName(
            "deleteKeyButton"
        )

        self.delete_key_button.setVisible(
            False
        )

        login_layout.addWidget(
            self.delete_key_button
        )

        # 상태
        self.status_label = QLabel("")

        self.status_label.setObjectName(
            "statusLabel"
        )

        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status_label.setWordWrap(True)

        login_layout.addWidget(
            self.status_label
        )

        main_layout.addWidget(
            login_frame
        )

        # 이벤트
        self.login_button.clicked.connect(
            self._on_login_clicked
        )

        self.api_key_input.returnPressed.connect(
            self._on_login_clicked
        )

        self.nickname_input.returnPressed.connect(
            self._on_login_clicked
        )

        self.delete_key_button.clicked.connect(
            self._on_delete_key_clicked
        )

    def _load_saved_api_key(self) -> None:
        """저장된 API KEY를 불러온다."""

        saved_api_key = (
            self.api_key_storage.load()
        )

        if not saved_api_key:
            return

        self.api_key_input.setText(
            saved_api_key
        )

        self.delete_key_button.setVisible(
            True
        )

        self.status_label.setText(
            "저장된 API KEY가 있습니다."
        )

        self.nickname_input.setFocus()

    def _on_login_clicked(self) -> None:
        """로그인 버튼 처리."""

        api_key = (
            self.api_key_input.text().strip()
        )

        nickname = (
            self.nickname_input.text().strip()
        )

        # API KEY 확인
        if not api_key:
            QMessageBox.warning(
                self,
                "API KEY 필요",
                "NEXON API KEY를 입력해주세요.",
            )

            self.api_key_input.setFocus()

            return

        # 닉네임 확인
        if not nickname:
            QMessageBox.warning(
                self,
                "닉네임 필요",
                "FC Online 닉네임을 입력해주세요.",
            )

            self.nickname_input.setFocus()

            return

        self._set_login_enabled(False)

        self.status_label.setText(
            "NEXON API KEY를 확인하는 중입니다..."
        )

        try:
            client = NexonClient(
                api_key
            )

            # 1. 닉네임 → OUID
            ouid = client.get_ouid(
                nickname
            )

            # 2. OUID → 기본 유저 정보
            client.get_user_info(
                ouid
            )

            # 실제 API 요청이 성공했으므로
            # API KEY를 저장한다.
            self.api_key_storage.save(
                api_key
            )

            self.authenticated_api_key = (
                api_key
            )

            self.status_label.setText(
                "로그인 성공"
            )

            self._open_main_window(
                api_key
            )

        except NexonAPIError as error:
            self._set_login_enabled(True)

            self.status_label.setText(
                "로그인에 실패했습니다."
            )

            QMessageBox.critical(
                self,
                "로그인 실패",
                str(error),
            )

        except ValueError as error:
            self._set_login_enabled(True)

            QMessageBox.warning(
                self,
                "입력 오류",
                str(error),
            )

        except OSError as error:
            self._set_login_enabled(True)

            QMessageBox.critical(
                self,
                "저장 오류",
                f"API KEY를 저장하지 못했습니다.\n\n"
                f"{error}",
            )

        except Exception as error:
            self._set_login_enabled(True)

            QMessageBox.critical(
                self,
                "오류",
                "예상하지 못한 오류가 발생했습니다.\n\n"
                f"{error}",
            )

    def _set_login_enabled(
        self,
        enabled: bool,
    ) -> None:
        """로그인 입력 컨트롤 활성화 상태."""

        self.login_button.setEnabled(
            enabled
        )

        self.api_key_input.setEnabled(
            enabled
        )

        self.nickname_input.setEnabled(
            enabled
        )

    def _on_delete_key_clicked(self) -> None:
        """저장된 API KEY 삭제."""

        answer = QMessageBox.question(
            self,
            "API KEY 삭제",
            "저장된 API KEY를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            self.api_key_storage.delete()

            self.api_key_input.clear()

            self.authenticated_api_key = None

            self.delete_key_button.setVisible(
                False
            )

            self.status_label.setText(
                "저장된 API KEY가 삭제되었습니다."
            )

            self.api_key_input.setFocus()

        except OSError as error:
            QMessageBox.critical(
                self,
                "삭제 오류",
                f"API KEY를 삭제하지 못했습니다.\n\n"
                f"{error}",
            )

    def _open_main_window(
        self,
        api_key: str,
    ) -> None:
        """로그인 성공 후 메인 화면을 연다."""

        from app.ui.main_window import MainWindow

        self.main_window = MainWindow(
            api_key=api_key
        )

        self.main_window.show()

        self.close()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background-color: #f5f6f8;
            }

            QLabel#titleLabel {
                font-size: 30px;
                font-weight: bold;
                color: #202124;
            }

            QLabel#subtitleLabel {
                font-size: 15px;
                color: #6b7280;
            }

            QFrame#loginFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }

            QLabel#inputLabel {
                font-size: 14px;
                font-weight: bold;
                color: #374151;
            }

            QLineEdit#apiKeyInput,
            QLineEdit#nicknameInput {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 0 12px;
                font-size: 14px;
            }

            QLineEdit#apiKeyInput:focus,
            QLineEdit#nicknameInput:focus {
                border: 1px solid #2563eb;
            }

            QPushButton#loginButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton#loginButton:hover {
                background-color: #1d4ed8;
            }

            QPushButton#loginButton:disabled {
                background-color: #93c5fd;
            }

            QPushButton#deleteKeyButton {
                background-color: transparent;
                color: #6b7280;
                border: none;
                font-size: 12px;
            }

            QPushButton#deleteKeyButton:hover {
                color: #dc2626;
            }

            QLabel#statusLabel {
                color: #6b7280;
                font-size: 12px;
            }
            """
        )