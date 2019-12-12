# As today we manipulate only vSphere. Maybe tomorrow the world.
module "vsphere" {
  source = "./modules/vsphere"
  vcenter=var.vcenter
  host_counter=var.host_count
  network=var.network
  vapps_options=var.vapps_options
  vm_list=var.vm_list
}

module "pdns" {
  source = "./modules/pdns"
  vcenter=var.vcenter
  host_counter=var.host_count
  network=var.network
  vm_list=var.vm_list
  pdns=var.pdns
  etcd=var.etcd
}
