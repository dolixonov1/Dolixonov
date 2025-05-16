# --- Python + ffmpeg Dockerfile for Telegram Bot ---
FROM python:3.11-slim

# Install ffmpeg and other dependencies
RUN apt-get update \
    && apt-get install -y ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy project files
COPY . /app

# Install python dependencies
RUN pip install --no-cache-dir -r telegram-bot/requirements.txt

# Expose port if needed (for webhooks, optional)
# EXPOSE 8080

# Start the bot
CMD ["python", "telegram-bot/main.py"]
