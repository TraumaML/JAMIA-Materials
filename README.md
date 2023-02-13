# Introduction:

This codebase provides resources for the development of accurate machine learning models for personalized treatment of patients with psychotic and mood disorders. The goal of the study is to extract trauma-related features from electronic health records (EHRs) of psychiatric patients. The study makes several contributions including the creation of training and testing corpora of EHRs, development of an annotation scheme, establishment of a gold standard corpus, and development of an annotation guideline. The study utilizes natural language processing (NLP) tools and the Brat rapid annotation interface, an open-source NLP annotation tool, to extract trauma-related information from clinical text. The study is the first attempt to identify trauma-related features in patients with psychotic and mood disorders.

The resources developed in this study are intended for use by the psychiatric community to improve the accuracy of machine learning models for the treatment of psychotic and mood disorders.

## Preprocessing

    The preprocessing directory contains 4 files:
        -python file "preannotation.py" used to preannotate directory of text files, according to regex rules in regex lists
        -3 regex lists serve as inputs to "preannotation.py":
            -symptoms list
            -events list
            -substances list

## BRAT configuration
    
    Contains two files for configuring the annotation program BRAT according to our task specifications
        -annotation.conf
        -visual.conf

## adjudication
    
    Contains two python files:
        -"adjudication.py" takes as input a directory containing several directories pertaining to the BRAT annotations of a unique annotator
            -takes .ANN files of same name annotated by more than one annotator, and adjudicates automatically, creating a new .ANN file in adjudicated 
                subdirectory that labels conflicts as red or yellow, and accordances as green in the BRAT interface, using our BRAT config files.
        -"unattributed_annotations.py" serves as a validation tool, to ensure that annotators did not tag an entity
            and accidentally leave no attributes, as the vast majority of entities should have additional attributes.

## baseline
    Contains code for running baseline models, including hyperparameter sweep.

## data
    Contains python pickle objects of pandas dataframes, that store data referenced by scripts in baseline subdirectory.

## finetuning
    Future work for finetuning transformer models

