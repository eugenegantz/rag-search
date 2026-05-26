import core.types

config: core.types.TConfig = {
    # Настройки подключения к LLM. OpenAI-совместимый протокол.
    "openai": {
        # URL подключения API.
        "base_url": "https://OPENAI_COMPATIBLE_API_ENDPOINT",

        # Токен подключения к API. Выдается поставщиком LLM.
        # Внимание это чувствительная информация. Не подлежит разглашению.
        "api_key": "WRITE_API_KEY_HERE",

        # Особые заголовки для подключения (если необходимо, опционально).
        # "default_headers": {
        #     "User-Agent": "WRITE_CUSTOM_USER_AGENT_HERE", # OPTIONAL
        # },
    },

    # Настройки веб-сервера (фоновый процесс, демон)
    "daemon": {
        "host": "127.0.0.1",
        "port": 8367,
    },

    # Настройки torchvision
    "torchvision": {
        "device_map": "auto",
    },

    # Настройки transformer
    "embeddings": {
        "device_map": "auto",
    },
}