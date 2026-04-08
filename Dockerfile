FROM python:3.11-slim

# Create an unprivileged user — never run the app as root.
RUN groupadd --system veritas && \
    useradd  --system --gid veritas --create-home --shell /usr/sbin/nologin veritas

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chown -R veritas:veritas /app

USER veritas

CMD ["python", "demo.py"]
