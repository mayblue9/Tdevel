###############################################################################
University of Turku BioNLP'09 Event Detection Software

Preliminary Release

December 2009
###############################################################################

Index
1. Introduction
2. Related Publications
3. Overview of the Software
4. How to Use It
5. Interaction XML
6. License

# 1. Introduction #############################################################

This software package contains the system designed to detect biomedical events as defined in the BioNLP'09 Shared Task. It combines machine learning and rule based systems, using Joachims SVM-Multiclass for the machine learning components.

This preliminary release contains software required for detecting events as defined in the tasks 1 & 2 of the shared task, starting from textual data in the interaction XML (see section 5) format. Software for task 3 will be included in the final release.

This preliminary release is both badly documented, potentially buggy and quite possibly extremely annoying to use. Please bear with us, the final release will be made ASAP in January 2010 :-)

# 2. Related Publications #####################################################

This software release covers the following publications:

Björne, Jari and Ginter, Filip and Heimonen, Juho and Pyysalo, Sampo and Salakoski, Tapio: Learning to Extract Biological Event and Relation Graphs. Proceedings of NODALIDA'09. 2009

Björne, Jari and Heimonen, Juho and Ginter, Filip and Airola, Antti and Pahikkala, Tapio and Salakoski, Tapio: Extracting Complex Biological Events with Rich Graph-Based Feature Sets. Proceedings of the BioNLP'09 Shared Task on Event Extraction. 2009, pp. 10-18

Björne, Jari and Heimonen, Juho and Ginter, Filip and Airola, Antti and Pahikkala, Tapio and Salakoski, Tapio: Extracting Contextualized Complex Biological Events with Rich Graph-Based Feature Sets. Journal of Computational Intelligence. (Under review)

# 3. Overview of the Software #################################################

The main idea behind the software architecture of this system is to separate and abstract the machine learning away from the actual textual data. In this, the system follows traditional machine learning approaches where all kinds of data are handled through a generic feature vector representation. The learning component is a thin wrapper around the SVM-multiclass, and can be replaced with other learning systems. All the components should be independent, so different components can be mixed to perform different experiments.

The overall structure of the system goes like this (<>=process, []=data, V=arrow. Hooray for ASCII art!).

Fig 1: Classifying with the system

	[Interaction-XML with parses and named entities]
	       V
	<Trigger example generation>
	       V
	<Trigger example classification (SVM-multiclass)>
	       V
	<Insertion of predicted triggers into Interaction XML>
	       V
	[Interaction-XML with parses, named entities and triggers]
	       V
	<Edge (Event argument) example generation>
	       V
	<Edge example classification (SVM-multiclass)>
	       V
	<Insertion of predicted edges into Interaction XML>
	       V
	[Interaction-XML with parses, named entities, triggers and edges]
	       V
	<Post-processing (trigger node duplication etc.)>
	       V
        <Conversion to BioNLP'09 Shared Task format (a2 files)>
	       V
	[Predicted events in shared task format]
	       V
	<Evaluation with BioNLP'09 Shared Task tools>

Figure 1 shows how to get classifications with the pre-trained models. If anything in the input files changes, you will need to retrain the system. There are programs for this and the basic idea is to use known training data to generate training examples and then train the SVM-multiclass on these.

You will probably want to change the input files, e.g. use your own parses. The process for making the Interaction XML from the Shared task data is like this:

Fig 2: Preparing the data

	[Shared Task Data]
	       V
	<Charniak-McClosky Parser>
	       V
	<Johnson Reranker>
	       V
	<Stanford Conversion>
	       V
	<Interaction XML generation (including head token detection)>
	       V
	[Parsed Shared task data in interaction XML format]

This is quite an involved process, so to make things easier we have provided the Shared Task data already in the interaction XML format. It should be quite simple to insert e.g. your own parses into this format. The original data preparation tools will be released in the official software release.

# 4. How to Use It ############################################################

