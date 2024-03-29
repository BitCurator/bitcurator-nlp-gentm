#!/usr/bin/env bash
#
# bootstrap.sh: Build and configuration script for nlp-webtools in Vagrant
# --------------------------------------------------------------------------------------
# This script is only the *first time* you issue the command:
#
#    vagrant up
#
# Or, following the commands:
#
#    (vagrant halt)
#    vagrant destroy
#    vagrant up
#
#===============================================================================
# vim: softtabstop=4 shiftwidth=4 expandtab fenc=utf-8 spell spelllang=en cc=81
#===============================================================================
#
# Script Version
__ScriptVersion="0.1"
# Base directory for build log
LOG_BASE=/var/log
WWW_ROOT=/var/www

#--- FUNCTION ----------------------------------------------------------------
# NAME: __function_defined
# DESCRIPTION: Checks if a function is defined within this scripts scope
# PARAMETERS: function name
# RETURNS: 0 or 1 as in defined or not defined
#-------------------------------------------------------------------------------
__function_defined() {
    FUNC_NAME=$1
    if [ "$(command -v $FUNC_NAME)x" != "x" ]; then
        echoinfo "Found function $FUNC_NAME"
        return 0
    fi

    echodebug "$FUNC_NAME not found...."
    return 1
}

#--- FUNCTION ----------------------------------------------------------------
# NAME: __strip_duplicates
# DESCRIPTION: Strip duplicate strings
#-------------------------------------------------------------------------------
__strip_duplicates() {
    echo "$@" | tr -s '[:space:]' '\n' | awk '!x[$0]++'
}

#--- FUNCTION ----------------------------------------------------------------
# NAME: echoerr
# DESCRIPTION: Echo errors to stderr.
#-------------------------------------------------------------------------------
echoerror() {
    printf "%s * ERROR%s: %s\n" "${RC}" "${EC}" "$@" 1>&2;
}

#--- FUNCTION ----------------------------------------------------------------
# NAME: echoinfo
# DESCRIPTION: Echo information to stdout.
#-------------------------------------------------------------------------------
echoinfo() {
    printf "%s * STATUS%s: %s\n" "${GC}" "${EC}" "$@";
}

#--- FUNCTION ----------------------------------------------------------------
# NAME: echowarn
# DESCRIPTION: Echo warning informations to stdout.
#-------------------------------------------------------------------------------
echowarn() {
    printf "%s * WARN%s: %s\n" "${YC}" "${EC}" "$@";
}

