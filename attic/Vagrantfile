#-*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

    # Note: Built is tested with Ubuntu 17.04, but should also work with Ubuntu 16.04
    config.vm.box = "bento/ubuntu-17.04"

    # Run the provisioning script
    config.vm.provision :shell, :path => "./provision/bootstrap.sh"

    # Configure synced folder - uncomment the following line to enable
    # config.vm.synced_folder "", "/vagrant"

    # Port forward HTTP (80) to host 2020
    # Port forward 8080 (required for gensim)
    config.vm.network :forwarded_port, :host => 8080, :guest => 80
    config.vm.network :forwarded_port, :host => 8888, :guest => 8888

    # Use VirtualBox as the provider. Default specs are 4GB RAM, 2 procs
    # Increase vb.memory and vb.cpus for better performance
    config.vm.provider :virtualbox do |vb|
      vb.name = "nlp-webtools-0.0.1"
      vb.memory = 4096
      vb.cpus = 2
    end
end
