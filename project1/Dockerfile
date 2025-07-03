 # 1. Base Python image
FROM python:3.10

# 2. Set working directory inside container
WORKDIR /app

# 3. Copy all files from your folder into the container
COPY . .

# 4. Install all dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5. Expose port 8000 for FastAPI
EXPOSE 8000

# 6. Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
