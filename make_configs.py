#!/usr/bin/env python3
from jinja2 import Environment, FileSystemLoader
import yaml
import json
import os
from pathlib import Path
import shlex, subprocess
from subprocess import Popen, PIPE
from pprint import pprint
from os import chmod
import socket
import urllib.request
import tarfile
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
import requests
import shutil
from shutil import copyfile
import base64
import ipaddress
from netaddr import IPAddress

def create_if_not_exist(thedir):
    if not os.path.exists(thedir):
        print("Creating ", thedir)
        os.mkdir(thedir)
def clean_if_exist(thedir):
    if not os.path.exists(thedir):
        print("Creating ", thedir)
        os.mkdir(thedir)
    else:
        print("Cleaning ", thedir)
        shutil.rmtree(thedir)
        print("Creating ", thedir)
        os.mkdir(thedir)

global confs
global install_config
global pull_json

###########################################################################################################

ocp_target_version      = "4.2.9"
ocp_base_url            = "https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest"
vsphere_cfg             = "configuration.yaml"
pull_auth               = "pull.json"
bin_dir                 = "bin"
tmp_dir                 = "/tmp/ocp_dld"
template_dir            = "templates"
haproxy_tpl             = "haproxy.txt"
dhcpd_tpl               = "dhcpd.txt"
dnsmasq_tpl             = "dnsmasq.txt"
docker_compose_tpl      = "docker-compose.txt"
vphsere_terraform_vars  = 'terraform/modules/vsphere/terraform.tf.json'
ocp_client_dld          = 'client.tgz'
ocp_installer_dld       = 'install.tgz'
bootstrap_filename      = "bootstrap.ign"
configuration_dir       = "configurations"
ocp_web_path            = "%s/www"                               % (configuration_dir)
dhcpd_dir               = "%s/dhcpd"                             % (configuration_dir)
dockercompose           = "%s/docker-compose.yaml"               % (configuration_dir)
dnsmasq_cfg             = "%s/dnsmasq.conf"                      % (configuration_dir)
haproxy_cfg             = "%s/haproxy.cfg"                       % (configuration_dir)
ssh_priv                = "%s/private.key"                       % (configuration_dir)
ssh_pub                 = "%s/public.key"                        % (configuration_dir)
install_config_file     = "%s/install-config.yaml"               % (configuration_dir)
ocp_install             = "%s/openshift-install"                 % (bin_dir)
dhcpd_cfg               = "%s/dhcpd.conf"                        % (dhcpd_dir)
install_config_tpl      = "%s/install-config.txt"                % (template_dir)
append_bootstrap_tpl    = "%s/append-bootstrap.ign"              % (template_dir)
ocp_client_url          = "%s/openshift-client-linux-%s.tar.gz"  % (ocp_base_url, ocp_target_version)
ocp_installer_url       = "%s/openshift-install-linux-%s.tar.gz" % (ocp_base_url, ocp_target_version)
bootstrap_path          = "%s/bootstrap.ign"                     % (ocp_web_path)
basedirs                = [bin_dir, configuration_dir, dhcpd_dir] #Tmp dir treated differently.


for namedir in basedirs:
    create_if_not_exist(namedir)

with open(vsphere_cfg) as info:
    confs = yaml.load(info, Loader=yaml.FullLoader)

with open(install_config_tpl) as info:
    install_config = yaml.load(info, Loader=yaml.FullLoader)

with open(pull_auth, 'r') as myfile:
    pull_json=myfile.read().replace('\n', '')
networks_info           = confs['variable']['network']['default']
lb                      = networks_info.get('lb')
lb_int                  = networks_info.get('lb_int')
apiintip                = networks_info.get('apiint')
subnet                  = networks_info.get('subnet')
ocp_clustername         = networks_info.get('cluster')
ocp_work_path           = "cluster-%s"              % (ocp_clustername)
master_ignition         = "%s/master.ign"           % (ocp_work_path)
infra_ignition          = "%s/worker.ign"           % (ocp_work_path)
bootstrap_ignition      = "%s/%s"                   % (ocp_work_path, bootstrap_filename)

ocp_dir_param           = "--dir=%s"                % (ocp_work_path)
ocp_install_config_file = "%s/install-config.yaml"  % (ocp_work_path)
append_bootstrap_url    ="http://%s:8888/%s"        % (lb, bootstrap_filename)

###########################################################################################################
# Functions


create_if_not_exist(ocp_work_path)

def downloader_fun(url_src, file_dest):
    u = urllib.request.urlopen(url_src)
    h = u.info()
    totalSize = int(h["Content-Length"])
    
    print("Downloading %s for %s bytes...\n" %(url_src, totalSize))
    fp = open(file_dest, 'wb')

    blockSize = 8192 #100000 # urllib.urlretrieve uses 8192
    count = 0
    while True:
        chunk = u.read(blockSize)
        if not chunk: break
        fp.write(chunk)
        count += 1
        if totalSize > 0:
            percent = int(count * blockSize * 100 / totalSize)
            if percent > 100: percent = 100
            if percent < 100:
                print ("\033[A                             \033[A")
                print("%2d%%" %(percent))
            else:
                print ("\033[A                             \033[A") 
                print("Done donwnloading %s. Saved in %s" %(url_src, file_dest))

    fp.flush()
    fp.close()
    if not totalSize:
        print()

