# Send email using Gmail

1. Read quickstart [google workspace gmail api](https://developers.google.com/workspace/gmail/api/quickstart/python)
1. Read code [google api sending email](https://developers.google.com/workspace/gmail/api/guides/sending#python)

## Quickstart

```bash
# setup .env file, refer to env section for params
touch .env
# load your google_credential.json into ./creds
mkdir creds
# run python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Env

```bash
# .env
send_email_target='user@someemail.com'
```

## Debian OS

```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install libssl-dev openssl
sudo apt install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils
     tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
cd ~/downloads
# Python.org: 3.12.10
wget https://www.python.org/ftp/python/3.12.10/Python-3.12.10.tgz
tar -xf Python-3.12.10.tgz
cd Python-3.12.10
./configure --enable-optimizations
make -j 2
sudo make altinstall
```
