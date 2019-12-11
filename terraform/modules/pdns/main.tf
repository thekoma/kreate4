# Configure the PowerDNS provider
variable "vcenter" {} 
variable "network" {} 
variable "pdns" {} 
variable "vm_list" {} 
variable "host_counter" {}

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
  name    = "XXXXXXX"
  kind    = "Native"
  nameservers = [ var.pdns.name ]
}


resource "powerdns_record" "record_A" {
  zone    = "${var.network.cluster}.${var.network.basedomain}."
  name    = "${var.vm_list[count.index].hostname}.${var.network.cluster}.${var.network.basedomain}."
  type    = "A"
  ttl     = 300
  records = ["${var.vm_list[count.index].ip}.${var.network.cluster}.${var.network.basedomain}"]
  count = var.host_counter
}


resource "powerdns_record" "record_PTR" {
  zone    = "XXXXXXX"
  name    = "${var.vm_list[count.index].reverse}.${var.network.cluster}.${var.network.basedomain}."
  type    = "PTR"
  ttl     = 300
  records = ["${var.vm_list[count.index].hostname}.${var.network.cluster}.${var.network.basedomain}."]
}