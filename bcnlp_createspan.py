#!/usr/bin/python
# coding=UTF-8
#
# BitCurator NLP Tools
# Copyright (C) 2016 -2017 
# All rights reserved.
#
# This code is distributed under the terms of the GNU General Public
# License, Version 3. See the text file "COPYING" for further details
# about the terms of this license.
#
# This file contains BitCurator NLP Tools code
#

import spacy
from configobj import ConfigObj
import os
import codecs
import sys
import textract
#import unicodedata
from warnings import warn

try:
    from argparse import ArgumentParser
except ImportError:
    raise ImportError("This script requires ArgumentParser which is in Python 2.7 or Python 3.0")
import logging
# Set up logging location
logging.basicConfig(filename='span.log', level=logging.DEBUG)

def replace_suffix(filename,orig, new):
    orig_suffix = '.' + orig
    new_suffix = '.' + new
    if filename.endswith(orig):
        filename = filename[:-len(orig_suffix)+1] + new_suffix

    return filename


class ParseForEnts():
    """ Parses the given file(s) into entities and generates the span
        Input: text, entity_list
        Output: Span file(s)
        entity_list can be configured in the file bcnlp_config.txt.
    """
    def __init__(self):
        self.spans = []
    def tagEnts(self, text, entity_list):
        # If text is not unicode, convert it.
        ###utext = text.decode('string_escape')
        ###utext = text.encode('utf-8')
        self.spacy_doc = nlp(text)
        logging.debug("SPACY_DOC Entities: \n")

        '''
        for ent in self.spacy_doc.ents:
            logging.debug("%s, %s, %s", ent, ent.label, ent.label_)
        '''

        for word in self.spacy_doc[:-1]:
            #logging.debug("Word: %s ", word)

            start = word.i
            end = word.i + 1
            while end < len(self.spacy_doc) and self.spacy_doc[end].is_punct:
                end += 1
            self.span = self.spacy_doc[start : end]
            ##logging.debug("tagEnts: Ent type of word %s is: %s or %s", word, \
                 # word.ent_type_, word.ent_type_.lower())
            if word.ent_type_ in entity_list or (word.ent_type_).lower() in entity_list:
                ## logging.debug("[D]tagEnts: ent_type %s is in entity_list ", \
                      ##word.ent_type_)
                end_char = "end: "+str(self.span.end_char)
                start_char = "start: "+str(self.span.start_char)
                ent_type = "type: "+word.ent_type_
                self.spans.append((end_char, start_char, ent_type))
                ##logging.debug("[D]tagEnts: Appended %s, New SPANS: %s ", \
                      ## word, self.spans)
            '''
            # Note: This is commented out to reduce noice in the log file.
            else:
                logging.debug("ent_type %s for word %s is NOT in entity_list", 
                        word.ent_type_, word)
            '''

        return self.spans

    def extractContents(self, infile):
        """ If infile is not in text format, it uses textract api to extract
            text out of the given file.
        """
        if infile.endswith('.span'):
            return None
        if not infile.endswith('.txt'):
            print("infile {} doesnt end with txt. So textracting".format(infile))
    
            '''
            # Note: This is just in case we want to see the conversion
            # copied to a file
            filename, file_ext = os.path.splitext(infile)
            print("Filename: {}, ext: {}".format(filename, file_ext))
    
            new_infile = replace_suffix(infile,file_ext, 'txt')
            print "new_infile: ", new_infile
    
            f = codecs.open(new_infile, "r", "utf-8")
            input_file_contents = f.read()
    
            '''
            filename, file_ext = os.path.splitext(infile)
            try: 
                text = textract.process(infile)
            except:
                print("Textract probably does not support extension ", file_ext)
                return None
    
            #nlp expects a unicode text string. 
            input_file_contents = unicode(text,'utf-8')
    
        else:
            print "Extracting Contents of file", infile
            f = codecs.open(infile, "r", "utf-8")
            try:
                input_file_contents = f.read()
            except:
                print "Error reading file ", infile
                return None

        return input_file_contents

    def bnParseConfigFile(self, filename):
        """ Parses the configuration file bcnlp_config.txt to extract the 
            desired entities to be recognized.
        """
        config = ConfigObj(filename)
        entity_list_section = config['entity_list_section']
        cfg_entity_list = []
        for key in entity_list_section:
            logging.debug("Cfg: Key: %s %s ", key, entity_list_section[key])
            flag = int(entity_list_section[key])
            if flag == 1:
                logging.debug("Cfg: bnParseConfigFile: Appending key  %s: ", key) 
                cfg_entity_list.append(key)
        return cfg_entity_list

    def bcnlpProcessDir(self, infile):
        """ Recursively calls itself till it finds a file which is not a 
            directory, to process the file contents.
        """
        for f in os.listdir(infile):
            f_path = infile + '/' + f
            print "\n>> Processing file ", f_path
            logging.debug("bcnlpProcessDir: Processing file %s ",f_path)
            if os.path.isdir(f_path):
                self.bcnlpProcessDir(f_path)
            else:
                # It is a file
                logging.debug(">>>> Processing single file %s ", f_path)
                self.bcnlpProcessSingleFile(f_path)

    def bcnlpProcessSingleFile(self, infile):
        """ Given a file, it extracts the contents and calls tagEnts to
            create the spans for the entities given in the config file. 
        """
        outfile = infile+'.span'

        # Get the entity list from the config file:
        entity_list = self.bnParseConfigFile("bcnlp_config.txt")
        logging.debug("infile:{}, outfile:{}".format(infile, outfile))
        logging.debug("Entity List:%s: ", str(entity_list))

        text = self.extractContents(infile)

        if text == None:
            print("textract returned None for file ", infile)
            return
        spans = self.tagEnts(text, entity_list)
        '''
        # NOTE: just for debugging purpose. Produces a lot of log
        logging.debug("const text = %s", text)
        logging.debug("const spans = %s", str(spans)) 
        logging.debug("const ents = %s", entity_list)
        '''
    
        if not os.path.exists(outfile):
            logging.debug('writing spans to outfile %s ', outfile)
            with open(outfile, "w") as of:
                text_line = ("const text = '"+ text + "'")
                try:
                    of.write(text_line.encode('utf8'))
                except UnicodeEncodeError as e:
                    print "Unicode Error({0}) ".format(e)
                    print (" ### Error in writing: ", infile)
                    return
                span_line = str(spans).replace('(','{')
                span_line = span_line.replace(')','}')
                span_line = unicode("const spans = "+ span_line, 'utf-8') 
                of.write("%s\n" % span_line)
                ent_line = unicode("const ents = " + str(entity_list), 'utf-8')
                of.write("%s\n" % ent_line)
        else:
            print("Outfile {} exists. So skipping".format(outfile))
    
        print("\n")
        print(" >> Wrote span info to output file ", outfile)

    def bnCleanSpanFiles(self, indir):
        """ A utility to remove all the span files generated. It recursively
            traverses through the specified directory and removes all spans.
            It is called when --cleanspan option is used in command-line
        """
        for f in os.listdir(indir):
            logging.debug("bnCleanSpanFiles: file %s: ", f)
            f_path = indir + '/' + f
            logging.debug("Processing file %s ", f_path)
            if f.endswith('span'):
                logging.debug("removing %s", f_path)
                os.remove(f_path)
            if os.path.isdir(f_path):
                logging.debug("Recursively calling bnCleanSpanFiles to remove \
                      files in %s", f_path)
                self.bnCleanSpanFiles(f_path)
    
