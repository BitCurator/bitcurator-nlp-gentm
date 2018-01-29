#!/usr/bin/python
# coding=UTF-8
#
# BitCurator NLP (Disk Image Access for the Web)
# Copyright (C) 2014 - 2016
# All rights reserved.
#
# This code is distributed under the terms of the GNU General Public
# License, Version 3. See the text file "COPYING" for further details
# about the terms of this license.
#
# This file contains the main BitCurator NLP application for 3D plot.

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
import spacy
#import spacy.en
#from spacy.en import English
import textract

dict_ent = {}
dict_time = {}
dict_org = {}
dict_person = {}
dict_gpe = {}
dict_event = {}
dict_date = {}
dict_languages = {}
dict_facility = {}
dict_work_of_art = {}
dict_norp = {}
dict_loc = {}

def get_dict(ent_type):
    if ent_type == 'time':
        return "time", dict_time
    elif ent_type == 'org':
        return "org", dict_org
    elif ent_type == 'person':
        return "person", dict_person
    elif ent_type == 'gpe':
        return "gpe", dict_gpe
    elif ent_type == 'date':
        return "date", dict_date
    elif ent_type == 'languages':
        return "languages", dict_languages
    elif ent_type == 'facility':
        return "facility", dict_facility
    elif ent_type == 'work_of_art':
        return "work_of_art", dict_work_of_art
    elif ent_type == 'norp':
        return 'norp', dict_norp
    elif ent_type == 'loc':
        return "loc", dict_loc
    else:
        return None, None


from bn_filextract import *

from configobj import ConfigObj
# Dict to number of partitions in each image
partition_in = dict()
config_file = "bntm_config.txt" # FIXME: Remove the globalization
logging.basicConfig(filename= 'bcnlp.log', level=logging.DEBUG)

img_list = []
doc_list = []
entities_list = []

class ParseForEnts():
    """ Parses the given file(s) into entities and generates the span
        Input: text, entity_list
        Output: Span file(s)
        entity_list can be configured in the file bcnlp_config.txt.
    """
    def __init__(self):
        self.spans = []
        fig = plt.figure()
        self.ax = fig.add_subplot(111, projection='3d')
        self.ax.set_xlabel('Image')
        self.ax.set_ylabel('Document')
        self.ax.set_zlabel('Entity')

    def getIdsForPlot(self, img, doc, entity):
        if img not in img_list:
            logging.info("Appending img to img_list : %s", img)
            img_list.append(img)
        # return the key as it already exists
        img_id = img_list.index(img)
        
        #logging.info("[V]ParseForEnts: getIdsForPlot: doc_list: %s ", doc_list)
        if doc not in doc_list:
            logging.info("Appending DOC to doc_list : %s", doc)
            doc_list.append(doc)
        else:
            logging.info("Doc %s already exists ",doc)

        # return the key as it already exists
        doc_id = doc_list.index(doc)
  
        if entity not in entities_list:
            entities_list.append(entity)
        # return the key as it already exists
        entity_id = entities_list.index(entity)

        logging.info("getIdsForPlot:ret img_id %d doc_id %d entity_id: %d ",\
                      img_id, doc_id, entity_id)
  
        return img_id, doc_id, entity_id

    def tagEnts(self, text, entity_list, nlp, img, doc):
        self.spacy_doc = nlp(text)
        logging.info("Spacy_doc Entities: \n")

        '''
        for ent in self.spacy_doc.ents:
            logging.info("%s, %s, %s", ent.text, ent.label, ent.label_)
        '''

        for j in entity_list:
            dict_ent[j] = 0

        logging.info("tagEnts: Entity list: %s", entity_list)
        for word in self.spacy_doc[:-1]:
            #logging.info("[V]Word: %s ent_type: %s ", \
                              #word, str(word.ent_type_))

            start = word.i
            end = word.i + 1
            while end < len(self.spacy_doc) and self.spacy_doc[end].is_punct:
                end += 1
            self.span = self.spacy_doc[start : end]
            if word.ent_type_ in entity_list or \
                       (word.ent_type_).lower() in entity_list:
                #logging.info("tagEnts:Img:%s Doc:%s Entity: %s ent_type:%s ", \
                                  #img, doc, word, word.ent_type_)

                x, y, z = self.getIdsForPlot(img, doc, word)
                self.plot3d(x, y, z)
                logging.info("[D]tagEnts: ent_type %s is in entity_list ", \
                      word.ent_type_)
                end_char = "end: "+str(self.span.end_char)
                start_char = "start: "+str(self.span.start_char)
                ent_type = "type: "+word.ent_type_
                self.spans.append((end_char, start_char, ent_type))
                logging.debug("[D]tagEnts: Appended %s, New SPANS: %s ", \
                       word, self.spans)

                # For generating histogram, a new dictionary is created for
                # each entity. First time the value is initialized to 1.
                # It is appended for subsequent words
                edict_name, edict = get_dict(word.ent_type_.lower())

                if edict != None:
                    if str(word) in edict:
                        edict[str(word)] += 1
                    else:
                        edict[str(word)] = 1

                dict_ent[str(word.ent_type_.lower())] += 1

            '''
            # Note: This is commented out to reduce noice in the log file.
            else:
                logging.debug("ent_type %s for word %s is NOT in entity_list", 
                        word.ent_type_, word)
            '''

        return self.spans, dict_ent
    def plot3d(self, x, y, z):
        self.ax.scatter(x, y, z, c='r', marker='.')
        

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

    def bnParseConfigFileForEnts(self, filename):
        """ Parses the configuration file plot_config.txt to 
            extract FIXME
        """
        config = ConfigObj(filename)
        entity_list_section = config['entity_list_section']
        cfg_entity_list = []
        for key in entity_list_section:
            #logging.debug("Cfg: Key: %s %s ", key, entity_list_section[key])
            flag = int(entity_list_section[key])
            if flag == 1:
                #logging.debug("Cfg: bnParseConfigFile: Appending key  %s: ", key)
                cfg_entity_list.append(key)
        return cfg_entity_list

    def bcnlpProcessDir(self, infile, bg):
        """ Recursively calls itself till it finds a file which is not a 
            directory, to process the file contents.
        """
        for f in os.listdir(infile):
            f_path = infile + '/' + f
            print "\n>> Processing file ", f_path
            logging.debug("bcnlpProcessDir: Processing file %s ",f_path)
            if os.path.isdir(f_path):
                self.bcnlpProcessDir(f_path, bg)
            else:
                # It is a file
                logging.debug(">>>> Processing single file %s ", f_path)
                self.bcnlpProcessSingleFile(f_path, bg)
    
    
    def bcnlpProcessText(self, img, doc, text, entity_list, parse_en, bg=False):
        logging.info("ProcessText: img: %s doc: %s",img, doc)
        spans, dict_ents = self.tagEnts(text, entity_list, parse_en, img, doc)
        #logging.debug("const ents = %s", entity_list)
        

    def bcnlpProcessSingleFile(self, infile, bg = False):
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
        spans, dict_ents = self.tagEnts(text, entity_list, img=None, doc=None)
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
        print ">> Wrote span info to output file ", outfile

