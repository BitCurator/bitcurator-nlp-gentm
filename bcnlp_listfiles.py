#!/usr/bin/python
# -*- coding: utf-8 -*-

# BitCurator NLP 
# Copyright (C) 2016 - 2018
# All rights reserved.
#
# This code is distributed under the terms of the GNU General Public
# License, Version 3. See the text file "COPYING" for further details
# about the terms of this license.
#
# This file contains the File Extraction routines for BitCurator NLP.
#

"""Script to list file entries.
   Extended from dfvfs example code list_file_entries.py
"""

from __future__ import print_function
import argparse
import logging
import os
import stat
import sys

from dfvfs.analyzer import analyzer
from dfvfs.lib import definitions
from dfvfs.lib import raw
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver
from dfvfs.volume import tsk_volume_system

class FileEntryLister(object):
  """Class that lists file entries."""

  # Class constant that defines the default read buffer size.
  _READ_BUFFER_SIZE = 32768

  # For context see: http://en.wikipedia.org/wiki/Byte
  _UNITS_1000 = [u'B', u'kB', u'MB', u'GB', u'TB', u'EB', u'ZB', u'YB']
  _UNITS_1024 = [u'B', u'KiB', u'MiB', u'GiB', u'TiB', u'EiB', u'ZiB', u'YiB']

  def _GetHumanReadableSize(self, size):
    """Retrieves a human readable string of the size.

    Args:
      size: The size in bytes.

    Returns:
      A human readable string of the size.
    """
    magnitude_1000 = 0
    size_1000 = float(size)
    while size_1000 >= 1000:
      size_1000 /= 1000
      magnitude_1000 += 1

    magnitude_1024 = 0
    size_1024 = float(size)
    while size_1024 >= 1024:
      size_1024 /= 1024
      magnitude_1024 += 1

    size_string_1000 = None
    if magnitude_1000 > 0 and magnitude_1000 <= 7:
      size_string_1000 = u'{0:.1f}{1:s}'.format(
          size_1000, self._UNITS_1000[magnitude_1000])

    size_string_1024 = None
    if magnitude_1024 > 0 and magnitude_1024 <= 7:
      size_string_1024 = u'{0:.1f}{1:s}'.format(
          size_1024, self._UNITS_1024[magnitude_1024])

    if not size_string_1000 or not size_string_1024:
      return u'{0:d} B'.format(size)

    return u'{0:s} / {1:s} ({2:d} B)'.format(
        size_string_1024, size_string_1000, size)

  def _GetNextLevelTSKPartionVolumeSystemPathSpec(self, source_path_spec, is_single_part):
    """Determines the next level volume system path specification.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).

    Returns:
      The next level volume system path specification (instance of
      dfvfs.PathSpec).

    Raises:
      RuntimeError: if the format of or within the source is not supported.
    """
    volume_system_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK_PARTITION, location=u'/',
        parent=source_path_spec)

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(volume_system_path_spec)

    volume_identifiers = []
    for volume in volume_system.volumes:
      volume_identifier = getattr(volume, 'identifier', None)
      if volume_identifier:
        volume_identifiers.append(volume_identifier)

    if not volume_identifiers:
      logging.warning(u'No supported partitions found.')
      return source_path_spec

    if (len(volume_identifiers) == 1) or (is_single_part == True):
      return path_spec_factory.Factory.NewPathSpec(
          definitions.TYPE_INDICATOR_TSK_PARTITION, location=u'/p1',
          parent=source_path_spec)

    print(u'The following partitions were found:')
    print(u'Identifier\tOffset\t\t\tSize')

    for volume_identifier in sorted(volume_identifiers):
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise RuntimeError(
            u'Volume missing for identifier: {0:s}.'.format(volume_identifier))

      volume_extent = volume.extents[0]
      print(
          u'{0:s}\t\t{1:d} (0x{1:08x})\t{2:s}'.format(
              volume.identifier, volume_extent.offset,
              self._GetHumanReadableSize(volume_extent.size)))

    print(u'')

    while True:
      print(
          u'Please specify the identifier of the partition that should '
          u'be processed:')

      selected_volume_identifier = sys.stdin.readline()
      selected_volume_identifier = selected_volume_identifier.strip()

      if selected_volume_identifier in volume_identifiers:
        break

      print(u'')
      print(
          u'Unsupported partition identifier, please try again or abort '
          u'with Ctrl^C.')
      print(u'')

    location = u'/{0:s}'.format(selected_volume_identifier)

    return path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK_PARTITION, location=location,
        parent=source_path_spec)

  def _GetNextLevelTSKPartionVolumeSystemPathSpecForBcnlp(self, \
                                                          source_path_spec,\
                                                          spath):
    """Determines the next level volume system path specification.
       and calls ListFileEntry to output the file-list from every
       partition into the specified output file.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).
      spath: source path

    Returns:
      number of Partitions

    Raises:
      RuntimeError: if the format of or within the source is not supported.
    """
    fname = sys._getframe().f_code.co_name
    spath_basename = os.path.basename(spath)
    volume_system_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_TSK_PARTITION, location=u'/',
        parent=source_path_spec)

    volume_system = tsk_volume_system.TSKVolumeSystem()
    volume_system.Open(volume_system_path_spec)

    volume_identifiers = []
    for volume in volume_system.volumes:
      volume_identifier = getattr(volume, 'identifier', None)
      if volume_identifier:
        volume_identifiers.append(volume_identifier)

    if not volume_identifiers:
      logging.warning(u'No supported partitions found.')
      return source_path_spec

    print(u'The following partitions were found:')
    print(u'Identifier\tOffset\t\t\tSize')

    for volume_identifier in sorted(volume_identifiers):
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      if not volume:
        raise RuntimeError(
            u'Volume missing for identifier: {0:s}.'.format(volume_identifier))

      volume_extent = volume.extents[0]
      print(
          u'{0:s}\t\t{1:d} (0x{1:08x})\t{2:s}'.format(
              volume.identifier, volume_extent.offset,
              self._GetHumanReadableSize(volume_extent.size)))

    print(u'')

    for volume_identifier in sorted(volume_identifiers):
      volume = volume_system.GetVolumeByIdentifier(volume_identifier)
      location = u'/{0:s}'.format(volume_identifier)
      base_path_spec = path_spec_factory.Factory.NewPathSpec( \
            definitions.TYPE_INDICATOR_TSK_PARTITION, location=location, \
        parent=source_path_spec)

      logging.info("%s: Listing files for partition: %s ", fname, \
                                                  volume_identifier)

      base_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_TSK, location=u'/',
            parent=base_path_spec)

      outfile = spath + "_filelist_" + str(volume_identifier)
      of = open(outfile, "a")
      logging.info("%s:Calling ListFileEntries to write list to file %s ",\
                                   fname, outfile)
      self.ListFileEntries(base_path_spec, of, volume_identifier)
      of.close()
    return len(volume_identifiers)

  def _GetNextLevelVshadowVolumeSystemPathSpec(self, source_path_spec):
    """Determines the next level volume system path specification.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).

    Returns:
      The next level volume system path specification (instance of
      dfvfs.PathSpec).

    Raises:
      RuntimeError: if the format of or within the source is not supported.
    """
    # TODO: implement.
    return source_path_spec

  def _GetUpperLevelVolumeSystemPathSpec(self, source_path_spec, is_single_part):
    """Determines the upper level volume system path specification.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).

    Returns:
      The upper level volume system path specification (instance of
      dfvfs.PathSpec).

    Raises:
      RuntimeError: if the format of or within the source is not supported.
    """
    type_indicators = analyzer.Analyzer.GetVolumeSystemTypeIndicators(
        source_path_spec)

    if not type_indicators:
      # No supported volume system found, we are at the upper level.
      return source_path_spec

    if len(type_indicators) > 1:
      raise RuntimeError(
          u'Unsupported source found more than one volume system types.')

    if type_indicators[0] == definitions.TYPE_INDICATOR_TSK_PARTITION:
      path_spec = self._GetNextLevelTSKPartionVolumeSystemPathSpec(
          source_path_spec, is_single_part)

    elif type_indicators[0] == definitions.TYPE_INDICATOR_VSHADOW:
      path_spec = self._GetNextLevelVshadowVolumeSystemPathSpec(
          source_path_spec)

    else:
      raise RuntimeError((
          u'Unsupported source found unsupported volume system '
          u'type: {0:s}.').format(type_indicators[0]))

    return path_spec

  def _GetUpperLevelVolumeSystemPathSpecForBcnlp(self, source_path_spec, spath):
    """Determines the upper level volume system path specification,
       then calls methods to lsit files from all partitions into the
       specified file.

    Args:
      source_path_spec: the source path specification (instance of
                        dfvfs.PathSpec).
      of: Output file descriptor

    Returns: number partitions

    Raises:
      RuntimeError: if the format of or within the source is not supported.
    """
    fname = sys._getframe().f_code.co_name
    type_indicators = analyzer.Analyzer.GetVolumeSystemTypeIndicators(
        source_path_spec)

    if not type_indicators:
      # No supported volume system found, we are at the upper level.
      return source_path_spec

    if len(type_indicators) > 1:
      raise RuntimeError(
          u'Unsupported source found more than one volume system types.')

    if type_indicators[0] == definitions.TYPE_INDICATOR_TSK_PARTITION:
      partitions = self._GetNextLevelTSKPartionVolumeSystemPathSpecForBcnlp(
          source_path_spec, spath)

    elif type_indicators[0] == definitions.TYPE_INDICATOR_VSHADOW:
      path_spec = self._GetNextLevelVshadowVolumeSystemPathSpec(
          source_path_spec)

    else:
      raise RuntimeError((
          u'Unsupported source found unsupported volume system '
          u'type: {0:s}.').format(type_indicators[0]))

    return partitions

  def _ListFileEntry(
      self, file_system, file_entry, parent_full_path, output_writer, p):
    """Lists a file entry.
      #self, file_system, file_entry, parent_full_path, output_writer, p):

    Args:
      file_system: the file system (instance of dfvfs.FileSystem).
      file_entry: the file entry (instance of dfvfs.FileEntry).
      parent_full_path: the full path of the parent file entry.
      output_writer: the output writer (instance of StdoutWriter).
    """
    # Since every file system implementation can have their own path
    # segment separator we are using JoinPath to be platform and file system
    # type independent.
    full_path = file_system.JoinPath([parent_full_path, file_entry.name])
    if file_entry.IsFile():
      output_writer.write(full_path)
      output_writer.write("\n")

    for sub_file_entry in file_entry.sub_file_entries:
      self._ListFileEntry(file_system, sub_file_entry, full_path, output_writer, p)

  def ListFileEntries(self, base_path_spec, output_writer, partition):
    """Lists file entries in the base path specification.

    Args:
      base_path_spec: the base path specification (instance of dfvfs.PathSpec).
      output_writer: the output writer (instance of StdoutWriter).
    """

    file_system = resolver.Resolver.OpenFileSystem(base_path_spec)
    file_entry = resolver.Resolver.OpenFileEntry(base_path_spec)
    if file_entry is None:
      print(
          u'Unable to open base path specification:\n{0:s}'.format(
              base_path_spec.comparable))
      logging.warning(
          u'Unable to open base path specification:\n{0:s}'.format(
              base_path_spec.comparable))
      return

    self._ListFileEntry(file_system, file_entry, u'', output_writer, partition)

  def GetInodeForFile(self, image_path, file_path):
    """Returns the Inode of the given file in the given image.

    Args:
      image_path: Path to the image
      file_path: Path to the given fime.
    """
    logging.info("GetInode: image_path: %s ", image_path)
    logging.info("GetInode: file_path:%s ", file_path)
    os_path_spec = path_spec_factory.Factory.NewPathSpec(\
                    definitions.TYPE_INDICATOR_OS, location=image_path)
    ewf_path_spec = path_spec_factory.Factory.NewPathSpec(\
                    definitions.TYPE_INDICATOR_EWF, parent=os_path_spec)
    tsk_partition_path_spec = path_spec_factory.Factory.NewPathSpec(\
                    definitions.TYPE_INDICATOR_TSK_PARTITION, \
                    location=u'/p1', parent=ewf_path_spec)
    tsk_path_spec = path_spec_factory.Factory.NewPathSpec(\
                      definitions.TYPE_INDICATOR_TSK, location=file_path, \
                      parent=tsk_partition_path_spec)
    file_entry = resolver.Resolver.OpenFileEntry(tsk_path_spec)

    if (file_entry == None):
        return -1 

    stat_object = file_entry.GetStat()

    logging.info("Inode: for file %s = %s ",file_path, stat_object.ino)
    return(stat_object.ino)

  def GetBasePathSpec(self, source_path, is_single_part=False):
    """Determines the base path specification.
       (If is_sing_part is True (when this is called per partition),
       it doesn't get into checking the individual partitions).

    Args:
      source_path: the source path.

    Returns:
      The base path specification (instance of dfvfs.PathSpec).

    Raises:
      RuntimeError: if the source path does not exists, or if the source path
                    is not a file or directory, or if the format of or within
                    the source file is not supported.
    """
    if not os.path.exists(source_path):
      raise RuntimeError(u'No such source: {0:s}.'.format(source_path))

    stat_info = os.stat(source_path)

    if (not stat.S_ISDIR(stat_info.st_mode) and
        not stat.S_ISREG(stat_info.st_mode)):
      raise RuntimeError(
          u'Unsupported source: {0:s} not a file or directory.'.format(
              source_path))

    if stat.S_ISDIR(stat_info.st_mode):
      path_spec = path_spec_factory.Factory.NewPathSpec(
          definitions.TYPE_INDICATOR_OS, location=source_path)

    elif stat.S_ISREG(stat_info.st_mode):
      path_spec = path_spec_factory.Factory.NewPathSpec(
          definitions.TYPE_INDICATOR_OS, location=source_path)

      type_indicators = analyzer.Analyzer.GetStorageMediaImageTypeIndicators(
          path_spec)

      if len(type_indicators) > 1:
        raise RuntimeError((
            u'Unsupported source: {0:s} found more than one storage media '
            u'image types.').format(source_path))

      if len(type_indicators) == 1:
        path_spec = path_spec_factory.Factory.NewPathSpec(
            type_indicators[0], parent=path_spec)

      if not type_indicators:
        # The RAW storage media image type cannot be detected based on
        # a signature so we try to detect it based on common file naming
        # schemas.
        file_system = resolver.Resolver.OpenFileSystem(path_spec)
        raw_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_RAW, parent=path_spec)

        glob_results = raw.RawGlobPathSpec(file_system, raw_path_spec)
        if glob_results:
          path_spec = raw_path_spec

      # In case we did not find a storage media image type we keep looking
      # since not all RAW storage media image naming schemas are known and
      # its type can only detected by its content.

      path_spec = self._GetUpperLevelVolumeSystemPathSpec(path_spec, is_single_part)

      # In case we did not find a volume system type we keep looking
      # since we could be dealing with a store media image that contains
      # a single volume.

      type_indicators = analyzer.Analyzer.GetFileSystemTypeIndicators(
          path_spec)

      if len(type_indicators) > 1:
        raise RuntimeError((
            u'Unsupported source: {0:s} found more than one file system '
            u'types.').format(source_path))

      if not type_indicators:
        logging.warning(u'Unable to find a supported file system.')
        path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_OS, location=source_path)

      elif type_indicators[0] != definitions.TYPE_INDICATOR_TSK:
        raise RuntimeError((
            u'Unsupported source: {0:s} found unsupported file system '
            u'type: {1:s}.').format(source_path, type_indicators[0]))

      else:
        path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_TSK, location=u'/',
            parent=path_spec)

    return path_spec

  def ListAllFiles(self, source_path):
    """Determines the base path specification and lists all the files
       per partition, in the given disk image file, into text files
       <disk_image>_filelist_<partition>
       Note: Modified routine from the original GetBasePathSpec method

    Args:
      source_path: the source path.

    Returns:
      The base path specification (instance of dfvfs.PathSpec).

    Raises:
      RuntimeError: if the source path does not exist, or if the source path
                    is not a file or directory, or if the format of or within
                    the source file is not supported.
    """

    fname = sys._getframe().f_code.co_name
    logging.debug("%s: Listing files for %s", fname, source_path)
    if not os.path.exists(source_path):
      raise RuntimeError(u'No such source: {0:s}.'.format(source_path))

    stat_info = os.stat(source_path)

    if (not stat.S_ISDIR(stat_info.st_mode) and
        not stat.S_ISREG(stat_info.st_mode)):
      raise RuntimeError(
          u'Unsupported source: {0:s} not a file or directory.'.format(
              source_path))
    if stat.S_ISDIR(stat_info.st_mode):
      path_spec = path_spec_factory.Factory.NewPathSpec(
          definitions.TYPE_INDICATOR_OS, location=source_path)

    elif stat.S_ISREG(stat_info.st_mode):
      path_spec = path_spec_factory.Factory.NewPathSpec(
          definitions.TYPE_INDICATOR_OS, location=source_path)

      type_indicators = analyzer.Analyzer.GetStorageMediaImageTypeIndicators(
          path_spec)

      if len(type_indicators) > 1:
        raise RuntimeError((
            u'Unsupported source: {0:s} found more than one storage media '
            u'image types.').format(source_path))

      if len(type_indicators) == 1:
        path_spec = path_spec_factory.Factory.NewPathSpec(
            type_indicators[0], parent=path_spec)

      if not type_indicators:
        # The RAW storage media image type cannot be detected based on
        # a signature so we try to detect it based on common file naming
        # schemas.
        file_system = resolver.Resolver.OpenFileSystem(path_spec)
        raw_path_spec = path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_RAW, parent=path_spec)

        glob_results = raw.RawGlobPathSpec(file_system, raw_path_spec)
        if glob_results:
          path_spec = raw_path_spec

      # In case we did not find a storage media image type we keep looking
      # since not all RAW storage media image naming schemas are known and
      # its type can only detected by its content.

      partitions = self._GetUpperLevelVolumeSystemPathSpecForBcnlp(path_spec,\
                                              source_path)

    return partitions
  def GetFileEntry(self, base_path_spec):
    return resolver.Resolver.OpenFileEntry(base_path_spec)


class StdoutWriter(object):
  """Class that defines a stdout output writer."""

  def Open(self):
    """Opens the output writer object.

    Returns:
      A boolean containing True if successful or False if not.
    """
    return True

  def Close(self):
    """Closes the output writer object."""
    pass

  def WriteFileEntry(self, path):
    """Writes the file path to stdout.

    Args:
      path: the path of the file.
    """
    print(u'{0:s}'.format(path))

