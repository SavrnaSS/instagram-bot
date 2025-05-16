FROM python:3.10-slim

# Install only what instagrapi needs (mostly build tools for cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
     build-essential libffi-dev libssl-dev git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