def extract_tools(fname, where):
    tar = tarfile.open(fname, "r:gz")
    tar.extractall(path=where)
    tar.close()

def download_tools():
    print('#### Download dei tools')
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)
    if not os.path.exists(bin_dir):
        os.mkdir('bin')

    dest_path="%s/%s" % (tmp_dir, ocp_client_dld)
    if not os.path.exists(dest_path):
        downloader_fun(ocp_client_url, dest_path)
    else:
        print("Skipping download of %s Already there." % (dest_path))
    
    
    extract_tools(dest_path, bin_dir)
    dest_path="%s/%s" % (tmp_dir, ocp_installer_dld)
    if not os.path.exists(dest_path):
        downloader_fun(ocp_installer_url, dest_path)
    else:
        print("Skipping download of %s Already there." % (dest_path))
    extract_tools(dest_path, bin_dir)

    print('#### Done')

def new_ssh_key():
    print("Creating new ssh pair...\t\t\t", end='')
    private_key_file = Path(ssh_priv)
    public_key_file = Path(ssh_pub)
    if private_key_file.is_file() or public_key_file.is_file():
        print('skipped (pair existing)')
    else:
        key = rsa.generate_private_key(
            backend=crypto_default_backend(),
            public_exponent=65537,
            key_size=2048
        )
        private_key = key.private_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PrivateFormat.PKCS8,
            crypto_serialization.NoEncryption())
        public_key = key.public_key().public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH
        )
        with open(ssh_pub, 'wb') as content_file:
            content_file.write(public_key)
        with open(ssh_priv, 'wb') as content_file:
            content_file.write(private_key)
        print("done")

def render_install_config():
    print("Creating install-config.yml...\t\t\t", end='')
    with open (ssh_pub, "r") as ssk_key_public:
        sshKey=ssk_key_public.read().replace('\n', '')

    install_config['baseDomain']                                = confs['variable']['network']['default'].get('basedomain')
    install_config['sshKey']                                    = sshKey
    install_config['platform']['vsphere']['datacenter']         = confs['variable']['vcenter']['default'].get('datacenter')
    install_config['platform']['vsphere']['defaultDatastore']   = confs['variable']['vcenter']['default'].get('datastore')
    install_config['platform']['vsphere']['username']           = confs['variable']['vcenter']['default'].get('user')
    install_config['platform']['vsphere']['password']           = confs['variable']['vcenter']['default'].get('password')
    install_config['platform']['vsphere']['vcenter']            = confs['variable']['vcenter']['default'].get('host')
    install_config['pullSecret']                                = pull_json
    install_config['metadata']['name']                          = confs['variable']['network']['default'].get('cluster')

    with open(install_config_file, 'w') as f:
        yaml.dump(install_config, f, default_flow_style=False)
    print("done")

def create_terraform_vars():
    print("Creating terraform vars for vsphere...\t\t", end='')
    with open(vphsere_terraform_vars, 'w') as fp:
        json.dump(confs, fp)
    print("done")

def render_haproxy_cfg(nodes):
    print("Rendering haproxy configuration template...\t", end='')
    file_loader = FileSystemLoader(template_dir)
    env = Environment(loader=file_loader)
    template = env.get_template(haproxy_tpl)
    output = template.render(nodes=nodes)
    with open(haproxy_cfg, 'w') as f:
        f.write(output)
    print("done")

def render_dhcpd_cfg(nodes):
    print("Rendering haproxy configuration template...\t", end='')
    file_loader = FileSystemLoader(template_dir)
    env = Environment(loader=file_loader)
    template = env.get_template(dhcpd_tpl)
    output = template.render(nodes=nodes)
    if not os.path.exists(dhcpd_dir):
        os.mkdir(dhcpd_dir)   
    with open(dhcpd_cfg, 'w') as f:
        f.write(output)
    print("done")

def render_dnsmasq_cfg(nodes):
    print("Rendering dnsmasq configuration template...\t", end='')
    
    loop=0
    kinds=['infra', 'master', 'bootstrap']
    for kind in kinds:
        loop=0
        for key in nodes[kind]:
            ip=key['ip']
            nodes[kind][loop]['reverse'] = ipaddress.ip_address(ip).reverse_pointer
            loop=loop+1

    nodes['network']['api_reverse']         = ipaddress.ip_address(nodes['network']['api']).reverse_pointer
    nodes['network']['apiint_reverse']      = ipaddress.ip_address(nodes['network']['apiint']).reverse_pointer
    file_loader = FileSystemLoader(template_dir)
    env = Environment(loader=file_loader)

    template = env.get_template(dnsmasq_tpl)
    output = template.render(nodes=nodes)
    with open(dnsmasq_cfg, 'w') as f:
        f.write(output)
    print("done")

