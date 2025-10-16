FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# (optional) build tools if you compile deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir "alembic>=1.13" "SQLAlchemy>=2" "psycopg[binary]>=3" "uvicorn[standard]>=0.30"

COPY . /app

# default run for the api service; migrate overrides this with its own command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
