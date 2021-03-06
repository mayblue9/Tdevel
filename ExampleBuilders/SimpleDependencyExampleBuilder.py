import sys
sys.path.append("..")
from Core.ExampleBuilder import ExampleBuilder

# The first example builder written, used in the first tests
# between July 8th and 11th 2008.
# Builds very simle examples, but SVMLightClassifier gives:
# Parameters: {'c': 50.0}
# p/n:908/5118 tp/fp|tn/fn:899/937|4181/9 p/r/f:0.4896/0.9900/0.6552

class SimpleDependencyExampleBuilder(ExampleBuilder):
        
    def buildExamples(self, sentenceGraph):
        examples = []
        exampleIndex = 0
        for i in range(len(sentenceGraph.tokens)-1):
            for j in range(i+1,len(sentenceGraph.tokens)):
                t1 = sentenceGraph.tokens[i]
                t2 = sentenceGraph.tokens[j]
                hasDep = sentenceGraph.dependencyGraph.has_edge(t1, t2) or sentenceGraph.dependencyGraph.has_edge(t2, t1)
                hasInt = sentenceGraph.interactionGraph.has_edge(t1, t2) or sentenceGraph.interactionGraph.has_edge(t2, t1)
                if hasDep or hasInt:
                    if hasDep and hasInt:
                        category = 1
                    elif hasDep and not hasInt:
                        category = -1
                    if hasDep:
                        features = self.buildFeatures(t1,t2,sentenceGraph)
                        extra = {"type":"edge","t1":t1,"t2":t2}
                        examples.append( (sentenceGraph.getSentenceId()+".x"+str(exampleIndex),category,features,extra) )
                        exampleIndex += 1
        return examples

    def buildFeatures(self, token1, token2, sentenceGraph):
        features = {}
        features[self.featureSet.getId("terminus_text_"+sentenceGraph.getTokenText(token1))] = 1
        features[self.featureSet.getId("terminus_POS_"+token1.attrib["POS"])] = 1
        features[self.featureSet.getId("terminus_text_"+sentenceGraph.getTokenText(token2))] = 1
        features[self.featureSet.getId("terminus_POS_"+token2.attrib["POS"])] = 1
        return features
