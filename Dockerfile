# Use Selenium's official Chrome image with driver pre-installed
FROM selenium/standalone-chrome:latest

# Set environment variables to avoid warnings
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Switch to root to install packages
USER root

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Copy all project files
COPY . /app

# Install required Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Default command to run the bot
CMD ["python3", "bot.py"]
