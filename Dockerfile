# Python 3.10 asosida
FROM python:3.10-slim

# Sistem kerakli kutubxonalar
RUN apt-get update && apt-get install -y \
    wget curl unzip tesseract-ocr \
    libglib2.0-0 libnss3 libgconf-2-4 libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0 libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Chrome va undetected-chromedriver uchun zaruriy sozlashlar
RUN apt-get update && apt-get install -y gnupg ca-certificates && \
    curl -fsSL https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable

# Loyihani konteynerga ko'chirish
WORKDIR /app
COPY . /app

# Python kutubxonalarini o‘rnatish
RUN pip install --upgrade pip && pip install -r requirements.txt

# GPU bo‘lsa, paddle avtomatik tanlaydi, bo‘lmasa CPU bilan ishlaydi.
ENV CUDA_VISIBLE_DEVICES=""

# Port va boshqa sozlashlar kerak bo‘lsa shu yerda qo‘shish mumkin

# Loyihani ishga tushirish
CMD ["python", "main.py"]
