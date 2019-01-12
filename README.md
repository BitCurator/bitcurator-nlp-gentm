![Logo](https://github.com/BitCurator/bitcurator.github.io/blob/master/logos/BitCurator-Basic-400px.png)

# bitcurator-nlp-gentm

[![GitHub issues](https://img.shields.io/github/issues/bitcurator/bitcurator-nlp-gentm.svg)](https://github.com/bitcurator/bitcurator-nlp-gentm/issues)
[![GitHub forks](https://img.shields.io/github/forks/bitcurator/bitcurator-nlp-gentm.svg)](https://github.com/bitcurator/bitcurator-nlp-gentm/network)

Generate topic models using open text automatically extracted from various file formats in disk images. This project uses The Sleuth Kit (https://github.com/sleuthkit/sleuthkit) to parse file systems in disk images, textract (https://textract.readthedocs.io/en/stable/) to extract text from common file formats, gensim to generate topic models (https://radimrehurek.com/gensim/), and pyLDAvis (https://github.com/bmabey/pyLDAvis) for visualization.

## Setup and Installation

The topic model generation tool depends on a number of external natural language processing and digital forensics libraries. For convenience, we have included a script that will install all the required dependencies in Ubuntu 18.04LTS. This script will install certain tools (TSK, libewf, and several others) by compiling and installing from source.

In a Ubuntu host or a clean virtual machine, first make sure you have git installed: 

* Open a terminal and install git using apt:
```shell
$ sudo apt-get install git
```

Next, follow these steps:

* Clone this repository:
```shell
$ git clone https://github.com/bitcurator/bitcurator-nlp-gentm
```

* Change directory into the repository:
```shell
$ cd bitcurator-nlp-gentm
```

* Run the setup shell script to install and configure the required software (various dependencies, TSK, textract, and gensim). Note that this may take some time (**typically 10-15 minutes**).
```shell
$ sudo ./setup.sh
```

## Disk Image Selection and Configuration

This repository includes a sample Expert Witness Format disk image (**govdocs45sampler.E01**) in the **disk-images** directory. If you do not make any changes to the configuration file, the topic modeler and visualization tool will be run on text extracted from files discovered in this image.

To run the tool against other disk images (EWF or raw), simply copy those images into the **disk-images** directory and edit the **[image_section]** of the configuration file (**config.txt**) to include the relevant files. For example, if you had two images named **testimage1.E01** and **testimage2.dd**, the section would be modified as follows:

```shell
# Disk images to process (the default location can be changed in the following section)
[image_section]
my-image-name1.E01 = 1
my-image-name2.dd = 1
```

## Running the Tool

* Run the following command to extract text from the configured file types, start the topic modeling tool, and load the results into a browser window.
```shell
$ python bcnlp_tm.py
```

* The results based on the text extracted from your specified file types and processed using pyLDAvis will appear automatically in a browser window. When finished viewing, you can terminate the server in the existing terminal by typing "Ctrl-X" followed by "Ctrl-C".

* Additional usage notes

Additional adjustments can be performed with command-line flags.
* --topics: number of topics (default 10)
* --tm: topic modeling tool (default gensim). (Graphlab option disabled due to licensing restrictions)
* --infile: file source: if the --infile option is not used, the disc image(s) listed in the configuration 
file will be extracted. Use --infile to specify a directory instead.
* --config: configuration file (default **config.txt** in main directory) - specify file path for alternate configuration file

```shell
$ Usage: python bcnlp_tm.py [--topics <10>] [--tm <gensim|graphlab>] [--infile </directory/path>] [--config </path/to/config-file/>] 
```

## Additional Notes

If your Ubuntu VM does not already have a desktop (graphic UI), you will need to install one in order to view the results in a browser:

```shell
$ sudo apt-get update
$ sudo apt-get install ubuntu-desktop
```

## Documentation

Additional project information can be found on the BitCurator NLP wiki at https://github.com/BitCurator/bitcurator-nlp/wiki.

## License(s)

The BitCurator logo, BitCurator project documentation, and other non-software products of the BitCurator team are subject to the the Creative Commons Attribution 4.0 Generic license (CC By 4.0).

Unless otherwise indicated, software items in this repository are distributed under the terms of the GNU Lesser General Public License, Version 3. See the text file "COPYING" for further details about the terms of this license.

In addition to software produced by the BitCurator team, BitCurator packages and modifies open source software produced by other developers. Licenses and attributions are retained here where applicable.

