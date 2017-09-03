# bitcurator-nlp-gentm

Generate topic models using open text automatically extracted from various file formats in disk iamges. This project is in development.

## Building and running

The topic model generation tool depends on a number of external natural language processing and digital forensics libraries. For convenience, we have included a script that will install all the required dependencies in Ubuntu (currently tested in Ubuntu 16.04 and Ubuntu 17.04).

To get started, follow the steps below in a clean Ubuntu host or VM:

1. Clone the repository https://github.com/BitCurator/bitcurator-nlp-gentm

2. Populate the config file, "bntm_config.txt" with the relevant images,
in the section "image-section"

3. Run the script provision/nlp_script to install packages like
textract, graphlab, etc.

4. Run the script "python bcnlp_tm.py" to perform text extraction, execute the graphlab topic modeling tool, and load the results into a browser window.

Usage: python bcnlp_tm.py [--topics <10>] [--tm <gensim|graphlab>]
Default topics = 10, tm=graphlab

## Documentation

Additional project information can be found on the BitCurator Access wiki page at https://wiki.bitcurator.net/index.php?title=BitCurator_NLP.

## License(s)

The BitCurator logo, BitCurator project documentation, and other non-software products of the BitCurator team are subject to the the Creative Commons Attribution 4.0 Generic license (CC By 4.0).

Unless otherwise indicated, software items in this repository are distributed under the terms of the GNU Lesser General Public License, Version 3. See the text file "COPYING" for further details about the terms of this license.

In addition to software produced by the BitCurator team, BitCurator packages and modifies open source software produced by other developers. Licenses and attributions are retained here where applicable.

