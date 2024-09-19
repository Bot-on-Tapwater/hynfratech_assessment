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
- Kubernetes (for deployment)

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

Our project uses a robust CI/CD pipeline to ensure smooth development and deployment processes.

### CI Pipeline

1. **Version Control**: We use Git for version control, with the main repository hosted on GitHub.

2. **Automated Testing**: On every push to the repository, GitHub Actions triggers our test suite:
   - Unit tests for both `accounts` and `vm_management` apps
   - Integration tests to ensure proper interaction between components
   - Code linting using flake8 to maintain code quality

3. **Code Quality Checks**: SonarQube is integrated to perform static code analysis, identifying potential bugs, code smells, and security vulnerabilities.

4. **Docker Image Building**: If all tests pass, a Docker image is automatically built and tagged with the commit SHA.

### CD Pipeline

1. **Image Push**: The Docker image is pushed to our private Docker registry.

2. **Deployment Trigger**: Successful image push triggers the deployment process.

3. **Kubernetes Deployment**: Our Kubernetes cluster is updated using the following process:
   - The `django-deployment.yml` file is automatically updated with the new image tag.
   - Kubernetes applies the updated deployment file, performing a rolling update to ensure zero downtime.

## Kubernetes Deployment Details

Our application is deployed on a Kubernetes cluster for scalability and ease of management.

### Kubernetes Resources

1. **Persistent Volumes**: Defined in `pvc.yml`, these ensure data persistence across pod restarts.

2. **PostgreSQL Deployment**: `postgres-deployment.yml` sets up the database service:
   - Uses a StatefulSet for stable network identities
   - Configures resource limits and requests
   - Sets up environment variables for database initialization

3. **Django Application Deployment**: `django-deployment.yml` deploys our main application:
   - Defines resource limits and requests
   - Sets up environment variables, including database connection details
   - Configures liveness and readiness probes for better reliability
   - Sets up an ingress for external access

4. **Nginx Ingress**: Configured to route traffic to our Django service and handle SSL termination.

### Scaling

- Horizontal Pod Autoscaler (HPA) is set up to automatically scale the number of Django pods based on CPU utilization.

### Monitoring and Logging

- Prometheus is used for monitoring the Kubernetes cluster and application metrics.
- ELK stack (Elasticsearch, Logstash, Kibana) is employed for centralized logging.

### Secrets Management

- Kubernetes Secrets are used to manage sensitive information like database passwords and API keys.

## Deployment Process

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

www.botontapwater.com