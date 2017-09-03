#!/usr/bin/python
# coding=UTF-8
#
# BitCurator NLP 
# Copyright (C) 2014 - 2016
# All rights reserved.
#
# This code is distributed under the terms of the GNU General Public
# License, Version 3. See the text file "COPYING" for further details
# about the terms of this license.
#
# This file contains the File Extraction routines for BitCurator NLP.
#

# NOTE: The code is based on bca-webtools. Need to clean up to keep
# what is needed for NLP. 

import pytsk3
import pyewf
import os
import sys
import string
import time
import re
import logging
from configobj import ConfigObj
import subprocess
from subprocess import Popen,PIPE
import xml.etree.ElementTree as ET
import textract
#from bn_spacy import *
import logging

# FIXME: The following is needed only for bn_plot : See how it can be 
# selectively imported
#import bn_plot

class ewf_Img_Info(pytsk3.Img_Info):
  
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super(ewf_Img_Info, self).__init__(
            url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        self._ewf_handle.close()

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()

def bn_getimginfo(image_path):
    logging.debug("bn_getimginfo: Image Info for image %s: ", image_path) 
    filenames = pyewf.glob(image_path)
    ewf_handle = pyewf.handle()
    ewf_handle.open(filenames)

    img = ewf_Img_Info(ewf_handle)
    return img

# Dict to number of partitions in each image
partition_in = dict()
logging.basicConfig(filename= 'bcnlp.log', level=logging.DEBUG)

class BnFilextract:
    """ This class contains the file extraction methods from 
        disk images.
    """
    num_partitions = 0
    part_array = ["image_path", "addr", "slot_num", "start_offset", "desc"]
    partDictList = []
    num_partitions_ofimg = dict()
    exc_fmt_list = []
  
    def bnlpGetNumPartsForImage(self, image_path, image_index):
        img = bn_getimginfo(image_path)

        # pytsk3.Volume_Info works only with file systems which have partition
        # defined. For file systems like FAT12, with no partition info, we need
        # to handle in an exception.
        try:
            volume = pytsk3.Volume_Info(img)
        except:
            logging.debug(">> Volume Info failed. Could be FAT12 ")
            self.num_partitions = 1
            return (self.num_partitions)

        for part in volume:
            if part.slot_num >= 0:
                try:
                    fs = pytsk3.FS_Info(img, offset=(part.start * 512))
                except:
                    logging.debug(">> Exception in pytsk3.FS_Info in partition:%s ", 
                               self.num_partitions )
                    continue
                self.num_partitions += 1
        return (self.num_partitions)

    def bnlpGetPartInfoForImage(self, image_path, image_index):
        img = bn_getimginfo(image_path)
        is_partition_info = False

        # pytsk3.Volume_Info works only with file systems which have partition
        # defined. For file systems like FAT12, with no partition info, we need
        # to handle in an exception.
        try:
            volume = pytsk3.Volume_Info(img)
            is_partition_info = True
        except:
            ## print "bnlpGetPartionInfoForImage: Volume Info failed.
            ## Could be FAT12 "
            self.num_partitions = 1
            is_partition_info = False
            fs = pytsk3.FS_Info(img, offset=0)

            ## print "D: File System Type Detected ", fs.info.ftype
            if fs.info.ftype == pytsk3.TSK_FS_TYPE_FAT12:
                fs_desc = "FAT12 file system"
            elif fs.info.ftype == pytsk3.TSK_FS_TYPE_ISO9660_DETECT:
                fs_desc = "ISO file system"
            else:
		fs_desc = "Unknown file system"

            self.partDictList.append([])
            # First level files and directories off the root
            # returns file_list for the root directory
            file_list_root = self.bnlpListFiles(fs, "/", image_index, 0)
            image_name = os.path.basename(image_path)
            self.num_partitions_ofimg[image_name] = self.num_partitions

            # Populate the partDictList for the image.
            self.partDictList[image_index].append({self.part_array[0]:image_path, \
					     self.part_array[1]:0, \
					     self.part_array[2]:0, \
					     self.part_array[3]:0, \
					     self.part_array[4]:fs_desc })
            return self.num_partitions

        # For images with partition_info, we continue here.
        self.partDictList.append([])
        
        self.num_partitions = 0
        for part in volume:
            # The slot_num field of volume object has a value of -1
            # for non-partition entries - like Unallocated partition
            # and Primary and extended tables. So we will look for this
            # field to be >=0 to count partitions with valid file systems
            if part.slot_num >= 0:
                # Add the entry to the List of dictionaries, partDictList.
                # The list will have one dictionary per partition. The image
                # name is added as the first element of each partition to
                # avoid a two-dimentional list.
                ## print "D: image_path: ", image_path
                ## print "D: part_addr: ", part.addr
                ## print "D: part_slot_num: ", part.slot_num
                ## print "D: part_start_offset: ", part.start
                ## print "D: part_description: ", part.desc
                # Open the file system for this image at the extracted
                # start_offset.
                try:
                    fs = pytsk3.FS_Info(img, offset=(part.start * 512))
                except:
                    logging.debug("Exception in pytsk3.FS_Info for partition:%s", 
                                 self.num_partitions)
                    continue

                self.partDictList[image_index].append({self.part_array[0]:image_path, \
                                     self.part_array[1]:part.addr, \
                                     self.part_array[2]:part.slot_num, \
                                     self.part_array[3]:part.start, \
                                     self.part_array[4]:part.desc })

                self.num_partitions += 1

                fs = pytsk3.FS_Info(img, offset=(part.start * 512))

                # First level files and directories off the root
                # returns file_list for the root directory
                file_list_root = self.bnlpListFiles(fs, "/", image_index, part.slot_num)
                ## print(file_list_root)
                
        image_name = os.path.basename(image_path)
        self.num_partitions_ofimg[image_name] = self.num_partitions
        logging.debug("Number of Partitions for image  %s = %s", 
                                  image_name, self.num_partitions)
        return (self.num_partitions)

    bnlpFileInfo = ['name', 'size', 'mode', 'inode', 'p_inode', 'mtime', \
                     'atime', 'ctime', 'isdir', 'deleted', 'name_slug']

    def bnlpListFiles(self, fs, path, image_index, partition_num):
        file_list = []
        try:
           directory = fs.open_dir(path=path)
        except:
           print "Error in opening file path {} ".format(path)
           return None

        i=0
        for f in directory:
            is_dir = False
            '''
            print("Func:bnlpListFiles:root_path:{} size: {} inode: {} \
            par inode: {} mode: {} type: {} ".format(f.info.name.name,\
            f.info.meta.size, f.info.meta.addr, f.info.name.meta_addr,\
            f.info.name.par_addr, f.info.meta.mode, f.info.meta.type))
            '''
            # Some files may not have the metadta information. So
            # access it only if it exists.
            if f.info.meta != None:
                if f.info.meta.type == 2:
                    is_dir = True

                # Since we are displaying the modified time for the file,
                # Convert the mtime to isoformat to be passed in file_list.
                ## d = date.fromtimestamp(f.info.meta.mtime)
                ## mtime = d.isoformat()
                mtime = time.strftime("%FT%TZ",time.gmtime(f.info.meta.mtime))


                if (int(f.info.meta.flags) & 0x01 == 0):
                    deleted = "Yes"
                else:
                    deleted = "No"

                # NOTE: A new item "name_slug" is added to those file names which
                # have a space. The space is replaced by %20 and saved as name_slug.
                # This is used later when a file with a "non-None" name_slug shows
                # up at the route. It is recognized as a filename with spaces and
                # using the inode comparison, its real name is extracted before
                # downloading the file.
                name_slug = "None"
                if " " in f.info.name.name:
                    name_slug = f.info.name.name.replace(" ", "%20")
                file_list.append({self.bnlpFileInfo[0]:f.info.name.name, \
                              self.bnlpFileInfo[1]:f.info.meta.size, \
                              self.bnlpFileInfo[2]:f.info.meta.mode, \
                              self.bnlpFileInfo[3]:f.info.meta.addr, \
                              self.bnlpFileInfo[4]:f.info.name.par_addr, \
                              self.bnlpFileInfo[5]:mtime, \
                              self.bnlpFileInfo[6]:f.info.meta.atime, \
                              self.bnlpFileInfo[7]:f.info.meta.ctime, \
                              self.bnlpFileInfo[8]:is_dir, \
                              self.bnlpFileInfo[9]:deleted, \
                              self.bnlpFileInfo[10]:name_slug })

        ##print("Func:bnlpListFiles: Listing Directory for PATH: ", path)
        ##print file_list
        ##print "\n\n"
        return file_list


    def bnlpGenFileList(self, image_path, image_index, partition_num, root_path):
        logging.debug('D1: image_path: %s', image_path)
        logging.debug('D1: index: %s', image_index)
        logging.debug('D1: part: %s', partition_num)
        logging.debug('D1: root_path: %s', root_path)
        # print("D1: image_path: {} index: {} part: {} rootpath: \
             # {}".format(image_path, image_index, partition_num, root_path))
        img = bn_getimginfo(image_path)
        # Get the start of the partition:
        
        part_start =  \
         self.partDictList[int(image_index)][partition_num]['start_offset']

        # Open the file system for this image at the extracted
        # start_offset.
        fs = pytsk3.FS_Info(img, offset=(part_start * 512))

        file_list_root = self.bnlpListFiles(fs, root_path, image_index, partition_num)

        return file_list_root, fs

    def fixup_dfxmlfile(self, dfxmlfile):
        ## print("D: Fix up the dfxml file: ")
        with open(dfxmlfile) as fin, open("/tmp/tempfile", "w") as fout:
            for line in fin:
                if not "xmlns" in line:
                    if "dc:type" in line:
                        line = line.replace("dc:type","type")
                        fout.write(line)

        fin.close()
        fout.close()

        cmd = "mv /tmp/tempfile " + dfxmlfile
        subprocess.check_output(cmd, shell=True)
        logging.debug('>> : Updated dfxmlfile ')
        # print(">> : Updated dfxmlfile ")
        return dfxmlfile


    def bnlpGenerateDfxml(self, image_name, dfxmlfile):
        # First generate the dfxml file for the image
        #ewfinfo_xmlfile = os.getcwd() +"/"+ image_name+".xml"
        #cmd = "ewfinfo -f dfxml "+image_name+ " > "+ewfinfo_xmlfile
        print "\n>> bnlpGenerateDfxml: Generating dfxml file: ", dfxmlfile

        '''
        # FIXME: Just for testing: dfxml removed and recreated.
        #if dfxml_dir:
        if os.path.exists(dfxmlfile):
            rmcmd = ['rm', dfxmlfile]
            subprocess.check_output(rmcmd)
        '''


        if not os.path.exists(dfxmlfile):
            printstr = "WARNING!!! DFXML FIle " + dfxmlfile + \
                     " does NOT exist. Creating one"
            logging.debug('Warning: %s ', printstr)
            # print (printstr)
            cmd = ['fiwalk', '-b', '-g', '-z', '-X', dfxmlfile, image_name]
            logging.debug('CMD: %s ', cmd)
            # print ("CMD: ", dfxmlfile, cmd)
            subprocess.check_output(cmd)

        # Remove the name space info as the xml parsing won't give proper
        # tags with the name space prefix attached.
        ## print('D: Fiwalk generated dfxml file. Fixing it up now ')
        # print("D: Fiwalk generated dfxml file. Fixing it up now ")
        #self.fixup_dfxmlfile(dfxmlfile)
        #dfxmlfile = self.fixup_dfxmlfile(dfxmlfile)

        return dfxmlfile

    def bnGetExFmtsFromConfigFile(self, config_file):
        self.exc_fmt_list = []
        config = ConfigObj(config_file)
        section = config["exclude_format_section"]
        for key in section:
            if section[key]:
                self.exc_fmt_list.append(key)

        return self.exc_fmt_list

    def bnGetFileContents(self, filename):
        if filename.endswith('.txt') or filename.endswith('.TXT'):
            with open(filename, 'r') as tempfile:
                #input_file_contents = tempfile.read().replace('\n', '')
                input_file_contents = tempfile.read()
        
        else:
            # Eliminate the files that are configured to be excluded
            fn, filetype = os.path.splitext(filename)
            if filetype in self.exc_fmt_list:
                logging.debug("File type %s excluded: %s", filetype, fn)
                return None
            logging.debug("Filename %s is not a txt file. So textracting", filename) 

            try:
                input_file_contents = textract.process(filename)
                #logging.debug("bcnlp:: File contents of %s %s ",\
                    # filename, input_file_contents)
            except:
                print("\n >>> textract failed for doc {} ".format(filename))
                return None

        '''
        try:
            ent.bcnlpProcessText(img, filename, \
                 unicode(input_file_contents, "utf-8"), entity_list, 
                               parse_en, bg=False)
        except:
            return None
        '''
        return input_file_contents 

    def bn_traverse_infile_dir(self, filextract_dir, documents):
        ''' This routine traverses the given directory to extract the
        files and adds the contents to the global documents list.
        '''

        num_docs = 0
        for root, dirs, files in os.walk(filextract_dir):
            path = root.split(os.sep)
            '''
            print "path: ", path, len(path)
            print "dirs: ", dirs
            print "files: ", files
            print((len(path) - 1) * '---', os.path.basename(root))
            '''
            for filename in files:
                file_path = '/'.join(path) + '/' + filename
                doc = self.bnGetFileContents(file_path)
                # print("bnTraverseInFileDir: Appending doc {} \
                                     # to documents list ".format(doc))
                documents.append(doc)
                num_docs += 1
            # print "bnTraverseInFileDir: Total num docs: ", num_docs

    def bnExtractFiles(self, ent, image, image_index, parse_en, config_file):
        logging.debug("Extracting files for img: %s, with config_file: %s ",\
                                                 image, config_file)

        config = ConfigObj(config_file)

        file_extract_dir = "file_staging_directory"
        config_section = config['confset_section']
        for key in config_section:
           #print (key, config_section[key])
           if key == "file_staging_directory":
               file_extract_dir = config_section[key]
               break
        else:
           print "file_staging_directory not found in config file. \
                          using default\n"
        disk_image_dir = self.bnGetConfigInfo(config_file, \
                         "confset_section", "disk_image_dir")
        ## print "Disk image: ", disk_image_dir
        image_path = os.getcwd() + "/" + disk_image_dir + "/" + image
        ## print "Image Path: ", image_path

        file_extract_dir_path = os.getcwd() + '/'+ file_extract_dir
        print "\n>> Files will be extracted in ", file_extract_dir_path

        cmd = "mkdir " + file_extract_dir
        if not os.path.exists(file_extract_dir):
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        file_extract_dir_per_image = file_extract_dir + '/' + str(image_index)
        cmd = "mkdir " + file_extract_dir_per_image
        if not os.path.exists(file_extract_dir_per_image):
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)

        # FIXME: For multipart image, find the numparts here
        # partition_in[img] = self.num_partitions  (just a placeholder)
        # for now, num_partitions = 1
        self.num_partitions = \
            self.bnlpGetPartInfoForImage(image_path, image_index)
        ## print "NUM of partitions: ", self.num_partitions

        # Generate dfxml file if doesn't exist
        #file_extract_dir = self.bnGetConfigInfo("confset_section",
                        # "file_staging_directory")
        dfxmlfile = image_path +"_dfxml.xml"
        if not os.path.exists(dfxmlfile):
            print(">> Generating dfxml file as it doesn't exist ".\
                         format(dfxmlfile))
            self.bnlpGenerateDfxml(image_path, dfxmlfile)

        partition_in[image] = self.num_partitions

        root_dir = os.getcwd()

        for p in range(0, self.num_partitions):
            # make the directory for this img and partition
            part_dir = str(root_dir) + '/img'+str(image_index)+"_"+ str(p)
            file_list_root, fs =  \
              self.bnlpGenFileList(image_path, image_index,int(p), '/')

            if file_list_root == None:
                print "Error: File_list_root is None for image_path {} \
                            and part {}".format(image_path, p)
                continue

            self.bnlpDnldRepo(image, file_list_root, fs, image_index, p, \
                               image_path, '/', parse_en, ent, config_file)


    def isFileTextractable(self, filename):
        if (filename.endswith('.txt') or filename.endswith('.TXT') or  \
            filename.endswith('.pdf') or filename.endswith('.PDF') or \
            filename.endswith('.bnGetExFmtsFromConfigFilexml') or \
            filename.endswith('.XML') or \
            filename.endswith('.doc') or filename.endswith('.DOC') or \
            filename.endswith('.htm') or filename.endswith('.HTM;1') or \
            filename.endswith('.html') or filename.endswith('.HTML') or \
            filename.endswith('.jpg') or filename.endswith('.JPG') ):

            # if any of the above types are configured to be exluded,
            # filter them out.
            fn, fe = os.path.splitext(filename)
            logging.debug("isFileTextratable:file:%s, exc_fmt_list: %s", \
                                    self.exc_fmt_list, filename)
            if fe in self.exc_fmt_list:
                logging.debug("isTextraxtable:File %s configured \
                             to be excluded",filename)
                return False
            return True
        else:
            return False

    def bnlpDnldRepo(self, img, root_dir_list, fs, image_index, partnum, \
                        image_path, root_path, parse_en, ent, config_file):
        """This routine is used to download the indexable files of the Repo
        """
        ## print("Index-dbg2:COMM bnlpDnldRepo: Root={} len={} ".format(\
                           # root_path, len(root_dir_list)))

        num_elements = len(root_dir_list)
        if root_path == '/':
            new_path = ""
        else:
            new_path = root_path

        nlpdir = self.bnGetConfigInfo(config_file, "confset_section", "nlp_dir")
        if not os.path.exists(nlpdir):
            print ">> Creating nlpdir Directory ", nlpdir
            os.mkdir(nlpdir)
        else:
            logging.debug(">> Directory %s exists. ", nlpdir)

        token_file = nlpdir + "/" + "token_file"
        sents_file = nlpdir + "/" + "sents_file"
        post_file = nlpdir + "/" + "post_file"
        of = open(token_file,"a")
        of_sents = open(sents_file,"a")
        of_post = open(post_file,"a")

        ## print("Index-dbg2:bnlpDnldRepo:iterating within root_dir_list:{}, \
        ##                     new_path:{} ".format(root_dir_list, new_path)
        for item in root_dir_list:
            if item['isdir'] == True:
                logging.debug("bnlpDnldRepo: D1:It is a Directory %s", \
                                            str(item['name']))
                if item['name'] == '.' or item['name'] == '..':
                    continue

                if new_path == None:
                   ## print "Index-dbg1:root_path is None.Name: ", item['name']
                   continue

                new_path = new_path + '/'+ str(item['name'])

                dfxml_file = image_path + "_dfxml.xml"

                new_path = self.bnlpGetPathFromDfxml(str(item['name']), \
                                                   dfxml_file)
                ## print("D: bnlpDnldRepo: path from Dfxml file: ", new_path)
                if new_path == None:
                   ## print "Index-debug1: Path for file {} is not found in \
                   ##                    DFXML".format(dfxml_file)
                   continue
                # We will add image_index to the path so we can later
                # extract the image name to be displayed. We could have
                # passed the image name itself, instead of the index, but
                # if the image name has special characters, we might bump
                # into unexpected errors while creating files/directories
                # with an unknown string. So chose to use the image
                # index here and later extract the corresponding image name.

                file_extract_dir = self.bnGetConfigInfo(config_file, \
                      "confset_section", "file_staging_directory")
                directory_path = os.getcwd() + "/" + \
                        file_extract_dir+"/"+str(image_index) +"/"+new_path

                if not os.path.exists(directory_path):
                    cmd = "mkdir " + re.escape(directory_path)
                    ## print("bnlpDnldRepo:Creating directry with cmd: ", cmd)
                    try:
                        shelloutput = subprocess.check_output(cmd, shell=True)
                    except subprocess.CalledProcessError as cmdexcept:
                        logging.debug('Error return code: %s ', \
                                     cmdexcept.returncode)
                        logging.debug('Error output: %s ', \
                                     cmdexcept.output)
                    ## print("D2: Created directory {}".format(directory_path))

                # Generate the file-list under this directory
                new_filelist_root, fs = self.bnlpGenFileList(image_path, \
                       image_index, partnum, new_path)

                # if file_list is None, continue
                if new_filelist_root == None:
                    ## print "Index-dbg1:GetFileList retd Null filelist_root \
                    ##          for Image Path {}, partnum {}, new_path: \
                    ##          {}".format(image_path, partnum, new_path)
                    continue

                # Call the function recursively
                logging.debug("bnlpDnldRepo: D2: Calling func recursively \
                               with item-name: %s new_path:%s item: %s",  \
                               item['name'], new_path, item)
                foo = BnFilextract()
                foo.bnlpDnldRepo(img, new_filelist_root, fs, \
                        image_index, partnum, image_path, new_path, \
                        parse_en, ent, config_file)
            else:
                ## print("Index-dbg2:bnlpDnldRepo:It is a File", item['name'])
                filename = item['name'] # FIXME: Test more to make \
                                        # sure files with space work.
                #if item['name_slug'] != "None" and item['inode'] == int(inode) :
                if item['name_slug'] != "None" :

                    # Strip the digits after the last "-" from filepath \
                                       # to get inode
                    #new_filepath, separater, inode = filepath.rpartition("-")
                    ## print("D >> Found a slug name ", \
                           # item['name'], item['name_slug'])
                    filename = item['name_slug']

                # If it is indexable file, download it and generate index.
                if self.isFileTextractable(filename):

                    dfxml_file = image_path + "_dfxml.xml"
                    # We will use the 'real' file name while looking \
                    # for it in dfxml file
                    new_file_path = self.bnlpGetPathFromDfxml(item['name'], \
                                      dfxml_file)

                    # If there is space in the file-name, replace it by %20
                    new_file_path = new_file_path.replace(" ", "%20")

                    file_extract_dir = self.bnGetConfigInfo(config_file, \
                            "confset_section", "file_staging_directory")
                    file_path = file_extract_dir + "/" + str(image_index) + \
                                            "/" + str(new_file_path)

                    self.bnlpDnldSingleFile(item, fs, file_path, \
                                                 file_extract_dir)

                    ## print "D: Downloaded single file: ", file_path
                    if filename.endswith('.txt') or filename.endswith('.TXT'):
                        with open(file_path, 'r') as tempfile:
                            #input_file_contents =
                                #tempfile.read().replace('\n', '')
                            input_file_contents = tempfile.read()

                    else:
                        ## print("Filename {} is not a txt file. So \
                               ## textracting".format(filename))
                        fn, filetype = os.path.splitext(filename)
                        if filetype in self.exc_fmt_list:
                            logging.debug("bnlpDnldRepo:File type %s excluded",\
                                         filetype)
                            continue
                        logging.debug("Filename %s is not a txt file. So \
                                       textracting", filename) 
                        try:
                            input_file_contents = textract.process(file_path)
                            #logging.debug("bnlpDnldRepo: File contents of \
                                  # %s %s ",filename, input_file_contents)
                        except:
                            print("\n >>> textract failed for doc {} ".format(\
                                              file_path))
                            continue

                    # Text file is created. Now apply NLP features
                    img_file = img + ':'+filename

                    # FIXME: Commented out the following as these
                    # aren't needed for topic modeling code.
                    # Clean them up while testing the plot feature.
    
                    ##bnDoNlp(input_file_contents, "spacy", parse_en,
                               ##img_file, of, of_sents, of_post)
                    ##ent = bn_plot.ParseForEnts()
    
                    # Add this file and img to image_list and document_list
                    # to get the image_id and doc_id for the plot
                    ###img_id, doc_id = ent.getIdsForPlot(img, filename)
                    #ent.bcnlpProcessSingleFile(file_path, bg=False)
                    entity_list = None
                    if ent != None:
                        entity_list = ent.bnParseConfigFileForEnts(config_file)
                    '''
                    try:
                        utf_text = unicode(input_file_contents, "utf-8")
                    except:
                        print "UTF Exception. Sending text as is"
                        utf_text = input_file_contents
                    '''

                    try:
                        ent.bcnlpProcessText(img, filename, \
                           unicode(input_file_contents, "utf-8"), \
                           entity_list, parse_en, bg=False)
                    except:
                        continue
    def bnlpGetPathFromDfxml(self, in_filename, dfxmlfile):
        """ In order to get the complete path of each file being indexed,
            we use the information from the dfxml file. This routine looks
            for the given file in the given dfxml file and returns the
            <filename> info, whic happens to be the complete path.
            NOTE: In case this process is contributing significantly
            to the indexing time, we need to find a better way to get this info.
        """
        ##print("##D1: bnlpGetPathFromDfxml: in_filename: {}, \
                            ##  dfxmlfile: {}".format(in_filename, dfxmlfile))

        try:
            tree = ET.parse( dfxmlfile )
        except IOError, e:
            print('Failure parsing DFXML file %s ', e)
            # print "Failure Parsing %s: %s" % (dfxmlfile, e)

        root = tree.getroot() # root node
        for child in root:
            if child.tag == "{http://www.forensicswiki.org/wiki/Category:Digital_Forensics_XML}volume":
                volume = child
                for vchild in volume:
                    if vchild.tag == "{http://www.forensicswiki.org/wiki/Category:Digital_Forensics_XML}fileobject":
                        fileobject = vchild
                        for fo_child in fileobject:
                            if fo_child.tag == '{http://www.forensicswiki.org/wiki/Category:Digital_Forensics_XML}filename':
                                f_name = fo_child.text
                                # if this is the filename, return the path.
                                # "fielname" has the complete path in the
                                # DFXML file.
                                # Extract just the fiename to compare with
                                base_filename = os.path.basename(f_name)
                                ## print("D2: base_filename: {}, \
                                  ##f_name: {}".format(base_filename, f_name))
                                if in_filename == base_filename:
                                    return f_name

        return None

    def bnlpDnldSingleFile(self, file_item, fs, filepath, index_dir):
        """ While indexing we download every file in the image, index it
            and remove. This routine does exactly that - gets the inode
            of the file_item, calls the pytsk3 APs (open_meta, info.meta,
            read_random) to get the handle for that file, extract the size
            and read the data into a buffer. The buffer is copied into a
            file, which rsides in the same path as it does wihtin the disk
            image.
        """
        ## print(">> D1:Dnlding File: {}, file: {} ".\
                    #format(file_item['name'], filepath))

        f = fs.open_meta(inode=file_item['inode'])

        # Read data and store it in a string
        offset = 0
        size = f.info.meta.size
        BUFF_SIZE = 1024 * 1024

        total_data = ""
        while offset < size:
            available_to_read = min(BUFF_SIZE, size - offset)
            data = f.read_random(offset, available_to_read)
            if not data:
                # print("Done with reading")
                break

            offset += len(data)
            total_data = total_data+data
            ## print("D2: Length OF TOTAL DATA: ", len(total_data))

        ## print("D2: Dumping the contents to filepath ", filepath)

        with open(filepath, "w") as text_file:
            text_file.write(total_data)

        ## print ("D2: Time to index the file ", filepath)
        basepath = os.path.dirname(filepath)
    def bnGetConfigInfo(self, config_file, section_name, cfg_string):
        ## print "GetConfigInfo: Getting ", cfg_string
        config = ConfigObj(config_file)
        section = config[section_name]
        for key in section:
            if key == cfg_string:
                # found the string
                return section[key]
        else:
            print "bnGetConfigInfo: Key not found in section ", section_name

    def bnGetOutDirFromConfig(self, config_file):
        config = ConfigObj(config_file)

        file_extract_dir = "file_staging_directory"
        config_section = config['confset_section']
        for key in config_section:
           #print (key, config_section[key])
           if key == "file_staging_directory":
               file_extract_dir = config_section[key]
               return file_extract_dir
               break
        else:
           print("file_staging_directory not in config file - using default\n")
           return None

