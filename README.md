# kreate4
This tool want's to help you create an environment for OCP4 without the assle of staticizing IPs and using dhcp and dns.

You need to create 2 files
- The first is pull.json which contains the pull information for openshift (one line)
- The second is the file configuration.yaml, which contains all the needed configuration to deliver the entire openshift 4 lab. (You have to review it but is pretty straightforward and commented)

Requirements:
- python3
- docker
- terraform
- You need a bastion (infrastructure) host where you'll run this script and that will be the dhcp and dns server for the network
- You need to run the script as root or as sudo (NO_PASSWD) user.
- You need 2 IP for the haproxy (one is your bastion ip the second is any in the same network).

## Execution:

Install docker (this is for centos 8 or fedora)
```bash
dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo
dnf install -y docker-ce --nobest
systemctl enable --now docker
```

Disable the firewall (it's a lab)
```bash
systemctl disable --now firewalld
```

Install terraform
```
wget https://releases.hashicorp.com/terraform/0.12.17/terraform_0.12.17_linux_amd64.zip
unzip ./terraform_0.12.17_linux_amd64.zip –d /usr/local/bin
chmod +x /usr/local/bin/terraform
```

Install the required libraries
```bash
python3 -m venv .myenv
source .myenv/bin/activate
pip install -r requirements.txt
```

Copy your `pull.json` from try.openshift.com
```
vi pull.json
```

Edit `configuration.yaml`
```bash
cp configuration.yaml.dist configuration.yaml
vi configuration.yaml
```

Run the script
```bash
./kreate4.py
```

# It's a prototype. Be kind.
