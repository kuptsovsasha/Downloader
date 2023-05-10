# Base image
FROM python:3.9

# Install Supervisor
RUN apt-get update && apt-get install -y supervisor

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy the entire project to the container
COPY . .

# Copy the Supervisor configuration file
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose the necessary port (Flask default is 5000)
EXPOSE 5000

# Run Supervisor to manage the Flask app and Celery worker
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
