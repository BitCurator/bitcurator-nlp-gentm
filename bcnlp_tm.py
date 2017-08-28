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
import pyLDAvis.graphlab
import graphlab as gl
from gensim import corpora, models, similarities
import textract
from bn_filextract import *
from configobj import ConfigObj

try:
    from argparse import ArgumentParser
except ImportError:
    raise ImportError("This script requires ArgumentParser which is in Python 2.7 or Python 3.0")

logging.basicConfig(filename= 'bcnlp_tm.log', level=logging.DEBUG)


cfg_image = {}
documents = []

class BnTopicModel():

    def tm_generate_gensim(self, infile):
        ''' Using the APIs provided by gensim, LDAvis gui is invoked. 
            NOTE: This is not yet tested well.
        '''
        # remove common words and tokenize
        stoplist = set('for a of the and to in'.split())
        texts = [[word for word in document.lower().split() if word not in stoplist]
            for document in documents]
        
        # remove words that appear only once
        from collections import defaultdict
        frequency = defaultdict(int)
        for text in texts:
            for token in text:
                frequency[token] += 1
    
        texts = [[token for token in text if frequency[token] > 1]
             for text in texts]
    
        dictionary = corpora.Dictionary(texts)
        ## dictionary.compactify()
        dictionary.save('/tmp/saved_dict.dict')
    
        # Now actually convert tokenized documents to vectors:
        corpus = [dictionary.doc2bow(text) for text in texts]

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
        lda_model = models.LdaModel(corpus_tfidf, \
                                    id2word=dictionary, \
                                    num_topics=5)
        corpus_lda = lda_model[corpus]
    
        corpus_lda_tfidf = lda_model[corpus_tfidf]
        
        ## lda_model.print_topics(5)
    
        #vis_data = pyLDAvis.gensim.prepare(lda_model, corpus, dictionary)
        vis_data = pyLDAvis.gensim.prepare(lda_model, corpus_lda, dictionary)

        #pyLDAvis.display(vis_data)
        pyLDAvis.show(vis_data)
    
    def tm_generate_graphlab(self, indir, num_topics):
        ''' Generate the LDA model for documents in indir, using graphlab
        '''
        print(">> Graphlab: Creating SArray")
        sa = self.bnGenerateSArray(indir)

        sa_docs = gl.text_analytics.count_words(sa)
        sa_docs_nsw = sa_docs.dict_trim_by_keys(gl.text_analytics.stopwords(), \
                                                True)

        print(">> Graphlab: Creating topic model with {} topics: ".\
                                        format(num_topics))
        topic_model = gl.topic_model.create(sa_docs_nsw, \
                      num_topics=int(num_topics), num_iterations=100)

        print("Graphlab: Preparing data: ")
        vis_data = pyLDAvis.graphlab.prepare(topic_model, sa_docs_nsw)

        print("Graphlab: Launching graphics ")
        pyLDAvis.show(vis_data)

    def bnGenerateSArray(self, filextract_dir):
        ''' Traverse through the files in a directory and create sArrays 
            and append them into one single sArray.
        '''
        num_docs = 0
        sa_g = gl.SArray(dtype = str)
        sw_list = ['a', 'an', 'the', 'of', 'to', 'for','as', 'from', 'is', \
                         'was', 'were', 'are', ',', '-', '|', '@', '.' ]
        for root, dirs, files in os.walk(filextract_dir):
            path = root.split(os.sep)
            '''
            print "path: ", path, len(path)
            print "dirs: ", dirs
            print "files: ", files
            print((len(path) - 1) * '---', os.path.basename(root))
            '''
            # if no files continue to next level
            if files == []:
                continue
            for filename in files:
                print(len(path) * '---', filename)
                file_path = '/'.join(path) + '/' + filename

                # If filename is not a text file, convert it
                if not (filename.endswith('.txt') or filename.endswith('.TXT')):
                    '''
                    ## FIXME: The jpg check needs removed. Just for testing.
                    if not (filename.endswith('.jpg') or filename.endswith('.JPG')):
                        print("Filename {} is not a txt file. So textracting".\
                               format(filename)) 
                        input_file_contents = textract.process(file_path) 
                        #f, ext = os.path.splitext(filename)
                        #file_path = file_path + '/' + f + '.txt'
                        file_path = os.path.splitext(file_path)[0]+'.txt'
                        print ("bnGenerateSArray: writing contents to outfile: ", 
                                             file_path) 
                        with open(file_path, "w") as text_file:
                            text_file.write(input_file_contents)
                    '''
                    print("Filename {} is not a txt file. So textracting".\
                           format(filename)) 
                    input_file_contents = textract.process(file_path) 
                    file_path = os.path.splitext(file_path)[0]+'.txt'
                    print ("bnGenerateSArray: writing contents to outfile: ", 
                                         file_path) 
                    with open(file_path, "w") as text_file:
                        text_file.write(input_file_contents)

                logging.debug(">>> Getting SArray for file %s ", file_path)
                sa_sub = gl.SArray(file_path)
                gl.text_analytics.trim_rare_words(sa_sub, threshold=2, stopwords=sw_list )
                # Now append the sub-sarray to the main one.
                if num_docs == 0:
                    sa_g = sa_sub
                else:
                    sa_g = sa_g.append(sa_sub)
                num_docs += 1
    
            # print "Total num docs: ", num_docs
            return sa_g

