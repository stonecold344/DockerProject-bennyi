FROM mongo:7.0.14

# Install legacy mongo shell
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | apt-key add - \
    && echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/debian buster/mongodb-org/4.4 main" | tee /etc/apt/sources.list.d/mongodb-org-4.4.list \
    && apt-get update && apt-get install -y mongodb-org-shell=4.4.18 \
    && rm -rf /var/lib/apt/lists/*

# Install mongosh
RUN curl -LO https://downloads.mongodb.com/compass/mongodb-mongosh_1.10.1_amd64.deb \
    && dpkg -i mongodb-mongosh_1.10.1_amd64.deb