def build_node_var():
    print("Building node list...\t\t\t", end='')
    
    net_info=confs['variable']['network']['default']
    machines=confs['variable']['vm_list'].get('default')
    infra_nodes=[]
    master_nodes=[]
    bootstrap_nodes=[]
    for elem in machines:
        if elem['type'] == 'infra':
            infra_nodes.append(elem)
        elif elem['type'] == 'master':
            master_nodes.append(elem)
        elif elem['type'] == 'bootstrap':
            bootstrap_nodes.append(elem)
    nodes=dict([('infra',infra_nodes),('master',master_nodes),('bootstrap',bootstrap_nodes),('network',net_info)])
    return nodes
    print("done")


def extract_machines():
    nodes=build_node_var()
    render_dhcpd_cfg(nodes)
    render_haproxy_cfg(nodes)
    render_dnsmasq_cfg(nodes)

def create_manifests():
    print("Creating manifest")
    print("Copy config")
    copyfile(install_config_file, ocp_install_config_file)
    subprocess.run([ocp_install, 'create', 'manifests', ocp_dir_param]) 

def modify_manifest():
    print("Modifying manifest...\t\t", end='')
    #Edit manifest
    manifest_to_edit = "%s/manifests/cluster-scheduler-02-config.yml" % (ocp_work_path)
    with open(manifest_to_edit) as info:
        manifest_var = yaml.load(info, Loader=yaml.FullLoader)

    manifest_var['spec']['mastersSchedulable']=False
    with open(manifest_to_edit, 'w') as f:
        yaml.dump(manifest_var, f, default_flow_style=False)
    print("done")

def create_ignition():
    subprocess.run([ocp_install, 'create', 'ignition-configs', ocp_dir_param]) 

def create_bootstrap_ignition():
    with open(append_bootstrap_tpl, 'r') as myfile:
        append_bootstrap=json.load(myfile)
    append_bootstrap['ignition']['config']['append'][0]['source']=append_bootstrap_url
    append_bootstrap=json.dumps(append_bootstrap)
    encodedBytes = base64.b64encode(str(append_bootstrap).encode("utf-8"))
    encodedStr = str(encodedBytes, "utf-8")
    confs['variable']['vapps_options']['default']['bootstrap']=encodedStr

def create_master_ignition():
    with open(master_ignition, 'r') as myfile:
        master_ignition_js=json.load(myfile)
    master_ignition_dump=json.dumps(master_ignition_js)
    encodedBytes = base64.b64encode(str(master_ignition_dump).encode("utf-8"))
    encodedStr = str(encodedBytes, "utf-8")
    confs['variable']['vapps_options']['default']['master']=encodedStr

def create_infra_ignition():
    with open(infra_ignition, 'r') as myfile:
        infra_ignition_js=json.load(myfile)
    infra_ignition_dump=json.dumps(infra_ignition_js)
    encodedBytes = base64.b64encode(str(infra_ignition_dump).encode("utf-8"))
    encodedStr = str(encodedBytes, "utf-8")
    confs['variable']['vapps_options']['default']['infra']=encodedStr

def prepare_web_path():
    if not os.path.exists(ocp_web_path):
        os.mkdir(ocp_web_path)   
    copyfile(bootstrap_ignition, bootstrap_path)

def build_compose_tpl():
    # For now is useless.. but maybe some day....
    nodes=build_node_var()
    file_loader = FileSystemLoader(template_dir)
    env = Environment(loader=file_loader)
    template = env.get_template(docker_compose_tpl)
    output = template.render(nodes=nodes)
    with open(dockercompose, 'w') as f:
        f.write(output)

def run_compose():
    build_compose_tpl()
    print("done")
    subprocess.run(['docker-compose', '-f', dockercompose, 'down', '--remove-orphans', '-t', '5']) 
    subprocess.run(['docker-compose', '-f', dockercompose, 'up', '-d']) 

def set_ip():
    cidr = IPAddress(subnet).netmask_bits()
    apiintipcidr = "%s/%s" % (apiintip, cidr)
    subprocess.run(['sudo', 'nmcli', 'connection', 'modify', lb_int, '+ipv4.addresses', apiintipcidr ])
    subprocess.run(['sudo', 'nmcli', 'connection', 'up', lb_int])

def set_dns():
    subprocess.run(['sudo', 'nmcli', 'connection', 'modify', lb_int, 'ipv4.dns', lb ])
    subprocess.run(['sudo', 'nmcli', 'connection', 'up', lb_int])

def create_machines():
    subprocess.run(['terraform', 'init', 'terraform/'])
    subprocess.run(['terraform', 'plan', 'terraform/'])
    subprocess.run(['terraform', 'apply', '-auto-approve', 'terraform/'])

def start_bootstrapper():
    subprocess.run([ocp_install, ocp_dir_param, 'wait-for', 'bootstrap-complete', '--log-level=info']) 


def main():
    download_tools()
    new_ssh_key()
    render_install_config()
    extract_machines()
    create_manifests()
    modify_manifest()
    create_ignition()
    create_bootstrap_ignition()
    create_master_ignition()
    create_infra_ignition()
    create_terraform_vars()
    prepare_web_path()
    set_ip()
    run_compose()
    set_dns()
    create_machines()
    start_bootstrapper()
main()