import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "data/links.db")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
CODE_LENGTH = int(os.getenv("CODE_LENGTH", "6"))
