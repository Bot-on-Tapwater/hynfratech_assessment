#!/bin/sh

# Ensure SSH directory exists and permissions are correct
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Ensure private key has correct permissions
chmod 600 ~/.ssh/id_rsa

# Add known hosts or any other SSH configuration needed
