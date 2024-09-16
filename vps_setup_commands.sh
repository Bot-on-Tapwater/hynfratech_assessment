sudo apt-get install docker
sudo apt-get install docker-compose
sudo systemctl enable docker
sudo systemctl start docker
snap install kubectl --classic

curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64
# minikube start

sudo apt install virtualbox
sudo service virtualbox start
sudo usermod -aG docker 
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql

sudo apt-get install certbot


# sudo apt-get install -y conntrack

# VERSION="v1.27.0" # Update to the latest version if needed
# wget https://github.com/kubernetes-sigs/cri-tools/releases/download/${VERSION}/crictl-${VERSION}-linux-amd64.tar.gz
# tar -zxvf crictl-${VERSION}-linux-amd64.tar.gz
# sudo mv crictl /usr/local/bin/

sudo apt update
sudo apt install postgresql postgresql-contrib

sudo systemctl start postgresql
sudo systemctl enable postgresql

CREATE DATABASE hynfratech;
CREATE USER botontapwater WITH PASSWORD 'TwoGreen1.';
GRANT ALL PRIVILEGES ON DATABASE hynfratech TO botontapwater;

sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose