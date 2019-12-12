# Configure the PowerDNS provider
variable "vcenter" {} 
variable "network" {} 
variable "pdns" {} 
variable "vm_list" {} 
variable "host_counter" {}
variable "etcd" {}

provider "powerdns" {
  api_key    = var.pdns.key
  server_url = var.pdns.host
}

# Add a zone
resource "powerdns_zone" "LAB" {
  name    = "${var.network.cluster}.${var.network.basedomain}."
  kind    = "Native"
  nameservers = [ var.pdns.name ]
}

resource "powerdns_zone" "PTR" {
  name    = "${var.network.zone_reverse}."
  kind    = "Native"
  nameservers = [ var.pdns.name ]
}


resource "powerdns_record" "record_A" {
  depends_on  = [powerdns_zone.LAB]
  zone    = "${var.network.cluster}.${var.network.basedomain}."
  name    = "${var.vm_list[count.index].hostname}.${var.network.cluster}.${var.network.basedomain}."
  type    = "A"
  ttl     = 300
  records = ["${var.vm_list[count.index].ip}"]
  count = var.host_counter
}


resource "powerdns_record" "record_PTR" {
  depends_on  = [powerdns_zone.PTR]
  zone    = "${var.network.zone_reverse}."
  name    = "${var.vm_list[count.index].reverse}."
  type    = "PTR"
  ttl     = 300
  records = ["${var.vm_list[count.index].hostname}.${var.network.cluster}.${var.network.basedomain}."]
  count = var.host_counter
}

resource "powerdns_record" "record_etcd_A" {
  depends_on  = [powerdns_zone.LAB]
  zone    = "${var.network.cluster}.${var.network.basedomain}."
  name    = "etcd-${count.index}.${var.network.cluster}.${var.network.basedomain}."
  type    = "A"
  ttl     = 300
  records = ["${var.etcd[count.index].ip}"]
  count = 3
}

resource "powerdns_record" "record_etcd_SRV" {
  depends_on  = [powerdns_zone.LAB]
  zone    = "${var.network.cluster}.${var.network.basedomain}."
  name    = "_etcd-server-ssl._tcp.${var.network.cluster}.${var.network.basedomain}."
  type    = "SRV"
  ttl     = 300
  records = ["0 10 2380 etcd-0.${var.network.cluster}.${var.network.basedomain}.", "0 10 2380 etcd-1.${var.network.cluster}.${var.network.basedomain}.", "0 10 2380 etcd-2.${var.network.cluster}.${var.network.basedomain}.", ]
}


resource "powerdns_record" "record_api_A" {
  depends_on  = [powerdns_zone.LAB]
  zone    = "${var.network.cluster}.${var.network.basedomain}."
  name    = "api.${var.network.cluster}.${var.network.basedomain}."
  type    = "A"
  ttl     = 300
  records = ["${var.network.api}"]
}
resource "powerdns_record" "record_api-int_A" {
  depends_on  = [powerdns_zone.LAB]
  zone    = "${var.network.cluster}.${var.network.basedomain}."
  name    = "api-int.${var.network.cluster}.${var.network.basedomain}."
  type    = "A"
  ttl     = 300
  records = ["${var.network.apiint}"]
}

resource "powerdns_record" "record_apps_A" {
  depends_on  = [powerdns_zone.LAB]
  zone    = "${var.network.cluster}.${var.network.basedomain}."
  name    = "*.apps.${var.network.cluster}.${var.network.basedomain}."
  type    = "A"
  ttl     = 300
  records = ["${var.network.lb}"]
}

resource "powerdns_record" "record_bastion_A" {
  depends_on  = [powerdns_zone.LAB]
  zone    = "${var.network.cluster}.${var.network.basedomain}."
  name    = "bastion.${var.network.cluster}.${var.network.basedomain}."
  type    = "A"
  ttl     = 300
  records = ["${var.network.lb}"]
}

# address=/.apps.{{nodes.network.cluster}}.{{nodes.network.basedomain}}/{{nodes.network.lb}}
# address=/api.{{nodes.network.cluster}}.{{nodes.network.basedomain}}/{{nodes.network.api}}
# address=/api-int.{{nodes.network.cluster}}.{{nodes.network.basedomain}}/{{nodes.network.apiint}}
# address=/bastion.{{nodes.network.cluster}}.{{nodes.network.basedomain}}/{{nodes.network.lb}}