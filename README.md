# kreate4
This tool want's to help you create an environment for OCP4 without the assle of staticizing IPs and using dhcp and dns.

You need to create 2 files

- The first is pull.json which contains the pull information for openshift (one line)
- The second is the file configuration.yaml, which contains all the needed configuration to deliver the entire openshift 4 lab. (You have to review it but is pretty straightforward and commented)

You have do 
- You need a bastion (infrastructure) host where you'll run this script
- You need to run the script as root or as sudo (NO_PASSWD) user.
- You need 2 IP for the haproxy (one is your bastion ip the second is any in the same network).

