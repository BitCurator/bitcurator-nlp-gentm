# bitcurator-nlp-gentm

Generate topic models using open text automatically extracted from various file formats in disk iamges. This project is in development.

## Building and running

The topic model generation tool depends on a number of external natural language processing and digital forensics libraries. For convenience, we have included a script that will install all the required dependencies in Ubuntu (currently tested in Ubuntu 16.04 and Ubuntu 17.04). Note that this script will install certain tools (TSK, libewf, and several others) by compiling and installing from source.

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

* (Optional) Update the configuration file.
A prebuilt configuration file, "bntm_config.txt" includes a single sample image and limits text extraction to some common file types. You can process additional images by copying them into the disk images directory and adding their names to the section entitled "image-section" prior to running the tool.

* Run the setup shell script to install and configure the required software (various forensics tools, textract, graphlab, etc).
```shell
$ sudo ./setup.sh
```

* Run the following command to extract text from the configured file types, start the graphlab topic modeling tool, and load the results into a browser window.
```shell
$ python bcnlp_tm.py
```

* Additional usage notes
Additional adjustments can be performed with command-line flags, specifically to adjust the number of default topics and topic modeling output. Defaults are "10" and "graphlab".
```shell
$ Usage: python bcnlp_tm.py [--topics <10>] [--tm <gensim|graphlab>]
```

## Documentation

Additional project information can be found on the BitCurator Access wiki page at https://wiki.bitcurator.net/index.php?title=BitCurator_NLP.

## License(s)

The BitCurator logo, BitCurator project documentation, and other non-software products of the BitCurator team are subject to the the Creative Commons Attribution 4.0 Generic license (CC By 4.0).

Unless otherwise indicated, software items in this repository are distributed under the terms of the GNU Lesser General Public License, Version 3. See the text file "COPYING" for further details about the terms of this license.

In addition to software produced by the BitCurator team, BitCurator packages and modifies open source software produced by other developers. Licenses and attributions are retained here where applicable.

