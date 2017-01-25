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
import subprocess 
import sys

try:
    from argparse import ArgumentParser
except ImportError:
    raise ImportError("This script requires ArgumentParser which is in Python 2.7 or Python 3.0")
import logging
# Set up logging location
logging.basicConfig(filename='span.log', level=logging.DEBUG)

def extractContents(infile):
    if not infile.endswith('.txt'):
        print("infile {} doesnt end with txt. So textracting".format(infile))

        filename, file_ext = os.path.splitext(infile)
        print("Filename: {}, ext: {}".format(filename, file_ext))

        new_infile = replace_suffix(infile,file_ext, 'txt')
        print "new_infile: ", new_infile
        textract_cmd = 'textract ' + infile + ' > ' + new_infile
        ## print "CMD: ", textract_cmd

        # Fixme: subprocess is not needed. The above line where textract.process
        # works fine, but it gives UicodeDecode error. But doing sdubprocess also
        # gives the same error when f.read() is done. Need to fix this.
        # UnicodeDecodeError: 'utf8' codec can't decode byte 0xc7 in position 10: invalid continuation byte
        subprocess.check_output(textract_cmd, shell=True, stderr=subprocess.STDOUT)

        f = codecs.open(infile, "r", "utf-8")
        input_file_contents = f.read()

        #input_file_contents = textacy.fileio.read.read_file(infile, mode=u'rt', encoding=None)

    else:
        print "Extracting Contents of file", infile
        f = codecs.open(infile, "r", "utf-8")
        input_file_contents = f.read()
        ##input_file_contents = textacy.fileio.read.read_file(infile, mode=u'rt', encoding=None)

    return input_file_contents

class ParseForEnts():
    def __init__(self):
        self.spans = []
    def tagEnts(self, text, entity_list):
        self.spacy_doc = nlp(text)
        logging.debug("SPACY_DOC Entities: \n")
        for ent in self.spacy_doc.ents:
            logging.debug("%s, %s, %s", ent, ent.label, ent.label_)

        for word in self.spacy_doc[:-1]:
            logging.debug("Word: %s ", word)

            start = word.i
            end = word.i + 1
            while end < len(self.spacy_doc) and self.spacy_doc[end].is_punct:
                end += 1
            self.span = self.spacy_doc[start : end]
            logging.debug("tagEnts: Ent type of word %s is: %s or %s", word, word.ent_type_, word.ent_type_.lower())
            if word.ent_type_ in entity_list or (word.ent_type_).lower() in entity_list:
                logging.debug("tagEnts: ent_type %s is in entity_list ",word.ent_type_)
                end_char = "end: "+str(self.span.end_char)
                start_char = "start: "+str(self.span.start_char)
                ent_type = "type: "+word.ent_type_
                #self.spans.append(   \
                    #(self.span.end_char, self.span.start_char, word.ent_type_))
                self.spans.append((end_char, start_char, ent_type))
                logging.debug("tagEnts: Appended %s, New SPANS: %s ", word, self.spans)
            else:
                logging.debug("ent_type %s for word %s is NOT in entity_list", 
                        word.ent_type_, word)

        return self.spans
            

def bnParseConfigFile(filename):
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

if __name__ == "__main__":
    parser = ArgumentParser(prog='bcnlp_createspan.py', description='Create NE Span')
    parser.add_argument('--infile', action='store', help="... ")
    parser.add_argument('--outfile', action='store', help="... ")

    args = parser.parse_args()
    infile = args.infile
    outfile = args.outfile

    if infile == None or outfile == None:
        print("\n>> Please specify input and output files.")
        print(">> Usage: python bcnlp_createspan.py --infile <input text file> --outfile <output file>")
        raise SystemExit, -1

    if os.path.exists(outfile):
        print("\n>> Outfile {} exists. Remove it before running the script".format(outfile)) 
        raise SystemExit, -1

    entity_list = bnParseConfigFile("bcnlp_config.txt")
    print "Entity List: ", entity_list
    ents = "["
     
    span = ParseForEnts()
    nlp = spacy.load('en')
    text = extractContents(infile)
    spans = span.tagEnts(text, entity_list)
    logging.debug("const text = %s", text)
    logging.debug("const spans = %s", str(spans)) 
    logging.debug("const ents = %s", entity_list)

    if not os.path.exists(outfile):
        logging.debug('writing spans to outfile %s ', outfile)
        with open(outfile, "w") as of:
            text_line = "const text = "+ text
            of.write("%s\n" % text_line)
            span_line = str(spans).replace('(','{')
            span_line = span_line.replace(')','}')
            span_line = "const spans = "+ span_line 
            of.write("%s\n" % span_line)
            ent_line = "const ents = " + str(entity_list)
            of.write("%s\n" % ent_line)

    print(">> Wrote span info to output file ", outfile)

    

