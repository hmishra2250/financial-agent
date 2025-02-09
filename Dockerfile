# Use a smaller Python base image
FROM python:3.10-slim

# Set environment variables for a smaller image
ENV PYTHONUNBUFFERED=1 \
    PYTHONPYCACHEPREFIX=/tmp/pycache \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install CPU-only PyTorch
RUN pip install --no-cache-dir \
    torch==2.6.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Copy only required files
COPY requirements.txt .

# Install dependencies in a single layer & remove cache
RUN pip install --no-cache-dir -r requirements.txt

# Install SentenceTransformer model
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2').save('model')"

# Copy the rest of the app
COPY . .

# Define the startup command
CMD ["python", "main.py"]