def unicodify_if_str(x):
    """
    Converts strs into unicodes and leaves everything else unchanged.
    Assumes strs to be UTF-8 encoded.
    """
    if isinstance(x, str):
        return x.decode('utf-8')
    elif isinstance(x, unicode):
        #warn(x.encode('utf-8') + b" already is unicode. ")
        logging.debug(" The given string is already is unicode. ")
        return x
    else:
        return x

def utf8ify_if_unicode(x):
    """
    Turns unicode arguments into strs.
    When given a unicode argument, encodes it as UTF-8 str. Warns when given
    strs. Returns everything else unchanged.
    """
    if isinstance(x, unicode):
        return x.encode('utf-8')
    elif isinstance(x, str):
        warn(x + b" already is str. ")
        return x
    else:
        return x

if __name__ == "__main__":
    parser = ArgumentParser(prog='bcnlp_createspan.py', description='Create NE Span')
    parser.add_argument('--infile', action='store', help="... ")
    ##parser.add_argument('--outfile', action='store', help="... ")
    parser.add_argument('--cleanspan', action="store_true", help="... ")
    parser.add_argument('--nolog', action="store_true", help="... ")

    args = parser.parse_args()

    infile = args.infile

    if args.nolog == True:
        # disable logging to console
        print(">> disabling logging ")
        #logger = logging.getLogger()
        #logger.propagate = False
        logging.disable(logging.DEBUG)

    if infile == None: 
        print("\n>> Please specify input file or directory.")
        print(">> Usage: python bcnlp_createspan.py --infile <input text file> ")
        raise SystemExit, -1


    span = ParseForEnts()
    if args.cleanspan == True:
        print "Cleanspan Flag: ", args.cleanspan
        if os.path.isdir(infile):
            span.bnCleanSpanFiles(infile)
        print "Cleaning done"
        raise SystemExit, 0

    nlp = spacy.load('en')
    if os.path.isdir(infile):
        logging.debug("%s is a directory. Traversing the directory", infile)

        # Traverse through the directory tree and read in every file.
        span.bcnlpProcessDir(infile)
    else:
        outfile = infile+".span"
        if os.path.exists(outfile):
            print("\n>> Outfile {} exists. Remove it before running the script".\
                  format(outfile)) 
            raise SystemExit, -1
        print "Processing bcnlpProcessSingleFile \n"
        span.bcnlpProcessSingleFile(infile)
        