""" FIXME: Clean these up while testing the plot feature.
def bnDoNlp(contents, tool, parse_en, img_file, of, of_sents, of_post):
    nlpdir = bnGetConfigInfo("confset_section", "nlp_dir")
    logging.debug("\nNLPDIR:{}: \
           Applying NLP features for img-file:{} ".format(nlpdir, img_file))
    if tool in "spacy":
        spacy_outfile = bnGetConfigInfo("confset_section", "spacy_outfile")
        spacy_outfile_path = os.getcwd() + "/"+ nlpdir+"/"+ spacy_outfile
        ###print "bnDoNlp: SpacyOutFile: ", spacy_outfile_path

        '''
        if not os.path.exists(nlpdir):
            print ">> Creating nlpdir Directory ", nlpdir 
            os.mkdir(nlpdir)
        else:
            logging.debug(">> Directory %s exists. ", nlpdir)
        '''

        token_file = nlpdir + "/" + "token_file"
        ##of = open(token_file,"wb")
        sents_file = nlpdir + "/" + "sents_file"
        post_file = nlpdir + "/" + "post_file"

        logging.debug("Calling bnSpacyGetTokens with outfile %s ", token_file)
        # Get Tokens 
        bnSpacyGetTokens(contents, token_file, parse_en, img_file, of)
        # 
        ##print "\n\n>> Sentences......"

        # Get Sentences
        bnSpacyGetSents(contents, sents_file, parse_en, img_file, of_sents)
        #
        # Get Parts of Speech tagging
        bnSpacyGetPOSTagging(contents, post_file, parse_en, img_file, of_post)
        #
"""
