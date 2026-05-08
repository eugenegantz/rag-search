import sys
from pathlib import Path

_CONFIG_DIR = Path(__file__).parent
_CONFIG_FILE = _CONFIG_DIR / "config.py"
_CONFIG_EXAMPLE = _CONFIG_DIR / "config.example.py"

if not _CONFIG_FILE.exists():
    if not _CONFIG_EXAMPLE.exists():
        print(
            "[ОШИБКА] Файл конфигурации app_config/config.py не найден, "
            "и отсутствует эталонный файл app_config/config.example.py."
        )
        sys.exit(1)

    _CONFIG_FILE.write_text(_CONFIG_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")

    print(
        "\n"
        "========================================\n"
        "  Создан файл конфигурации:\n"
        f"  {_CONFIG_FILE}\n"
        "========================================\n"
        "\n"
        "Пожалуйста, укажите в нем обязательные параметры:\n"
        "  - api_key\n"
        "  - base_url\n"
        "\n"
        "После заполнения перезапустите программу.\n"
    )
    sys.exit(1)
