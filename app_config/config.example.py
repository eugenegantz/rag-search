import core.types

config: core.types.TConfig = {
    "openai": {
        "base_url": "https://OPENAI_COMPATIBLE_API_ENDPOINT",
        "api_key": "WRITE_API_KEY_HERE",
        "default_headers": {
            "User-Agent": "WRITE_CUSTOM_USER_AGENT_HERE", # OPTIONAL
        },
    },
    "daemon": {
        "host": "127.0.0.1",
        "port": 8367,
    }
}