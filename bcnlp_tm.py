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
# This file contains the main BitCurator NLP application for Topic modeling

# Usage: python bcnlp_tm.py [--topics <10>] [--tm <gensim|graphlab>]
# Default num_topics = 10, tm=graphlab

import os
import logging
import pyLDAvis
import pyLDAvis.gensim
from gensim import corpora, models, similarities
import gensim
import textract
from bn_filextract import *
from configobj import ConfigObj
from stop_words import get_stop_words

try:
    from argparse import ArgumentParser
except ImportError:
    raise ImportError("This script requires ArgumentParser which is in Python 2.7 or Python 3.0")

#logging.basicConfig(filename= 'bcnlp_tm.log', level=logging.DEBUG)
logging.basicConfig(filename= 'bcnlp_tm_info.log', level=logging.INFO)
logging.basicConfig(filename= 'bcnlp_tm_debug.log', level=logging.DEBUG)
logging.basicConfig(filename= 'bcnlp_tm_warning.log', level=logging.WARNING)


cfg_image = {}
#documents = []

class BnTopicModel():

    def tm_generate_gensim(self, infile, num_topics, config_file):
        ''' Using the APIs provided by gensim, LDAvis gui is invoked. 
            NOTE: This is not yet tested well.
        '''
        documents = []
        documents = bn.bnTraverseInfileDir(infile, documents, config_file)
        if documents == []:
            print("Documents are empty")

        # remove common words and tokenize
        '''
        stoplist = set('a an the of to for s from is and this \
                         was were are , - | @ . '.split())
        texts = [[word for word in document.lower().split() \
                             if word not in stoplist] \
                              for document in documents]
        '''

        en_stop = get_stop_words('en')
        logging.info("Stop-words list: %s ", en_stop)
        texts = [[word for word in document.lower().split() \
                 if word not in en_stop] \
                   for document in documents]


        # remove words that appear only once
        from collections import defaultdict
        frequency = defaultdict(int)
        for text in texts:
            i = 0
            for word in text:
                # NOTE:  Some text files need this conversion. See if this can
                # be done for the whole document at one time.
                text[i] = unicode(word, errors='ignore')
                i+=1
            for token in text:
                frequency[token] += 1
    
        texts = [[token for token in text if frequency[token] > 1]
             for text in texts]

        texts = [[token for token in text if len(token) > 2]
             for text in texts]

        # NOTE: lemmatize not working
        ###texts = gensim.utils.lemmatize(texts)

        dictionary = corpora.Dictionary(texts)

        ##logging.info("[V]: token:id: %s", dictionary.token2id)

        ## dictionary.compactify()
        dictionary.save('/tmp/saved_dict.dict')
    
        # Now convert tokenized documents to vectors:
        corpus = [dictionary.doc2bow(text) for text in texts]

        ## logging.info("[V] Corpus: %s ", corpus)

        # store to disk, for later use
        corpora.MmCorpus.serialize('/tmp/saved_dict.mm', corpus)

        ## Creating Transformations
        ## The transformations are standard Python objects, typically 
        ## initialized (trained) by means of a training corpus:
        ## First, let's use tfidf for training: It just involves simply 
        ## going thru the supplied corpus once and computing document 
        ## frequencies of all its featuers.  
    
        tfidf = models.TfidfModel(corpus) # step 1 -- initialize a model
        
        corpus_tfidf = tfidf[corpus]
        corpora.MmCorpus.serialize('/tmp/saved_corpus_tfidf.mm', corpus_tfidf)

        ''' 
        # LSI model is commented out for now
        print "Printing TFIDF of given corpus \n"
        for doc in corpus_tfidf:
            print (doc)
    
        # Now Initialize an LSI transformation: num_topics set to 2 to make 
        # it 2D lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, 
        # num_topics=3)
    
        # create a double wrapper over the original corpus: 
        # bow->tfidf->fold-in-lsi
        corpus_lsi = lsi[corpus_tfidf]
    
        print "Printing LSI topics"
        lsi.print_topics(4)
    
        for doc in corpus_lsi:
            print (doc)
        '''
        
        # Create an LDA model
        '''
        lda_model = models.LdaModel(corpus_tfidf, \
                                    id2word=dictionary, \
                                    num_topics=5)
        '''
        lda_model = models.ldamodel.LdaModel(corpus=corpus, \
                                    id2word=dictionary, \
                                    num_topics=num_topics)
        corpus_lda = lda_model[corpus]
    
        corpus_lda_tfidf = lda_model[corpus_tfidf]
        
        # The following will print the topics in the logfile
        logging.info("Printing %s topics into log file: ", str(num_topics))
        lda_model.print_topics(num_topics)
    
        # Generate data for the pyLDAvis interface from the lda_model above
        vis_data = pyLDAvis.gensim.prepare(lda_model, corpus, dictionary)
        ##vis_data = pyLDAvis.gensim.prepare(lda_model, corpus_lda, dictionary)

        #pyLDAvis.display(vis_data)
        pyLDAvis.show(vis_data)

    def remove_punctuation(self, text):
        import string
        return text.translate(None, string.punctuation)

    def remove_digits(self, text):
        import string
        return text.translate(None, string.digits)

    def bnRemoveEmptyFiles(self, path):
        ''' Traverses the directory and recursively removes empty files.
        '''
        files = os.listdir(path)
        if len(files):
            for fl in files:
                fullpath = os.path.join(path, fl)
                if os.path.isdir(fullpath):
                    self.bnRemoveEmptyFiles(fullpath)
                if os.stat(fullpath).st_size == 0:
                    logging.info("Removing file %s ", fullpath)
                    os.remove(fullpath)

