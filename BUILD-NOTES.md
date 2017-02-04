# Ubuntu 16.04LTS + Python 3.5 preliminary build instructions:

These preliminary instructions may be incomplete. Do not assume they work.

## Install some basic requirements:

```shell
sudo apt-get install virtualenv virtualenvwrapper python3-pip python3-dev
```

## Install postgres and some associated requirements:

```shell
sudo apt-get install postgresql pgadmin3 postgresql-server-dev-9.5
```

## Install some dependencies for textract:

```shell
sudo apt-get install libxml2-dev libxslt1-dev antiword unrtf poppler-utils pstotext tesseract-ocr flac ffmpeg lame libffi-dev libmad0 libsox-fmt-mp3 sox libjpeg-dev zlib1g-dev
```

## Set up virtualenv and virtualenvwrapper:

You can skip or modify this step (and the remaining virtualenv steps) if your local setup differs or you don't wish to use virtualenvs.

```shell
mkdir ~/.virtualenvs
```

Add the following to the end of your __.bashrc__ file. You may need to verify the location of virtualenvwrapper on your system:

```shell
# Virtualenv and virtualenvwrapper
export WORKON_HOME="$HOME/.virtualenvs"
source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
```

Type ```source ~/.bashrc``` or close and reopen the terminal.

## Make a virtualenv for nei-core

```shell
mkvirtualenv -p /usr/bin/python3 nei-core
```

## Install textract:

```shell
pip3 install textract
```

## Install textacy dependencies: 

There are some legacy issues with cld2-cffi (see https://github.com/chartbeat-labs/textacy/issues/5 - using gcc-5 for the time being to route around them). Revisit in future. (Do __not__ use sudo when installing via pip3 in a virtualenv; if you do, the cld2-cffi dep will remain broken as it won't be found in the venv, and textacy will try to build it again with gcc-6).

```shell
sudo apt-get install gcc-5 g++-5 libffi-dev
env CC=/usr/bin/gcc-5 pip3 install -U cld2-cffi
```

## [Optional] Install textacy (this will also install spaCy):

```shell
pip3 install textacy
```

## Instqll spaCy (not needed if above option used)
```shell
pip3 install spacy
```

## Notes on working in a virtualenv:

With virtualenvwrapper, you can use simple commands to step out of and into the virtualenv as needed (or delete it completely):

Disable the nei-core virtualenv:

```shell
deactivate
```

Reenable the nei-core virtualenv:
```shell
workon nei-core
```

Wipe the virtualenv (deactivate first):
```shell
rmvirtualenv nei-core
```
