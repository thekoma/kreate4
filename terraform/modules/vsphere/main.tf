provider "vsphere" {
  user           = var.vcenter["user"]
  password       = var.vcenter["password"]
  vsphere_server = var.vcenter["host"]
  # If you have a self-signed cert
  allow_unverified_ssl = true
}

data "vsphere_datacenter" "dc" {
  name = var.vcenter["datacenter"]
}

data "vsphere_datastore" "datastore" {
  name          = var.vcenter["datastore"]
  datacenter_id = data.vsphere_datacenter.dc.id
}

# data "vsphere_datastore_cluster" "datastore_cluster" {
#   name          = var.vcenter["datastore"]
#   datacenter_id = data.vsphere_datacenter.dc.id
# }

data "vsphere_virtual_machine" "template" {
  name          = var.vcenter["template"]
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_network" "network" {
  name          = var.vcenter["portgroup"]
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_compute_cluster" "compute_cluster" {
  name          = var.vcenter["cluster"]
  datacenter_id = data.vsphere_datacenter.dc.id
}

resource "vsphere_folder" "folder" {
  path          = var.vcenter["vm_folder"]
  type          = "vm"
  datacenter_id = data.vsphere_datacenter.dc.id
}

resource "vsphere_folder" "folder" {
  path          = var.vcenter["cluster"]
  type          = "datastore"
  datacenter_id = data.vsphere_datacenter.dc.id
}

resource "vsphere_virtual_machine" "vm" {
  depends_on                = [vsphere_folder.folder]
  name                       = "${var.vm_list[count.index].hostname}.${var.network.cluster}.${var.network.basedomain}"
  resource_pool_id           = data.vsphere_compute_cluster.compute_cluster.resource_pool_id
  datastore_id               = data.vsphere_datastore.datastore.id
  #datastore_id               = data.vsphere_datastore_cluster.datastore_cluster.id
  folder                     = var.vcenter["vm_folder"]
  num_cpus                   = var.vm_list[count.index].cpu
  memory                     = var.vm_list[count.index].ram
  guest_id                   = data.vsphere_virtual_machine.template.guest_id
  wait_for_guest_net_timeout = 0
  wait_for_guest_ip_timeout  = 0
  enable_disk_uuid           = true
  //This is wrong but  you know.. lab 
  latency_sensitivity        = "normal" 
  scsi_type                  = data.vsphere_virtual_machine.template.scsi_type

  count = var.general["host_count"]

  network_interface {
    network_id     = data.vsphere_network.network.id
    adapter_type   = data.vsphere_virtual_machine.template.network_interface_types[0]
    use_static_mac = true
    mac_address    = var.vm_list[count.index].mac_address
  }

  disk {
    name             = "disk0.vmdk"
    size             = data.vsphere_virtual_machine.template.disks.0.size
    eagerly_scrub    = data.vsphere_virtual_machine.template.disks.0.eagerly_scrub
    thin_provisioned = data.vsphere_virtual_machine.template.disks.0.thin_provisioned
  }

  clone {
    template_uuid = data.vsphere_virtual_machine.template.id
  }

  vapp {
    properties = {
      "guestinfo.ignition.config.data.encoding" = "base64"
      "guestinfo.ignition.config.data" = "${var.vapps_options[var.vm_list[count.index].type]}"
    }
  }

}
