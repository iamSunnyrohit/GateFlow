import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = "GateFlow API Gateway"

    HOST: str = os.getenv("GATEWAY_HOST", "0.0.0.0")

    PORT: int = int(os.getenv("GATEWAY_PORT", "8000"))

    USER_SERVICE_URL: str = os.getenv(
        "USER_SERVICE_URL",
        "http://localhost:8002"
    )

    REQUEST_TIMEOUT: float = float(
        os.getenv("REQUEST_TIMEOUT", "10")
    )


settings = Settings()
