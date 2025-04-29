#!/bin/bash

# Agar .db fayl yo'q bo'lsa, yaratamiz
if [ ! -f /app/product_data.db ]; then
  touch /app/product_data.db
fi

# Asosiy dastur
python main.py
