# Update package list
sudo apt update


# Docker installation
sudo apt-get install docker
sudo systemctl enable docker
sudo systemctl start docker

# Docker-compose installation (Option 1)
sudo apt-get install docker-compose


# Docker-compose installation (Option 1)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Kubernetes installation | Kubectl
snap install kubectl --classic

# Minikube installation (Required for creating kubernetes clusters locally)
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64
minikube start

# Virtualbox installation (Gives access to vboxmanage command line tool)
sudo apt-get install virtualbox-7.1
sudo service virtualbox start

# Postgres installation (Not necessary since the db is run as a docker container)
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql

    # Run these in psql (sudo su postgres; psql;) - Not necessary DB is setup in container
    CREATE DATABASE hynfratech;
    CREATE USER botontapwater WITH PASSWORD 'TwoGreen1.';
    GRANT ALL PRIVILEGES ON DATABASE hynfratech TO botontapwater;

# Nginx reverse proxy installation (Necessary for deployment)
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl restart nginx

# Certbot installation and setup (For installing SSL certificates)
sudo certbot --nginx
sudo certbot renew --dry-run
sudo certbot --nginx -d hynfratech.botontapwater.com --non-interactive --agree-tos --email mundabrandon@outlook.com --redirect

# Allows nginx to access and serve static files in our repo
sudo chmod +x /home/lab
sudo chmod +x /home/lab/hynfratech_assessment

# Command to let you send any missing files to the repo
scp -P 2112 <local_file_path> lab@102.209.68.78:/home/lab/hynfratech_assessment/
