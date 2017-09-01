In order to run the topic modeling script bcnlp_tm.py, we need to 
install pytsk (for extrating file sfrom the disk images), gensim and GraphLab 
(for topic modeling using pyLDAvis).

[I]. Installation of pytsk
==========================

1. Install libewf-20140608  (This is the latest that works with tsk)
It is found here:
https://github.com/BitCurator/bitcurator-distro-main/tree/master/externals

tar zxvf libewf-20140608.tar.gz
cd libewf-20140608
./configure --enable-python --enable-v1-api
make -s
sudo make install
sudo ldconfig

2. Install libqcow (needed for pytsk)

wget -q https://github.com/libyal/libqcow/releases/download/20160123/libqcow-alpha-20160123.tar.gz

tar zxvf libqcow-alpha-20160123.tar.gz
cd libqcow-20160123
./configure --enable-python
make
sudo make install
sudo ldconfig

3. Install The Sleuth Kit from github

git clone https://github.com/sleuthkit/sleuthkit
cd sleuthkit
./bootstrap
./configure
make
sudo make install
sudo ldconfig

4. Install pytsk3 - latest

git clone https://github.com/py4n6/pytsk
cd pytsk
python setup.py update
python setup.py build
sudo python setup.py install

[II]. Installation of GraphLab
==============================

1. Install gensim: 
    pip install gensim
3. Install GraphLab: 
   One needs to request a registration product key from turi.com
   You will get a reply with the key and a customized installation procedure.
   For example this is the command I need to use:
   pip install --upgrade --no-cache-dir https://get.graphlab.com/GraphLab-Create/2.1/sunita@live.unc.edu/0295-EBD3-1F14-E97A-7FA1-5421-EA06-209A/GraphLab-Create-License.tar.gz
