FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    curl wget unzip gnupg2 libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libgtk-3-0 libxss1 fonts-liberation xdg-utils \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
      | gpg --dearmor -o /usr/share/keyrings/google.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/google.gpg] \
      http://dl.google.com/linux/chrome/deb/ stable main" \
      > /etc/apt/sources.list.d/google.list && \
    apt-get update && apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Install ChromeDriver (exact match to Chrome 136.0.7103.113)
RUN CHROMEDRIVER_VERSION=136.0.7103.113 && \
    wget -q -O /tmp/chromedriver.zip \
      "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip -j /tmp/chromedriver.zip -d /usr/local/bin chromedriver-linux64/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "bot.py"]
