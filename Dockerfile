# Start from a base image with Python installed
FROM python:3.9-slim-buster

# Set a working directory
WORKDIR /app

# Install the Tk library and mupdf
RUN apt-get update && apt-get install -y tk mupdf

# Copy your application code to the Docker image
COPY . /app

# Install your Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set Password
ENV admin_passwort='mypassword'

# Set the command to run your application
CMD ["python", "Kassensystem.py"]