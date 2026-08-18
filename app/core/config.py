from pathlib import Path


class Settings:
    """FC Online Personal Tool 애플리케이션 설정."""

    APP_NAME = "FC Online Personal Tool"
    APP_VERSION = "1.0.0"

    NEXON_API_BASE_URL = "https://open.api.nexon.com/fconline/v1"

    REQUEST_TIMEOUT = 10.0

    # 사용자 설정 저장 위치
    APP_DATA_DIR = (
        Path.home()
        / "AppData"
        / "Local"
        / "FCOnlinePersonalTool"
    )

    API_KEY_FILE = APP_DATA_DIR / "api_key"

    @classmethod
    def ensure_data_directory(cls) -> None:
        """사용자 설정 폴더를 생성한다."""
        cls.APP_DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )


settings = Settings()