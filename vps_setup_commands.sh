sudo apt-get install docker
sudo apt-get install docker-compose
sudo systemctl enable docker
sudo systemctl start docker
snap install kubectl --classic

curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64
# minikube start

# sudo apt install virtualbox

# wget -4 -O- https://www.virtualbox.org/download/oracle_vbox_2016.asc | sudo gpg --yes --output /usr/share/keyrings/oracle-virtualbox-2016.gpg --dearmor
# echo "deb [signed-by=/usr/share/keyrings/oracle-virtualbox-2016.gpg] https://download.virtualbox.org/virtualbox/debian jammy contrib" | sudo tee /etc/apt/sources.list.d/virtualbox.list
# sudo apt-get update
# sudo apt-get install virtualbox-6.1

sudo apt-get install virtualbox-7.1



sudo service virtualbox start
sudo usermod -aG docker 
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql

sudo apt-get install certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx
sudo certbot renew --dry-run
sudo certbot --nginx -d hynfrapersonal.botontapwater.com --non-interactive --agree-tos --email mundabrandon@outlook.com --redirect

sudo systemctl restart nginx

# sudo apt-get install -y conntrack

# VERSION="v1.27.0" # Update to the latest version if needed
# wget https://github.com/kubernetes-sigs/cri-tools/releases/download/${VERSION}/crictl-${VERSION}-linux-amd64.tar.gz
# tar -zxvf crictl-${VERSION}-linux-amd64.tar.gz
# sudo mv crictl /usr/local/bin/

sudo apt update
gunicorn --workers 3 hynfratech_assessment.wsgi:application
# sudo apt install postgresql postgresql-contrib

sudo chmod +x /home/lab
sudo chmod +x /home/lab/hynfratech_assessment


# sudo systemctl start postgresql
# sudo systemctl enable postgresql

CREATE DATABASE hynfratech;
CREATE USER botontapwater WITH PASSWORD 'TwoGreen1.';
GRANT ALL PRIVILEGES ON DATABASE hynfratech TO botontapwater;

sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose