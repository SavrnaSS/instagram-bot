FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget unzip gnupg curl fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libnspr4 libnss3 libxss1 libxcomposite1 libxdamage1 libxrandr2 xdg-utils libgbm-dev libgtk-3-0 && \
    rm -rf /var/lib/apt/lists/*

# Install Chrome 136
RUN wget -O chrome.deb "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" && \
    apt install -y ./chrome.deb && \
    rm chrome.deb

# Install ChromeDriver 136
RUN CHROMEDRIVER_VERSION=136.0.7103.113 && \
    wget -O /tmp/cd.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/cd.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && rm /tmp/cd.zip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run the bot
CMD ["python", "bot.py"]