4.1 Required Software & Hardware

The main requirement of the software is Python, at least versions 2.4 and 2.5 are known to work. Additionally, if you want to use the BioNLP'09 official evaluation tools, you will need to have perl installed, and have it in the PATH and callable with the command "perl".

For additional settings, there is a settings file located in src/Settings.py. You probably only need to modify it if you want to retrain the system, in which case you need Joachims SVM-multiclass. Download it from http://svmlight.joachims.org/svm_multiclass.html and compile with a C compiler. You will now have two binaries, "svm_multiclass_learn" and "svm_multiclass_classify". In src/Settings.py set the variable SVMMultiClassDir to point to the directory containing the binaries.

All the included xml-files contain information for all three subtasks of the BioNLP'09 Shared Task. All the model files are trained for joint prediction of tasks 1 & 2. Results for the primary task 1 can be obtained by giving the correct task parameter for the relevant pipeline.

Classification of the Shared Task dataset can take more than 1 Gb of memory, but the system should run fine on a machine with at least 2 Gb.

4.2 Running the System

The system is controlled by writing "pipeline files", which are simply Python scripts that call functions defined in the public interface of the event detection system. These functions usually pass the same data forward, each performing some step in the experiment. There are multiple pre-made pipelines in the package, and these should cover the most common use cases of the software. These are located in src/Classifiers/. To run a pipeline, simply call it with python "python name.py". For the provided pipelines, you can also pass command line parameters. To see a list of available options, call the program with the option "--help".

4.2 Quick Start (test basic classification)

1) Create an empty directory for the program output, e.g. /OUTPUT.

2) Go to directory src/Pipelines.

3) Execute the command "python BioNLP09Classify.py -o /OUTPUT". The program will perform event detection on the BioNLP'09 Shared Task devel-set, using pre-defined learned information from the Shared Task train set.

4) The program will print progress information on screen. If you haven't set up SVM-multiclass, classification will work but will be very slow.

5) Final results will show on screen using the official shared task evaluation script. The output directory will contain a "geniaformat" subdirectory with the predicted ".a2" files.

4.3 Classifying with Pre-trained Models

For using the pre-trained models for classification, use src/Pipelines/BioNLP09Classify.py. The program has many parameters, but the simplest test run takes just one, "-o" for the output directory which will be created if it doesn't exist. Running like this will classify the BioNLP'09 Shared Task devel set, for which you get the full set of available evaluations, including the official shared task evaluation, as described in section 4.2.

Classification will work even without SVM-multiclass, but is extremely slow (slightly faster if you have numpy installed). See section 4.1 for instructions on how to download and configure SVM-multiclass.

If you have made your own input interaction xml file (such as a new corpus or something), and just want to classify it with our models, use the "-i" parameter to define that file. You can also use "-t" and "-p" to define a tokenization and parse, but remember that the system is using models trained on our parses, so if yours differ too much, performance will suffer.

If you have re-trained the system (see 4.4), you can use "-m" and "-n" to point to the model files, and "-r" to define your optimal recall adjuster parameter.

4.3.1 Important note on feature and class ids

If you have modifier the provided training files, or are using some other data for training, the examples generated from it may contain new features. The support vector machine has no knowledge of the feature and class names, and instead uses integer ids to represent them. When given something to classify, it will match classes and features based on these ids. Therefore it is extremely important that the ids are consistent between training and classification.

When re-training the system, new id files are created in the output directory. These are of the format STEM.class_names and STEM.feature_names. When using your new models (with the "-m" and "-n" switches), remember to also use the matching id sets with the "-v" and "-w" parameters.

4.4 Re-training the system

If you modify the training data (such as using a new parse) or use a new dataset, you must retrain the system. For retraining, use src/Pipelines/BioNLP09Train.py. The re-training proceeds in two steps. First, one SVM model is created for each trigger and edge c-parameter to be tested. Then, using these models, triplets of trigger c-parameter, edge c-parameter and recall booster parameter are tested in the three-dimensional search space to determine the optimal parameter combination. The program will print evaluation results for all combinations on screen. This output is also stored for later use in a file called log.txt in the output directory.

