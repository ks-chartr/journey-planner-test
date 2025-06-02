import os

from dotenv import load_dotenv

from core.settings import ENV_DIR

COMMON_ENV_PATH = os.path.join(ENV_DIR, ".env.modules.common.dev")
load_dotenv(COMMON_ENV_PATH)

# Common environment variables
LOCATION = os.getenv("LOCATION")
X_API_KEY = os.getenv("X_API_KEY")
