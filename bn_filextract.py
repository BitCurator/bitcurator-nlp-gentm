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
#import xml.etree.ElementTree as ET
import textract
import logging
from bcnlp_listfiles import FileEntryLister
from bcnlp_fxtract import FileExtractor

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
    logging.info("bn_getimginfo: Image Info for image %s: ", image_path)
    filenames = pyewf.glob(image_path)
    ewf_handle = pyewf.handle()
    ewf_handle.open(filenames)

    img = ewf_Img_Info(ewf_handle)
    return img

# Dict to number of partitions in each image
partition_in = dict()

logging.basicConfig(filename= 'bcnlp_tm_info.log', level=logging.INFO)
logging.basicConfig(filename= 'bcnlp_tm_debug.log', level=logging.DEBUG)

class BnFilextract:
    """ This class contains the file extraction methods from 
        disk images.
    """
    num_partitions = 0
    part_array = ["image_path", "addr", "slot_num", "start_offset", "desc"]
    partDictList = []
    num_partitions_ofimg = dict()

    def bnlpGetFsForImage(self, image_path, image_index, partition_num):
        """ Gets the filesystem info for an image and partition,
            using Pytsk3 method

        Args:
          image_path: Path to disk image
          image_index: Internally maintained serial number of the iamge
          partition_num: Partition within the volume

        Returns:
          Filesystem descriptor
        """
        logging.info('bnlpGetFsForImage: image_path: %s', image_path)
        logging.info('bnlpGetFsForImage: index: %s', image_index)
        logging.info('bnlpGetFsForImage: part: %s', partition_num)
        img = bn_getimginfo(image_path)
        
        part_start =  \
         self.partDictList[int(image_index)][partition_num]['start_offset']

        fs = pytsk3.FS_Info(img, offset=(part_start * 512))
        return fs

    def bnGetExFmtsFromConfigFile(self, config_file):
        """Extract the list of excluded format types from the given
           config file.

        Args:
          config_file: Configuration file

        Returns:
          list of the format types to be excluded.
        """
        exc_fmt_list = []
        config = ConfigObj(config_file)
        section = config["exclude_format_section"]
        for key in section:
            if section[key]:
                exc_fmt_list.append(key)

        return exc_fmt_list

    def bnGetFileContents(self, filename, config_file):
        """EXtract the contents of a file while doing nlp on a local
           directory of files as opposed to a disk image.
 
        Args:
            filename: Given file
            config_file: Configuration file
        """
        if filename.endswith('.txt') or filename.endswith('.TXT'):
            with open(filename, 'r') as tempfile:
                #input_file_contents = tempfile.read().replace('\n', '')
                input_file_contents = tempfile.read()
        
        else:
            # Eliminate the files that are configured to be excluded
            fn, filetype = os.path.splitext(filename)
            exc_fmt_list = self.bnGetExFmtsFromConfigFile(config_file)
            if filetype in exc_fmt_list:
                logging.info("File type %s excluded: %s", filetype, fn)
                return None
            logging.info("Filename %s is not a txt file. So textracting", \
                                                          filename)

            try:
                input_file_contents = textract.process(filename)
                #logging.info("bcnlp:: File contents of %s %s ",\
                    # filename, input_file_contents)
            except:
                print("\n >>> textract failed for doc {} ".format(filename))
                return None

        return input_file_contents 

    def bn_traverse_infile_dir(self, filextract_dir, documents, config_file):
        ''' This routine traverses the given directory to extract the
            files and adds the contents to the global documents list.

        Args:
          filextract_dir: Direcotry whose files need to be extracted.
          documents: Where the contents of th files will go.
          config_file: Configuration file.
        '''

        num_docs = 0
        for root, dirs, files in os.walk(filextract_dir):
            path = root.split(os.sep)
            '''
            logging.info("traverse: path: %s, length: %s ", path, len(path))
            logging.info("traverse: dirs: %s ", dirs)
            logging.info("traverse: files: %s ", files)
            '''
            for filename in files:
                file_path = '/'.join(path) + '/' + filename
                doc = self.bnGetFileContents(file_path, config_file)
                logging.info("D2: traverse: Appending doc %s \
                                     to documents list ", doc)
                documents.append(doc)
                num_docs += 1
            logging.info("D2: traverse: Total num docs: ", num_docs)

    def bnDfvfsGenerateFileList(self, image_path):
        """ Using Dfvfs methods, file-list is geenrated from the given 
            disk image in an output file with the name:
            <image_name>_filelist

        Args:
          image_path: Path to specified image
      
        """
        num_partitions = 1

        file_entry_lister = FileEntryLister()
        try:
            num_partitions = file_entry_lister.ListAllFiles(image_path)
            
        except:
            print "file_entry_lister failed"
            return(0)

        return num_partitions

    def bnCreateDirsInPath(self, file_extract_dir, filepath):
        """ Looking at the path of the file, directories are created
            if they don't yet exist.

        Args:
          file_extract_dir: Directory where files are to be extracted.
          filepath: Path to the file
        """
        filename = os.path.basename(filepath)
        dir_name = os.path.dirname(filepath)

        current_dir = os.path.join(os.getcwd(), file_extract_dir)
        file_list = filepath.split('/')
        logging.info("bnCreateDirsInPath: file_list: %s ", file_list)

        listlen = len(file_list)

        newdir = os.path.join(current_dir, file_list[0])
        for i in range (0, listlen-1):
            #logging.info("i:%s file_list[i]: %s", i, file_list[i])
            if os.path.exists(newdir):
                newdir = os.path.join(newdir, file_list[i+1])
            else:
                logging.info("bnCreateDirsInPath: Creating dir: %s", newdir)
                os.mkdir(newdir)
                newdir = os.path.join(newdir, file_list[i+1])
        

    def bnExtractFiles(self, ent, image, image_index, parse_en, config_file):
        """ Generate file-list from the disk image and extract the
            files into a specified directory.
 
        Args:
            ent: Placeholder
            image: disk image
            image_index: Internally maintained index for the image
            parse_en: Placeholder
            config_file: Name of the configuration file.
        """
        fname = sys._getframe().f_code.co_name
        logging.info("%s: Extracting files for img: %s, with config_file: %s ",\
                                                 fname, image, config_file)

        config = ConfigObj(config_file)
        exc_fmt_list = self.bnGetExFmtsFromConfigFile(config_file)

        file_extract_dir = "file_staging_directory"
        config_section = config['confset_section']
        for key in config_section:
           #print (key, config_section[key])
           if key == "file_staging_directory":
               file_extract_dir = config_section[key]
               break
        else:
           print("file_staging_directory not found in config file. \
                          using default\n")
        disk_image_dir = self.bnGetConfigInfo(config_file, \
                         "confset_section", "disk_image_dir")

        image_path = os.getcwd() + "/" + disk_image_dir + "/" + image

        file_extract_dir_path = os.getcwd() + '/'+ file_extract_dir

        print "\n>> Files will be extracted in ", file_extract_dir_path

        cmd = "mkdir " + file_extract_dir
        if not os.path.exists(file_extract_dir):
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        file_extract_dir_per_image = file_extract_dir + '/' + str(image_index)
        cmd = "mkdir " + file_extract_dir_per_image
        if not os.path.exists(file_extract_dir_per_image):
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)

        self.num_partitions = \
            self.bnlpGetPartInfoForImage(image_path, image_index)

        '''
        # Call Dfvfs method to generate the file-list in the image
        self.num_partitions = self.bnDfvfsGenerateFileList(image_path)
        partition_in[image] = self.num_partitions
        '''

        logging.info("%s: # partitions:%s Generating filelist ", fname, \
                                              self.num_partitions)

        logging.info("%s: Generated filelist. Extract contents", fname)

        file_entry_lister = FileEntryLister()
        output_path = file_extract_dir_per_image
        base_path_spec = file_entry_lister.GetBasePathSpec(image_path)

        #file_entry = resolver.Resolver.OpenFileEntry(base_path_spec)
        file_entry = file_entry_lister.GetFileEntry(base_path_spec)

        fe = FileExtractor(base_path_spec, output_path)
        fe.start()
        fe.AddFileToQueue(file_entry, image_path)

        #fe.Finish()
        print("[{}]: Jobs: {}".format(fname, fe.jobs))

        for job in fe.jobs:
            job.join()
        fe.Finish()

        print(">> Files extractd for the image {} at {}".format(image, file_extract_dir_per_image)) 

        '''
        # NOTE: Original code - to be removed after testing with new
        # file-extraction code.
        for p in range(0, self.num_partitions):
            logging.info("%s: Extracting contents from part p = %s", fname, p)
            listfile = image_path + "_filelist" + "_p" + str(p+1)
            logging.info("%s: Reading from listfile %s to extract contents", \
                                               fname, listfile)

            with open(listfile) as lf:
                for line in lf:
                    logging.info("File:%s ", line)
                    if "Volume Label Entry" in line:
                        continue
                    filename = os.path.basename(line).rstrip()
                    dirname = os.path.dirname(line).rstrip()
                    logging.info("Filename: %s ", filename)

                    if self.isFileTextractable(filename, config_file):
                        logging.info("File %s is textractable", line)

                        # If directory for partition doesn't exist, create.
                        part_dir = os.path.join(file_extract_dir_per_image, \
                                                           str(p))
                        if not os.path.exists(part_dir):
                            os.mkdir(part_dir)
                            logging.info("%s: Created directory %s",\
                                                     fname, part_dir)

                        # Make sure all the directories in the path are created.
                        logging.info("%s: Creating directories for path %s ",\
                                       fname, line)
                        self.bnCreateDirsInPath(part_dir, line)

                        # Get the inode for the file
                        file_entry_lister = FileEntryLister()

                        u_image_path = unicode(image_path, "utf-8")
                        u_line = unicode(line, "utf-8")

                        file_path = part_dir + u_line.rstrip()
                        logging.info("%s: Writing file to directory: %s",\
                                        fname, file_path)
                        inode = file_entry_lister.GetInodeForFile(\
                                        u_image_path, u_line.rstrip())

                        logging.info("%s: Inode:%s ", fname, str(inode))
                        logging.info("%s: Getting FS for file %s \
                                and partition %s" ,fname, file_path, p)
                        if inode < 0:
                            logging.info("%s: Inode for file %s is %d", \
                               fname, file_path, inode)
                            continue
                                    
                        fs = self.bnlpGetFsForImage(image_path, \
                                                    image_index, \
                                                    p)
                        # Now copy the file to the directory
                        self.bnlpDnldFile(inode, fs, file_path)
                    else:
                        logging.info("%s: File not textractable:%s ",\
                                                  fname, filename)
        '''
                  
                    
    def isFileTextractable(self, filename, config_file):
        """ Not all files are extractable as text file. Before extracting
            a file, it should pass this test.
        Args: 
          filename: Input file
          config_file: Name of the config file
        """
        logging.info("isTextratable: filename: %s ", filename)

        if (filename.endswith('.txt') or filename.endswith('.TXT') or  \
            filename.endswith('.pdf') or filename.endswith('.PDF') or \
            filename.endswith('.xml') or \
            filename.endswith('.XML') or \
            filename.endswith('.doc') or filename.endswith('.DOC') or \
            filename.endswith('.htm') or filename.endswith('.HTM;1') or \
            filename.endswith('.html') or filename.endswith('.HTML') or \
            filename.endswith('.jpg') or filename.endswith('.JPG') ):

            # if any of the above types are configured to be exluded,
            # filter them out.
            fn, fe = os.path.splitext(filename)
            exc_fmt_list = self.bnGetExFmtsFromConfigFile(config_file)
            logging.info("isFileTextratable:file:%s, exc_fmt_list: %s", \
                                    filename, exc_fmt_list)
            if fe in exc_fmt_list:
                logging.info("isTextraxtable:File %s configured \
                             to be excluded",filename)
                return False
            return True
        else:
            return False

    def bnIsEntityInfoSetInConfig(self, config_file):
        """ Filter for some legacy code.
            FIXME: Will be removed from here eventually
        """
        entity_info = self.bnGetConfigInfo(\
           config_file, "confset_section", "entity_info")
        if entity_info == "Yes":
            return True
        else:
            return False

    def bnlpDnldFile(self, inode, fs, filepath):
        """ Extracts the contents of a given file.
        Args:
          inode: Inode of the given file
          fs: Filesystem info 
        """
        logging.info("bnlpDnldFile: file_path:%s, inode:%d",filepath, inode)
        try:
            f = fs.open_meta(inode=inode)
        except:
            logging.info("fs.open_meta failed for file %s ", filepath)
            return

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
            logging.info("bnlpDnldFile: D2: Length OF TOTAL DATA: %s ", \
                                  str(len(total_data)))

        logging.info("bnlpDnldFile: D2: Dumping the contents to filepath %s ",\
                                                   filepath)

        try:
            with open(filepath, "w") as text_file:
                text_file.write(total_data)
        except IOError, e:
            print("Opeing the file {} failed with error {}", filepath, e)
            return

        ## print ("D2: Time to index the file ", filepath)
        basepath = os.path.dirname(filepath)

    def bnGetConfigInfo(self, config_file, section_name, cfg_string):
        """Given the key, extract info from the config file

        Args:
          config_file: Configuration filename
          section_name: Name of the section within the config file
          cfg_string: What we ase looking for - the key
        """
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

    def bnlpGetNumPartsForImage(self, image_path, image_index):
        img = bn_getimginfo(image_path)

        # pytsk3.Volume_Info works only with file systems which have partition
        # defined. For file systems like FAT12, with no partition info, we need
        # to handle in an exception.
        try:
            volume = pytsk3.Volume_Info(img)
        except:
            logging.info(">> Volume Info failed. Could be FAT12 ")
            self.num_partitions = 1
            return (self.num_partitions)

        for part in volume:
            if part.slot_num >= 0:
                try:
                    fs = pytsk3.FS_Info(img, offset=(part.start * 512))
                except:
                    logging.info(">> Exception in pytsk3.FS_Info in prtn:%s ",
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
                    logging.info("Exception in pytsk3.FS_Info for prtn:%s",
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
        logging.info("Number of Partitions for image  %s = %s",
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