The program has several options. Options "-e" and "-r" are used to to define your training and testing files. The SVM uses training data to learn its classification principles, and testing data for determining the optimal regularization parameter c. Both files are in Interaction XML format, more information on which can be found in section 5.

Output directory "-o" will be created if it doesn't exist. If you have created new parse and tokenization elements in the interaction xml files, they can be used with the "-p" and "-t" options. Id sets ("-v" and "-w") should use the default values, so most features will be consistent with the pre-defined models.

The three parameters to optimize can be defined with options "-x" (trigger detector c-parameter), "-y (recall booster parameter)" and "-z" (edge detector c-parameter). All of these take as input a comma separated list of numbers, integers in the case of "-x" and "-z" and floats for "-y". Determining good parameter ranges for optimization is somewhat a case of trial and error, but the provided default values should be good for most situations. The SVM regularization parameters, or c-parameters, can be almost anything, but for this system usually exist in the range of 10000 - 1000000. 

The recall booster parameter is used to multiply the SVM's prediction strength for the negative class for each trigger. Therefore, recall booster parameters <1 cause more potential triggers to be classified as actual triggers and increase the recall. Parameters >1 reduce the number of triggers and increase precision.

When re-training the system, two things must be kept in mind when looking for the optimal parameter combination. First, the three-dimensional search grid must be dense enough. Second, if an optimal parameter triplet is discovered on the edge of the grid, it is possible that even better values are left outside the search space, and increasing the grid in the direction of the parameter(s) on the edge is recommended.

4.5 Writing Your Own Pipelines

The file src/Pipelines/Pipeline.py defines the public interface of the event detector. Following the example of the two pipelines introduced above, you can also write your own to make more complicated, new experiments.

# 5. Interaction XML ##########################################################

5.1 Corpus Files

