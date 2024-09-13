# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app/

# Install OpenSSH client for ssh-keygen
RUN apt-get update && apt-get install -y openssh-client

# Add host key to known_hosts
# RUN ssh-keyscan -H 192.168.1.191 >> /root/.ssh/known_hosts

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Collect static files
RUN python manage.py collectstatic --noinput

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the wait-for-it script to wait for the database to be ready before starting gunicorn
# CMD ["gunicorn", "--bind", "0.0.0.0:8000", "hynfratech_assessment.wsgi:application"]

# Run migrations before starting the application
CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 hynfratech_assessment.wsgi:application"]