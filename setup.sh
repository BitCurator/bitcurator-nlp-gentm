#!/usr/bin/env bash

#
# setup.sh: Build and configuration script for nlp-webtools
#
# This script sets up a correctly configured environment to the topic modeling tool.
# It should only be run once prior to running "python bcnlp_tm.py" for the first
# time.
#

LOG_BASE=/tmp

#--- FUNCTION -----------------------------------------------------------------
# NAME: echoinfo
# DESCRIPTION: Echo information to stdout.
#------------------------------------------------------------------------------
echoinfo() {
    printf "%s * STATUS%s: %s\n" "${GC}" "${EC}" "$@";
}

#--- FUNCTION -----------------------------------------------------------------
# NAME: echoerr
# DESCRIPTION: Echo errors to stderr.
#------------------------------------------------------------------------------
echoerror() {
    printf "%s * ERROR%s: %s\n" "${RC}" "${EC}" "$@" 1>&2;
}

#--- FUNCTION -----------------------------------------------------------------
#          NAME:  __apt_get_install_noinput
#   DESCRIPTION:  (DRY) apt-get install with noinput options
#------------------------------------------------------------------------------
__apt_get_install_noinput() {
    #apt-get install -y -o DPkg::Options::=--force-confold "$@"; return $?
    yes | aptdcon --hide-terminal --install "$@"; return $?
}

#--- FUNCTION -----------------------------------------------------------------
#          NAME:  __pip_install_noinput
#   DESCRIPTION:  (DRY)
#------------------------------------------------------------------------------

__pip_install_noinput() {
    # Uncomment for Python 3
    #pip3 install --upgrade $@; return $?
    pip2 install --upgrade $@; return $?
}

#--- FUNCTION -----------------------------------------------------------------
#          NAME:  __pip_install_noinput
#   DESCRIPTION:  (DRY)
#------------------------------------------------------------------------------
__pip_pre_install_noinput() {
    # Uncomment for Python 3
    #pip3 install --pre --upgrade $@; return $?
    pip2 install --pre --upgrade $@; return $?
}

install_ubuntu_deps() {

    echoinfo "Updating your APT Repositories ... "
    apt-get update >> $LOG_BASE/nlp-install.log 2>&1 || return 1

    echoinfo "Installing Python Software Properies ... "
    __apt_get_install_noinput software-properties-common >> $LOG_BASE/nlp-install.log 2>&1  || return 1

    echoinfo "Enabling Universal Repository ... "
    __enable_universe_repository >> $LOG_BASE/nlp-install.log 2>&1 || return 1

    echoinfo "Updating Repository Package List ..."
    apt-get update >> $LOG_BASE/nlp-install.log 2>&1 || return 1

    echoinfo "Upgrading all packages to latest version ..."
    __apt_get_upgrade_noinput >> $LOG_BASE/nlp-install.log 2>&1 || return 1

    return 0
}

install_ubuntu_packages() {
    packages="antiword
automake
curl
dkms
ffmpeg
flac
g++-5
gcc-5
lame
libffi-dev
libjpeg-dev
liblzma-dev
libmad0
libpulse-dev
libsox-fmt-mp3
libtool
libxml2-dev
libxslt1-dev
lzma
poppler-utils
pstotext
python
python-dev
python-pip
python3-dev
python3-pip
sox
swig
swig3.0
tesseract-ocr
unrtf
virtualbox-guest-utils
virtualenv
virtualenvwrapper
zlib1g-dev"

    if [ "$@" = "dev" ]; then
        packages="$packages"
    elif [ "$@" = "stable" ]; then
        packages="$packages"
    fi

    for PACKAGE in $packages; do
        __apt_get_install_noinput $PACKAGE >> $LOG_BASE/nlp-install.log 2>&1
        ERROR=$?
        if [ $ERROR -ne 0 ]; then
            echoerror "Install Failure: $PACKAGE (Error Code: $ERROR)"
        else
            echoinfo "Installed Package: $PACKAGE"
        fi
    done

    return 0
}

install_ubuntu_pip_packages() {

    pip_packages="textract
    gensim
    pyLDAvis
    configobj"
    pip_special_packages="textacy"

    if [ "$@" = "dev" ]; then
        pip_packages="$pip_packages"
    elif [ "$@" = "stable" ]; then
        pip_packages="$pip_packages"
    fi

    ERROR=0

    for PACKAGE in $pip_packages; do
        CURRENT_ERROR=0
        echoinfo "Installed Python Package: $PACKAGE"
        __pip_install_noinput $PACKAGE >> $LOG_BASE/nlp-install.log 2>&1 || (let ERROR=ERROR+1 && let CURRENT_ERROR=1)
        if [ $CURRENT_ERROR -eq 1 ]; then
            echoerror "Python Package Install Failure: $PACKAGE"
        fi
    done

    # Prep environment for special packages, install cld2-cffi
    #env CC=/usr/bin/gcc-5 pip3 install -U cld2-cffi
    env CC=/usr/bin/gcc-5 pip install -U cld2-cffi

    for PACKAGE in $pip_special_packages; do
        CURRENT_ERROR=0
        echoinfo "Installed Python (special setup) Package: $PACKAGE"
        __pip_pre_install_noinput $PACKAGE >> $LOG_BASE/nlp-install.log 2>&1 || (let ERROR=ERROR+1 && let CURRENT_ERROR=1)
        if [ $CURRENT_ERROR -eq 1 ]; then
            echoerror "Python Package Install Failure: $PACKAGE"
        fi
    done

    if [ $ERROR -ne 0 ]; then
        echoerror
        return 1
    fi

    return 0
}