Interaction XML is the graph format used for representing the Shared Task data. It is semantically equal to the shared task format, but when training for event detection, it is compressed into a "flat/merged" format (See the BioNLP'09 publication). The corpus files provided in this package are already in the flat format. The files are:

/data/devel123.xml: Shared Task devel set with information for all three tasks
/data/train123.xml: Shared Task train set with information for all three tasks
/data/everything123.xml: combination of the devel and train sets, used for training when classifying the test set
/data/test.xml: Shared Task test set, no annotation available. The Shared Task organizers provide an online evaluation system at http://www-tsujii.is.s.u-tokyo.ac.jp/GENIA/SharedTask/eval-test.shtml

In the final release we will include the conversion programs required for creating these interaction xml files from parses and the shared task data. However, for most applications, the interaction xml files provide the best starting point. For example, if you want to use a new parse, just insert it into the interaction xml files, and it can be immediately used with the event detection system.

5.2 Format

The interaction xml is an xml format describing sentences, their semantic content and optionally (sometimes) automated analyses such as parses. It was originally developed as a shared format for unifying a number of binary interaction corpora (http://mars.cs.utu.fi/PPICorpora/), but can be used as is for representing also event-type complex interactions. It is extendible, and new elements and attributes can be defined as long as their names don't overlap with existing ones. Here is an example of the format, with one instance of all elements:

<corpus source="GENIA">
  <document id="GENIA.d0">
    <sentence charOffset="0-168" id="GENIA.d0.s0" origId="10089566.s0" text="Involvement of adenylate cyclase and p70(S6)-kinase activation in IL-10 up-regulation in human monocytes by gp41 envelope protein of human immunodeficiency virus type 1.">
      <entity charOffset="37-50" headOffset="37-39" id="GENIA.d0.s0.e0" isName="True" negation="False" origId="10089566.T1" speculation="False" text="p70(S6)-kinase" type="Protein" />
      <interaction directed="True" e1="GENIA.d0.s0.e1" e2="GENIA.d0.s0.e4" id="GENIA.d0.s0.i0" origId="10089566.E1.0" type="Theme" />
      <sentenceanalyses>
        <tokenizations>
          <tokenization tokenizer="McClosky">
            <token POS="NN" charOffset="0-10" id="clt_1" text="Involvement" />
 	</tokenizations>
        <parses>
          <parse parser="McClosky" tokenizer="McClosky">
            <dependency id="clp_1" t1="clt_4" t2="clt_3" type="nn" />
	  </parse>
	</parses>
      </sentenceanalyses>
    </sentence>
  </document>
</corpus>

The format defines a corpus, that contains sentences grouped into documents. In the case of GENIA, these documents represent article abstracts. For each sentence, a number of entities and interactions are defined. The entities represent the named entities and triggers of the events, the interactions their arguments (Theme/Cause etc.). The entities and interactions define the semantic network (see BioNLP'09 article).

Character offsets are defined in the Offset-attributes, all offsets are zero based (e.g. the offset of "A" in the beginning of the sentence would be "0-0"). Entity offsets are relative to the sentence, sentence's offset is relative to the document. The sentence's origId attribute defines its GENIA/PubMed identifier.

Entities represent both the named entities and trigger words of the events. The "isName" attribute must be "True" for named entities, "False" for triggers. Attributes "speculation" and "negation" are specific for task 3 of the Shared Task. The "headOffset" attribute defines the syntactic head of the entity. This is always based on a specific parse, see 5.3.

Interactions are the edges of the semantic network, and correspond to event arguments. They are directed from entity one (e1) to entity two (e2). The directed attribute is optional, if present it must be "True" for event detection.

The optional sentenceanalyses-element contains the parses. All parses consist of a tokenization/parse pair. Tokens should be listed in the order they appear in the sentence, and their ids must be of the format NAME_x, where NAME is any string and x is a number in the range [1,n]. Dependencies don't require ids, but if they are used, they must be unique. The parses are identified with the "parser" and "tokenizer" attributes. Most of the event detector components allow also giving only the parse name as input, and for this reaseon each parse must have a tokenizer-attribute defining the corresponding tokenization.

The format uses mostly hierarchical ids. These are the ids of documents (NAME.d0), sentences (NAME.d0.s0), entities (NAME.d0.s0.e0) and interactions (NAME.d0.s0.i0). Their numbering starts from 0 and for each element its corresponding number must be unique. For fixing or updating these numbers, the Pipeline command ix.recalculateIds can be used. This can also be done with the program at src/CommonUtils/InteractionXML/RecalculateIds.py.

5.3 Notes on Editing the Corpus Files

To perform your own experiments, you will need to modify the interaction xml files provided in this package. A single interaction xml can have multiple parse and tokenization elements, as long as they have different "parser" and "tokenizer" attributes.

Remember to keep the hierarchical ids valid, and use src/CommonUtils/InteractionXML/RecalculateIds.py to fix them if in doubt.

For event detection, all entities are mapped to the parse through a single head token (see BioNLP'09 article). This is defined as the "headOffset" attribute of the entity. When you want to use a different parse, these offsets must be recalculated. For this, use the program src/Utils/FindHeads.py. The program takes as input (-i) an interaction xml file, gives all entities in it a headOffset based on parse (-p) and tokenization (-t), and writes the resulting xml into output (-o).

Having parse specific head offsets in the otherwise parse-independent entity-elements is a bit clumsy, so in future versions entity head offsets will probably be defined as part of the tokenization. But for now, ALWAYS remember to recalculated head offsets before using the system with a different parse and tokenization.

# 5. License ##########################################################

The program will be distributed under an open source license. Final license terms will be determined in time for the official release. This package contains also several external libraries and data, their licenses are as defined by their respective owners. Generally, everything here is free for non-commercial scientific use.