def bn_parse_config_file(config_file, section_name):
    ''' Parses the config file to extract the image names and entity list.
    '''
    logging.info("bn_parse_config_file: Section: %s ", section_name)
    config = ConfigObj(config_file)
    section = config[section_name]
    i = 0
    cfg_entity_list = []
    for key in section:
        #if key == cfg_string:
            # found the string
            #return section[key]
        if section_name == "image_section":
            logging.info("parse_config: key: %s, section: %s", \
                            key, section[key])
            cfg_image[i] = key
            i+=1
        elif section_name == "entity_list_section":
            flag = int(entity_list_section[key])
            if flag == 1:
                cfg_entity_list.append(key)
    if section_name == "entity_list_section":
        return cfg_entity_list

if __name__ == "__main__":
    parser = ArgumentParser(prog='bcnlp_tm.py', description='Topic modeling')
    parser.add_argument('--config', action='store', \
                                  help="Config file[bntm_config.txt] ")
    parser.add_argument('--infile', action='store', help="input directory ")
    parser.add_argument('--tm', action='store',  \
                         help="topic modeling :gensim/graphlab ")
    parser.add_argument('--topics', action='store', help="number of topics ")

    args = parser.parse_args()

    # Infile specifies the directory of files to run the topic modeling on.
    # If no argument specified, it will assume there are disk-images specified
    # in the config file bntm_config.txt.

    infile = args.infile
    tm = args.tm  # Topic modeling type: gensim/graphlab
    config_file = args.config
    is_disk_image = False

    num_topics = 10
    if args.topics:
        num_topics = args.topics

    # default it to gensim
    if tm == None:
        tm = 'gensim'

    if config_file == None:
        config_file = "bntm_config.txt"

    bn = BnFilextract()
    if infile == None:
        is_disk_image = True

        bn_parse_config_file(config_file, "image_section")
        print(">> Images in the config file: ", cfg_image)

        infile = bn.bnGetConfigInfo(config_file, \
                         "confset_section", "file_staging_directory")

        i = 0
        for img in cfg_image:
            print(">> Extracting files from image {}...".format(cfg_image[img]))
            bn.bnExtractFiles(None, cfg_image[img], i, None, config_file)
            i += 1
        print(">> ... Done ")

    else:
        documents = []
        print(">> Extracting files from ", infile)
        bn.bnTraverseInfileDir(infile, documents, config_file)

    tmc = BnTopicModel()
    tmc.tm_generate_gensim(infile, num_topics, config_file)


