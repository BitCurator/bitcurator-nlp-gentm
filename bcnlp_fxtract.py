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

import multiprocessing
import os
import errno
import re
import pytsk3
import logging
from dfvfs.resolver import resolver
from dfvfs.path import path_spec
from dfvfs.resolver import context
from bcnlp_listfiles import FileEntryLister
from dfvfs.path import factory as path_spec_factory
from dfvfs.lib import definitions

import argparse
try:
    from argparse import ArgumentParser
except ImportError:
    raise ImportError("This script requires ArgumentParser which is in Python 2.7 or Python 3.0")


class FileExtractor(multiprocessing.Process):
    def __init__(self,fs_path_spec,output_path):
        super(FileExtractor, self).__init__()
        self._READ_BUFFER_SIZE = 32768

        self.file_queue = multiprocessing.Queue()

        self.fs_path_spec = fs_path_spec
        self.output_path = output_path
        self.jobs = []

    def run(self):
        p = os.getpid()
        print(u"Running File Extractor: (PID {})".format(p))
        
        print("[REMOVE]PID: ", p)
        self.jobs.append(p)
        print("[REMOVE]Jobs: ", self.jobs)

        # We have to open the filesystem from within the process, cannot
        # be passed
        resolver_context = context.Context()
        file_system = resolver.Resolver.OpenFileSystem(
            self.fs_path_spec,
            resolver_context=resolver_context
        )

        # Read from the queue #
        while True:
            file_item = self.file_queue.get()
            if isinstance(file_item,unicode):
                if (file_item == u'TERMINATE'):
                    break
            elif isinstance(file_item,ExtractionInfo):
                # Get dfvfs file entry from our path_spec #
                outpath_stack = list(os.path.split(
                    self.output_path
                ))

                # Get dfvfs entry #
                file_entry = file_system.GetFileEntryByPathSpec(
                    file_item.path_spec
                )

                ads_name = self._GetStreamName(
                    file_item.full_path
                )

                # Export files based off of file_entry #
                self._ExportFiles(
                    file_system,
                    file_entry,
                    outpath_stack,
                    specified_ads_name=ads_name
                )
            else:
                print(u"Item type unhandled for type: {}; {}".format(
                    unicode(type(file_item)),
                    unicode(file_item)
                ))

        file_system.Close()

        print(u"Ending File Extractor: (PID {})".format(
            os.getpid()
        ))

    def _GetStreamName(self,full_path):
        ads_name = None

        if ':' in full_path:
            ads_name = full_path.split(':')[1]

        return ads_name

    def _GetExportFilename(self, outpath_stack, filename, ads_name=None):
        """Create a export filename"""
        export_filename = u''
        path_sep = os.pathsep
        export_path = os.path.sep.join(outpath_stack)

        name = os.path.basename(filename)
        if ads_name:
            name = u'{}.{}'.format(name,ads_name)
        export_filename = os.path.join(export_path, name)

        return export_filename

    def _ExportFiles(self, file_system, file_entry, outpath_stack, specified_ads_name=None):
        # Export if file_entry is a file #
        if file_entry.IsFile():
            for ads in file_entry._GetDataStreams():
                full_path = file_entry.path_spec.location

                if specified_ads_name:
                    # Only extract out this ads because it was specified #
                    if specified_ads_name != ads.name:
                        continue

                    full_path = u'{}:{}'.format(full_path,ads.name)

                if len(ads.name) > 0:
                    ads_name = ads.name
                    full_path = u'{}:{}'.format(full_path, ads.name)
                else:
                    ads_name = None

                export_name = self._GetExportFilename(
                    outpath_stack,
                    file_entry.name,
                    ads_name=ads_name
                )

                result = self._ExportFile(
                    file_entry,
                    export_name,
                    ads_name
                )
                if result:
                    #print(u"Exported {} to {}".format(full_path, export_name))
                    logging.info(u"Exported %s to %s",full_path, export_name)
                else:
                    print(u"{} Not Exported to {}".format(full_path, export_name))
        elif file_entry.IsDirectory():
            for sub_file_entry in file_entry.sub_file_entries:
                outpath_stack.append(file_entry.name)
                self._ExportFiles(
                    file_system,
                    sub_file_entry,
                    outpath_stack
                )
                outpath_stack.pop()

    def _ExportFile(self, file_entry, export_filename, ads_name):
        """Export a file"""
        _offset = None

        # Outfile #
        # Check that path exists #
        export_path = os.path.dirname(export_filename)
        if not os.path.isdir(export_filename):
            try:
                os.makedirs(export_path)
            except OSError as oserror:
                if oserror.errno != errno.EEXIST:
                    raise

        outfile = open(
            export_filename,
            'wb'
        )

        file_name = file_entry.name

        tsk_file = file_entry._tsk_file
        use_attribute = None

        if ads_name:
            data_stream_name = ads_name
            for attribute in tsk_file:
                if attribute.info.name == data_stream_name:
                    use_attribute = attribute
                    if data_stream_name == u'$J' and int(attribute.info.flags) & pytsk3.TSK_FS_ATTR_SPARSE:
                        # If USN Journal, start at end of sparse data run #
                        for run in attribute:
                            print "   Blocks %s to %s (%s blocks) [flags: %s] - [offset: %d]" % (
                                run.addr, run.addr + run.len, run.len, str(run.flags), run.offset
                            )
                            if run.flags != pytsk3.TSK_FS_ATTR_RUN_FLAG_SPARSE:
                                _offset = run.offset * tsk_file.info.fs_info.block_size
                                break
                    break

        if _offset is None:
            _offset = 0

        if use_attribute != None:
            _filesize = use_attribute.info.size
        else:
            _filesize = tsk_file.info.meta.size

        while _offset < _filesize:
            available_to_read = min(self._READ_BUFFER_SIZE, _filesize - _offset)

            if use_attribute != None:
                data = tsk_file.read_random(
                    _offset,
                    available_to_read,
                    use_attribute.info.type,
                    use_attribute.info.id
                )
            else:
                data = tsk_file.read_random(
                    _offset,
                    available_to_read
                )

            if not data:
                break

            _offset += len(data)

            outfile.write(data)

        outfile.close()
        return True

    #def AddFileToQueue(self,tsk_file_entry):
    def AddFileToQueue(self,tsk_file_entry, full_path):
        print("REMOVE-AddFileToQueue jobs: ", self.jobs)
        ''' ORIG
        einfo = ExtractionInfo(
            tsk_file_entry.path_spec,
            tsk_file_entry.full_path
        )
        '''
        einfo = ExtractionInfo(
            tsk_file_entry.path_spec,
            full_path
        )
        self.file_queue.put(einfo)

    def Finish(self):
        self.file_queue.put(u'TERMINATE')
        print ("[REMOVE] Finish: Jobs: ", self.jobs) 