#--- FUNCTION ----------------------------------------------------------------
# NAME: echodebug
# DESCRIPTION: Echo debug information to stdout.
#-------------------------------------------------------------------------------
echodebug() {
    if [ $_ECHO_DEBUG -eq $BS_TRUE ]; then
        printf "${BC} * DEBUG${EC}: %s\n" "$@";
    fi
}
#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  __apt_get_install_noinput
#   DESCRIPTION:  (DRY) apt-get install with noinput options
#-------------------------------------------------------------------------------
__apt_get_install_noinput() {
    apt-get install -y -o DPkg::Options::=--force-confold "$@"; return $?
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  __apt_get_upgrade_noinput
#   DESCRIPTION:  (DRY) apt-get upgrade with noinput options
#-------------------------------------------------------------------------------
__apt_get_upgrade_noinput() {
    apt-get upgrade -y -o DPkg::Options::=--force-confold; return $?
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  __pip_install_noinput
#   DESCRIPTION:  (DRY)
#-------------------------------------------------------------------------------
__pip_install_noinput() {
    #pip install --upgrade "$@"; return $?
    # Uncomment for Python 3
    pip3 install --upgrade $@; return $?
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  __pip_install_noinput
#   DESCRIPTION:  (DRY)
#-------------------------------------------------------------------------------
__pip_pre_install_noinput() {
    #pip install --pre --upgrade "$@"; return $?
    # Uncomment for Python 3
    pip3 install --pre --upgrade $@; return $?
}


#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  __check_apt_lock
#   DESCRIPTION:  (DRY)
#-------------------------------------------------------------------------------
__check_apt_lock() {
    lsof /var/lib/dpkg/lock > /dev/null 2>&1
    RES=`echo $?`
    return $RES
}

__enable_universe_repository() {
    if [ "x$(grep -R universe /etc/apt/sources.list /etc/apt/sources.list.d/ | grep -v '#')" != "x" ]; then
        # The universe repository is already enabled
        return 0
    fi
    echodebug "Enabling the universe repository"

    # Ubuntu versions higher than 12.04 do not live in the old repositories
    if [ $DISTRO_MAJOR_VERSION -gt 12 ] || ([ $DISTRO_MAJOR_VERSION -eq 12 ] && [ $DISTRO_MINOR_VERSION -gt 04 ]); then
        add-apt-repository -y "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) universe" || return 1
    elif [ $DISTRO_MAJOR_VERSION -lt 11 ] && [ $DISTRO_MINOR_VERSION -lt 10 ]; then
        # Below Ubuntu 11.10, the -y flag to add-apt-repository is not supported
        add-apt-repository "deb http://old-releases.ubuntu.com/ubuntu $(lsb_release -sc) universe" || return 1
    fi

    add-apt-repository -y "deb http://old-releases.ubuntu.com/ubuntu $(lsb_release -sc) universe" || return 1

    return 0
}

__check_unparsed_options() {
    shellopts="$1"
    # grep alternative for SunOS
    if [ -f /usr/xpg4/bin/grep ]; then
        grep='/usr/xpg4/bin/grep'
    else
        grep='grep'
    fi
    unparsed_options=$( echo "$shellopts" | ${grep} -E '(^|[[:space:]])[-]+[[:alnum:]]' )
    if [ "x$unparsed_options" != "x" ]; then
        usage
        echo
        echoerror "options are only allowed before install arguments"
        echo
        exit 1
    fi
}

configure_cpan() {
    (echo y;echo o conf prerequisites_policy follow;echo o conf commit)|cpan > /dev/null
}

usage() {
    echo "usage"
    exit 1
}

install_ubuntu_17.04_deps() {

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

install_ubuntu_17.04_packages() {
    packages="antiword 
automake
dkms
ffmpeg 
flac 
g++-5 
gcc-5 
lame 
libffi-dev
libjpeg-dev 
libmad0 
libpulse-dev 
libsox-fmt-mp3 
libtool
libxml2-dev 
libxslt1-dev 
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

install_ubuntu_17.04_pip_packages() {

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
    env CC=/usr/bin/gcc-5 pip3 install -U cld2-cffi

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

  #echoinfo "nlp-webtools: Nothing to be installed currently. Continuing..."
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
        cp /vagrant/externals/libewf-20140608.tar.gz .
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

OS=$(lsb_release -si)
ARCH=$(uname -m | sed 's/x86_//;s/i[3-6]86/32/')
VER=$(lsb_release -sr)

if [ $OS != "Ubuntu" ]; then
    echo "nlp-webtools is only installable on Ubuntu operating systems at this time."
    exit 1
fi

if [ $VER != "17.04" ]; then
    echo "nlp-webtools is only installable on Ubuntu 17.04 at this time."
    exit 3
fi

if [ "`whoami`" != "root" ]; then
    echoerror "The nlp-webtools bootstrap script must run as root."
    echoinfo "Preferred Usage: sudo bootstrap.sh (options)"
    echo ""
    exit 3
fi

if [ "$SUDO_USER" = "" ]; then
    echo "The SUDO_USER variable doesn't seem to be set"
    exit 4
fi

# while getopts ":hvcsiyu" opt
while getopts ":hv" opt
do
case "${opt}" in
    h ) usage; exit 0 ;;
    v ) echo "$0 -- Version $__ScriptVersion"; exit 0 ;;
    \?) echo
        echoerror "Option does not exist: $OPTARG"
        usage
        exit 1
        ;;
esac
done

shift $(($OPTIND-1))

if [ "$#" -eq 0 ]; then
    ITYPE="stable"
else
    __check_unparsed_options "$*"
    ITYPE=$1
    shift
fi

# Check installation type
if [ "$(echo $ITYPE | egrep '(dev|stable)')x" = "x" ]; then
    echoerror "Installation type \"$ITYPE\" is not known..."
    exit 1
fi

echoinfo "****************************************************************"
echoinfo "The nlp-webtools provisioning script will now configure your system."
echoinfo "****************************************************************"
echoinfo ""

#if [ "$YESTOALL" -eq 1 ]; then
#    echoinfo "You supplied the -y option, this script will not exit for any reason"
#fi

echoinfo "OS: $OS"
echoinfo "Arch: $ARCH"
echoinfo "Version: $VER"
echoinfo "The current user is: $SUDO_USER"

export DEBIAN_FRONTEND=noninteractive
install_ubuntu_${VER}_deps $ITYPE
install_ubuntu_${VER}_packages $ITYPE
install_ubuntu_${VER}_pip_packages $ITYPE
install_source_packages

complete_message
