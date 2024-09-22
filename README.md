# Hynfratech Assessment Project

This project is a Django-based web application for managing virtual machines (VMs) and user accounts. It includes features for VM management, user authentication, and subscription handling.

## Project Structure

The project consists of two main Django apps:

1. `accounts`: Handles user authentication and management
2. `vm_management`: Manages VMs, subscriptions, and payments

## Technologies Used

- Django
- PostgreSQL
- Nginx
- Docker
- Kubernetes

## Setup and Installation

### Prerequisites

- Docker
- Docker Compose (for container management)
- Kubernetes (for deployment)
- Minikube (for creating Kubernetes clusters locally)
- VirtualBox (for Minikube and virtual machine management)
- Nginx (for reverse proxy setup)
- Certbot (for SSL certificate management)
- PostgreSQL (Optional, since the database is managed as a Docker container)
  
You can find the detailed commands to install these prerequisites in the `vps_setup_commands.sh` script located in the repository.

Here is a summary of the tools installed via the script:

- **Docker**: 
  Used for containerizing applications.
  
- **Docker Compose**: 
  For defining and running multi-container Docker applications.

- **Kubernetes (kubectl)**: 
  Installed via Snap for managing Kubernetes clusters.

- **Minikube**: 
  Allows you to create and manage a local Kubernetes cluster for development.

- **VirtualBox**: 
  Required by Minikube for running Kubernetes in a virtualized environment.

- **PostgreSQL** (Optional): 
  Installed as a backup database option; the default setup uses a PostgreSQL container.

- **Nginx**: 
  Used as a reverse proxy for deploying your application in production.

- **Certbot**: 
  Automates the process of obtaining and renewing SSL certificates for your Nginx setup.

To install these tools, you can run the commands provided in `vps_setup_commands.sh`:

```bash
# Run the setup commands from the script
bash vps_setup_commands.sh
```

### Local Development

1. Clone the repository:
   ```
   git clone <repository-url>
   cd hynfratech_assessment
   ```

2. Build and run the Docker containers:
   ```
   docker-compose up --build
   ```

3. Access the application at `http://localhost:8000`

### Deployment

The project includes Kubernetes deployment files:

- `django-deployment.yml`: Deploys the Django application
- `postgres-deployment.yml`: Deploys the PostgreSQL database
- `pvc.yml`: Sets up persistent volume claims

To deploy:

1. Apply the Kubernetes configurations:
   ```
   kubectl apply -f pvc.yml
   kubectl apply -f postgres-deployment.yml
   kubectl apply -f django-deployment.yml
   ```

2. Set up SSH access (if required):
   ```
   ./setup_ssh.sh
   ```

## CI/CD Pipeline

Our project uses an automated CI/CD pipeline to streamline the development and deployment process.

### CI Pipeline

1. **Version Control**: Git is used for version control, with the primary repository hosted on GitHub.
   
2. **Automated Testing**: Every push to the `master` branch triggers GitHub Actions:
   - Unit tests for the `accounts` and `vm_management` apps.
   - Integration tests to ensure all components work together.
   - Code linting using `flake8` to maintain code standards.

3. **Environment Setup**: 
   - A PostgreSQL service is set up during the CI process using Docker to run database-related tests.
   - An `.env` file is automatically generated from GitHub secrets.

4. **Docker Image Build**: After passing the tests:
   - A Docker image is built using the latest code.
   - The image is tagged with the `latest` tag.

5. **SonarQube**: Static code analysis is run to check for potential bugs, security vulnerabilities, and code smells.

### CD Pipeline

1. **Docker Image Push**: Upon successful builds, the Docker image is pushed to Docker Hub.

2. **SSH Key Setup**: GitHub Actions uses an SSH key for passwordless access to the VPS.

3. **Repository Update**: The remote repository is cloned or updated on the VPS.

4. **Environment Setup on VPS**:
   - The `.env` file is securely uploaded to the server.
   - Docker Compose is run on the server to start or restart services.

5. **Deployment**: 
   - The Docker Compose file is executed remotely, ensuring all services are deployed correctly.
   - If updates are needed, the Docker containers are restarted.

By using this CI/CD pipeline, our development and deployment processes are automated and efficient, ensuring code quality and a seamless update process.


### Secrets Management

- Github Actions Secrets are used to manage sensitive information like database passwords and API keys.

## Deployment Process with Kubernetes

1. **Initial Setup**: 
   ```
   kubectl apply -f pvc.yml
   kubectl apply -f postgres-deployment.yml
   kubectl apply -f django-deployment.yml
   ```

2. **Updating the Application**:
   - CI/CD pipeline automatically updates the `django-deployment.yml` with the new image tag.
   - Apply the updated deployment:
     ```
     kubectl apply -f django-deployment.yml
     ```
   - Kubernetes performs a rolling update, ensuring zero downtime.

3. **Rollback** (if necessary):
   ```
   kubectl rollout undo deployment/django-deployment
   ```

4. **Scaling**:
   - Manual scaling:
     ```
     kubectl scale deployment django-deployment --replicas=3
     ```
   - Automatic scaling is handled by the Horizontal Pod Autoscaler


## Deployment Process with Docker & Nginx

### 1. Initial Setup

To deploy using Docker Compose:
On the server, navigate to the project directory and run the following:

```bash
sudo docker-compose up -d
```

This will spin up the necessary containers for the application (Django, PostgreSQL, etc.).

### 2. Nginx Configuration

Ensure that Nginx is configured correctly to listen for the Docker containers. A sample Nginx configuration file might look like this:

```nginx
server {
    server_name hynfratech.botontapwater.com;

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:8000; # Gunicorn listens on this port
    }

    location /static/ {
        alias /home/lab/hynfratech_assessment/static/;
    }

    location /media/ {
        alias /home/lab/hynfratech_assessment/media/;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/hynfratech.botontapwater.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/hynfratech.botontapwater.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

server {
    if ($host = hynfratech.botontapwater.com) {
        return 301 https://$host$request_uri;
    }

    server_name hynfratech.botontapwater.com;
    listen 80;
    return 404; # managed by Certbot
}
```

### 3. Updating the Application

When you need to update the application:

Pull the latest changes from your repository:
```bash
git pull
```

Restart the Docker containers:
```bash
sudo docker-compose down
sudo docker-compose up -d
```

### 4. SSL and Security

Nginx is configured with SSL certificates managed by Certbot. To ensure the certificates are kept up to date, use the following command:

```bash
sudo certbot renew
```

## Project Configuration

- Django settings are in `hynfratech_assessment/settings.py`
- Nginx configuration is in `nginx/nginx.conf`
- Docker configuration is in `Dockerfile` and `docker-compose.yml`

## Static Files

Static files (CSS, images, etc.) are stored in the `static` directory.

## Management Commands

Custom management commands can be added in `vm_management/management/commands/`.

## Testing

Run tests using:
```
python manage.py test
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

MIT License

Copyright (c) [2024] [Brandon Munda]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Contact

[www.botontapwater.com](https://www.botontapwater.com)

[www.brandonmunda.me](https://www.brandonmunda.me)