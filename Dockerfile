# Use Python 3.10 as base image
FROM python:3.10

# Set working directory
WORKDIR /app

# Install system dependencies for Chrome and drivers
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxi6 \
    libxtst6 \
    libxrandr2 \
    libxss1 \
    libxrender1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libgtk-3-0 \
    xvfb \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create directories for the application
RUN mkdir -p /app/logs /app/output /app/output/images

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create .env file if it doesn't exist (will be overridden by volume mount)
RUN touch .env

# Set up virtual display for Chrome
ENV DISPLAY=:99

# Set environment variable for headless mode
ENV HEADLESS=True

# Set up entrypoint
CMD ["sh", "-c", "Xvfb :99 -screen 0 1280x1024x24 -ac +extension GLX +render -noreset & python main.py"]