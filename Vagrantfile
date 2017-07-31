#-*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

    #config.vm.box = "bento/ubuntu-16.04"
    #Vagrant.configure("2") do |config|
    config.vm.box = "bento/ubuntu-17.04"
    #config.vm.box_version = "2.3.7"
    #end

    # Run the provisioning script
    config.vm.provision :shell, :path => "./provision/bootstrap.sh"

    # Configure synced folder
    # config.vm.synced_folder "", "/vagrant"

    # Port forward HTTP (80) to host 2020
    config.vm.network :forwarded_port, :host => 8080, :guest => 80

    config.vm.provider :virtualbox do |vb|
      vb.name = "nlp-webtools-0.0.0"
      vb.memory = 4096
      vb.cpus = 2
    end
end
