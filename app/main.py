import sys

from PySide6.QtWidgets import QApplication

from app.ui.login_window import LoginWindow


def main() -> int:
    app = QApplication(sys.argv)

    app.setApplicationName("FC Online Personal Tool")
    app.setOrganizationName("jmh0856")

    login_window = LoginWindow()
    login_window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())