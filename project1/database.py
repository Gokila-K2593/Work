from sqlmodel import create_engine
import os

# Get DB URL from docker-compose environment
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)
