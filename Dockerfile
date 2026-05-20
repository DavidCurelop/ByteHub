FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY --chown=appuser:appgroup requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY --chown=appuser:appgroup . /app

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

RUN mkdir -p /app/ByteHub/staticfiles && chmod -R 755 /app/ByteHub/staticfiles

USER appuser

WORKDIR /app/ByteHub

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
