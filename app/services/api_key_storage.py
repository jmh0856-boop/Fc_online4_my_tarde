from pathlib import Path

from app.core.config import settings


class APIKeyStorage:
    """사용자의 NEXON API KEY를 로컬에 저장하고 관리한다."""

    def __init__(self) -> None:
        settings.ensure_data_directory()

        self._file_path: Path = settings.API_KEY_FILE

    def save(self, api_key: str) -> None:
        """API KEY를 저장한다."""
        api_key = api_key.strip()

        if not api_key:
            raise ValueError("API KEY가 비어 있습니다.")

        self._file_path.write_text(
            api_key,
            encoding="utf-8",
        )

    def load(self) -> str | None:
        """저장된 API KEY를 불러온다."""
        if not self._file_path.exists():
            return None

        api_key = self._file_path.read_text(
            encoding="utf-8"
        ).strip()

        return api_key or None

    def delete(self) -> None:
        """저장된 API KEY를 삭제한다."""
        if self._file_path.exists():
            self._file_path.unlink()

    def exists(self) -> bool:
        """저장된 API KEY가 존재하는지 확인한다."""
        return self._file_path.exists()