cfg_image = {}
def bn_parse_config_file(config_file, section_name):
    print "bn_parse_config_file: Section: ", section_name, config_file 
    config = ConfigObj(config_file)
    section = config[section_name]
    i = 0
    cfg_entity_list = []
    for key in section:
        #if key == cfg_string:
            # found the string
            #return section[key]
        print "key: ", key
        if section_name == "image_section":
            print (key, section[key])
            cfg_image[i] = key
            i+=1
        elif section_name == "entity_list_section":
            flag = int(entity_list_section[key])
            if flag == 1:
                cfg_entity_list.append(key)
    if section_name == "entity_list_section":
        return cfg_entity_list
    #print "IMAGES: ", cfg_image
        

if __name__ == "__main__":

    #parse_en = English()
    nlp = spacy.load('en')
    config_file = "bntm_config.txt"
    #bn_parse_config_file(config_file)
    bn_parse_config_file(config_file, "image_section")
    #bn = bn_filextract.bcnlp()
    bn = BnFilextract()

    # for each image extract the files and convert the convertable
    # formats to text format
    i = 0 # image index
    ent = ParseForEnts()

    # Find the excluded formats from config file.
    bn.exc_fmt_list = bn.bnGetExFmtsFromConfigFile(config_file)
    print("Excluded formats in config file: ", bn.exc_fmt_list)
    
    for img in cfg_image:
        print "Extracting files from image ", cfg_image[img]
        bn.bnExtractFiles(ent, cfg_image[img], i, nlp, config_file)
        i += 1

    #entity_list = ent.bnParseConfigFileForEnts("bn_config.txt")
    # Now traverse the directory and generate entities, etc.
    file_extract_dir = bn.bnGetConfigInfo(config_file, \
                         "confset_section", "file_staging_directory")

    i = 0
    for img in cfg_image:
        new_file_extract_dir = os.path.join(file_extract_dir, str(i))
        bn.bnTraverseDirForPlot(img, new_file_extract_dir, \
                                       ent, nlp, config_file)
        i += 1

    print(">> Plotting the results ")

    plt.show()

    '''
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    xs = 
    ys = 
    zz = randrange(n, 0, 100)
    '''
  