class ExtractionInfo():
    def __init__(self,path_spec,full_path):
        self.path_spec = path_spec
        self.full_path = full_path


if __name__ == "__main__":
    parser = ArgumentParser(prog='bcnlp_fxtract.py', description='File Extraction')
    parser.add_argument('--config', action='store', help="Extract text")
    parser.add_argument('--image', action='store', help="Image")

    args = parser.parse_args()

    config_file = args.config
    if config_file == None:
        config_file = "bntm_config.txt"

    source_path = args.image
    if config_file == None:
        print("Image not specified ")
        os.exit()
    

    '''
    # Get the basePathSpec of the given file/dir
    #spath_basename = os.path.basename(spath)
    stat_info = os.stat(source_path)

    path_spec = path_spec_factory.Factory.NewPathSpec(
          definitions.TYPE_INDICATOR_OS, location=source_path)

    #bl_fle = bcnlp_listfiles.FileEntryLister()
    bl_fle = FileEntryLister()
    base_path_spec = bl_fle.GetBasePathSpec(source_path)

    #num_partitions = file_entry_lister.ListAllFiles(source_path)

    ####file_system = resolver.Resolver.OpenFileSystem(base_path_spec)
    ####file_entry = resolver.Resolver.OpenFileEntry(base_path_spec)

    output_path = os.path.join(os.getcwd(), "filextract_dir" )
    #fe = FileExtractor(base_path_spec)
    fe = FileExtractor(base_path_spec, output_path)
    file_entry = resolver.Resolver.OpenFileEntry(base_path_spec)
    '''

    bl_fle = FileEntryLister()
    base_path_spec = bl_fle.GetBasePathSpec(source_path)

    output_path = os.path.join(os.getcwd(), "new_filextract_dir" )
    file_location = os.path.join(os.getcwd(), "new_filextract_dir" )
    #image_location = os.path.join(os.getcwd(), "disk-images")
    os_path_spec = path_spec_factory.Factory.NewPathSpec(definitions.TYPE_INDICATOR_OS, location=source_path)
    ewf_path_spec = path_spec_factory.Factory.NewPathSpec(definitions.TYPE_INDICATOR_EWF, parent=os_path_spec)

    tsk_partition_path_spec = path_spec_factory.Factory.NewPathSpec(definitions.TYPE_INDICATOR_TSK_PARTITION, location=u'/p1', parent=ewf_path_spec)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(definitions.TYPE_INDICATOR_TSK, location=file_location, parent=tsk_partition_path_spec)

    #file_entry = resolver.Resolver.OpenFileEntry(tsk_path_spec)
    file_entry = resolver.Resolver.OpenFileEntry(base_path_spec)
    print("file_entry: ", file_entry)

    #fe = FileExtractor(tsk_path_spec, output_path)
    fe = FileExtractor(base_path_spec, output_path)
    fe.start()
    #fe.AddFileToQueue(file_entry)
    fe.AddFileToQueue(file_entry, source_path)
    print ("Added files to queue")

    fe.Finish()


    

    
