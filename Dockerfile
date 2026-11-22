FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN useradd --create-home appuser \
    && chown -R appuser /app
USER appuser

EXPOSE 8000

# apply pending migrations on every start (DB settings only exist at runtime),
# then hand the process over to gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn infiniting.wsgi:application --bind 0.0.0.0:${PORT} --workers 3"]