install_source_packages() {

  # Install libuna from specific release
  echoinfo "nlp-webtools: Building and installing libuna"
        CDIR=$(pwd)
        # Newer versions break a lot of stuff. Keep 20150927 for now.
        cd /tmp
        wget -q https://github.com/libyal/libuna/releases/download/20170112/libuna-alpha-20170112.tar.gz
        tar zxf libuna-alpha-20170112.tar.gz >> $HOME/nlp-install.log 2>&1
        cd libuna-20170112
        ./configure >> $HOME/nlp-install.log 2>&1
        make -s >> $HOME/nlp-install.log 2>&1
        make install >> $HOME/nlp-install.log 2>&1
        ldconfig >> $HOME/nlp-install.log 2>&1

        # Now clean up
        cd /tmp
        rm -rf libuna-20170112
        rm libuna-alpha-20170112.tar.gz

  # Install libewf from current sources
  echoinfo "nlp-webtools: Building and installing libewf"
        CDIR=$(pwd)

        # Newer versions break a lot of stuff. Keep 20140608 for now.
        cd /tmp
        cp /$HOME/bitcurator-nlp-gentm/externals/libewf-20140608.tar.gz .
        tar zxf libewf-20140608.tar.gz >> $HOME/nlp-install.log 2>&1
        cd libewf-20140608
        ./configure --enable-python --enable-v1-api >> $HOME/nlp-install.log 2>&1
        make -s >> $HOME/nlp-install.log 2>&1
        make install >> $HOME/nlp-install.log 2>&1
        ldconfig >> $HOME/nlp-install.log 2>&1

        # Now clean up
        cd /tmp
        rm -rf libewf-20140608
        rm libewf-20140608.tar.gz

  echoinfo "nlp-webtools: Adding DFXML tools and libraries"
        CDIR=$(pwd)
        git clone https://github.com/simsong/dfxml /usr/share/dfxml >> $HOME/nlp-install.log 2>&1
        # No cleanup needed
        cd /tmp

  # Install The Sleuth Kit (TSK) from current sources
  echoinfo "nlp-webtools: Building and installing The Sleuth Kit"
        CDIR=$(pwd)
        git clone --recursive https://github.com/sleuthkit/sleuthkit /usr/share/sleuthkit >> $HOME/nlp-install.log 2>&1
        cd /usr/share/sleuthkit
        git fetch
        git checkout master >> $HOME/nlp-install.log 2>&1
        ./bootstrap >> $HOME/nlp-install.log 2>&1
        ./configure >> $HOME/nlp-install.log 2>&1
        make -s >> $HOME/nlp-install.log 2>&1
        make install >> $HOME/nlp-install.log 2>&1
        ldconfig >> $HOME/nlp-install.log 2>&1

  # Install PyTSK
  echoinfo "nlp-webtools: Building and installing PyTSK (Python bindings for TSK)"
  echoinfo " -- Please be patient. This may take several minutes..."
        CDIR=$(pwd)
        cd /tmp
        git clone https://github.com/py4n6/pytsk
        cd pytsk
        python setup.py update >> $HOME/nlp-install.log 2>&1
        python setup.py build >> $HOME/nlp-install.log 2>&1
        python setup.py install >> $HOME/nlp-install.log 2>&1
        # Now clean up
        cd /tmp
        #rm -rf pytsk3-20170508
        rm -rf pytsk

}

complete_message() {
    echo
    echo "Installation Complete!"
    echo
}

echo "Installing core dependencies...."
install_ubuntu_deps

echo "Installing Ubuntu packages...."
install_ubuntu_packages stable

echo "Installing pip packages...."
install_ubuntu_pip_packages stable

echo "Installing source packages...."
install_source_packages

# echo "current directory1: ${PWD} "
echo "Installing textract support packages..."
sudo apt-get install libxml2-dev libxslt1-dev antiword unrtf poppler-utils pstotext tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 libpulse-dev sox swig swig3.0 libjpeg-dev zlib1g-dev


# echo "current directory2: ${PWD} "
echo "Installing textract..."
sudo pip install textract

echo "Installing graphlab..."
sudo pip install --upgrade --no-cache-dir https://get.graphlab.com/GraphLab-Create/2.1/sunita@live.unc.edu/0295-EBD3-1F14-E97A-7FA1-5421-EA06-209A/GraphLab-Create-License.tar.gz

echo "Installing configObj..."
pip install configobj

echo "Installing gensim..."
pip install gensim

echo "Installing pyLDAvis..."
pip install pyLDAvis

# The following are needed for bn_plot
pip install matplotlib
pip install spacy
python -m spacy download en

echo "Installing dfvfs..."
curl -O https://raw.githubusercontent.com/log2timeline/dfvfs/master/requirements.txt
pip install -r requirements.txt
pip install dfvfs

complete_message