def bn_parse_config_file(config_file, section_name):
    ''' Parses the config file to extract the image names and entity list.
    '''
    logging.debug("bn_parse_config_file: Section: %s ", section_name) 
    config = ConfigObj(config_file)
    section = config[section_name]
    i = 0
    cfg_entity_list = []
    for key in section:
        #if key == cfg_string:
            # found the string
            #return section[key]
        if section_name == "image_section":
            logging.debug("parse_config: key: %s, section: %s", \
                            key, section[key])
            cfg_image[i] = key
            i+=1
        elif section_name == "entity_list_section":
            flag = int(entity_list_section[key])
            if flag == 1:
                cfg_entity_list.append(key)
    if section_name == "entity_list_section":
        return cfg_entity_list

# FIXME: The routines that operate on files will be moved to a class 
# eventually.
def bnTraverseInfileDir(filextract_dir):
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
            # print "bnTraverseInFileDir: File Path: ", file_path
            doc = bn.bnGetFileContents(file_path)
            # print("bnTraverseInFileDir: Appending doc {} \
                                 # to documents list ".format(doc))
            documents.append(doc)
            num_docs += 1

        # print "bnTraverseInFileDir: Total num docs: ", num_docs
        
if __name__ == "__main__":
    parser = ArgumentParser(prog='bn_gensim.py', description='Topic modeling')
    parser.add_argument('--config', action='store', help="... ")
    parser.add_argument('--infile', action='store', help="... ")
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

    # default it to Graphlab
    if tm == None:
        tm = 'graphlab'

    if config_file == None:
        config_file = "bntm_config.txt"

    bn = BnFilextract()
    if infile == None:
        is_disk_image = True

        bn.exc_fmt_list = bn.bnGetExFmtsFromConfigFile(config_file)
        print("Excluded formats in config file: ", bn.exc_fmt_list)
        # No input directory specified. Look for config file for disk images

        bn_parse_config_file(config_file, "image_section")
        print(">> Images in the config file: ", cfg_image)

        i = 0
        for img in cfg_image:
            print(">> Extracting files from image {} ...".format(cfg_image[img]))
            bn.bnExtractFiles(None, cfg_image[img], i, None, config_file)
            i += 1
        print(">> ... Done ")

    else:
        print(">> Extracting files from ", infile)
        bn.bn_traverse_infile_dir(infile, documents)

    tmc = BnTopicModel()
    if tm == 'gensim':
        tmc.tm_generate_gensim(infile)
    elif tm == 'graphlab':
        if is_disk_image:
            indir = bn.bnGetOutDirFromConfig(config_file)
            print(">> Generating graphlab for images in disk image")
            logging.debug(">> Generating graphlab for images in disk image")
            logging.debug("File-extracted directory: %s ", indir)
            tmc.tm_generate_graphlab(indir, num_topics)
        else:
            print(">> Generating graphlab for files in ", infile)
            logging.debug(">> Generating graphlab for files in %s", infile)
            tmc.tm_generate_graphlab(infile, num_topics)


