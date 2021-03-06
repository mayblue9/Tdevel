import sys, os, shutil
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/..")
import Evaluators.EvaluateInteractionXML as EvaluateInteractionXML
import GraphToSVG
from HtmlBuilder import *
import Graph.networkx_v10rc1 as NX10

class CorpusVisualizer:
    def __init__(self, outputDirectory, deleteDirectoryIfItExists=False):
        self.outDir = outputDirectory
        self.__makeOutputDirectory(deleteDirectoryIfItExists)
        self.builder = None
        self.sentences = []
        self.featureSet = None
        self.classSet = None
    
    def __getOrigId(self, element):
        if element.attrib.has_key("origId"):
            return element.attrib["origId"]
        elif element.attrib.has_key("seqId"):
            return element.attrib["seqId"]
        else:
            return "N/A"

    def __makeOutputDirectory(self, deleteDirectoryIfItExists):
        if os.path.exists(self.outDir):
            if deleteDirectoryIfItExists:
                print >> sys.stderr, "Output directory exists, removing", self.outDir
                shutil.rmtree(self.outDir)
            else:
                sys.exit("Error, output directory exists.")
        print >> sys.stderr, "Creating output directory", self.outDir
        os.makedirs(self.outDir)
        os.makedirs(self.outDir+"/sentences")
        os.makedirs(self.outDir+"/svg")
        jsPath = os.path.dirname(os.path.abspath(__file__))+"/../../data/visualization-js"
#IF LOCAL
        jsPath = os.path.dirname(os.path.abspath(__file__))+"/../../../PPIDependencies/Visualization/js"
#ENDIF
        shutil.copytree(jsPath,self.outDir+"/js")
    
    def getMatchingEdgeStyles(self, graph1, graph2, posColor, negColor):
        arcStyles = {}
        labelStyles = {}
        annEdges = graph1.edges()
        for annEdge in annEdges:
            if graph2.hasEdges(annEdge[0], annEdge[1]) or graph2.hasEdges(annEdge[1], annEdge[0]):
                arcStyles[annEdge] = {"stroke":posColor}
                labelStyles[annEdge] = {"fill":posColor}
            else:
                arcStyles[annEdge] = {"stroke":negColor}
                labelStyles[annEdge] = {"fill":negColor}
        return arcStyles, labelStyles
    
    def getTokenMap(self, sentenceGraph, goldGraph):
        tokenMap = {}
        for i in range(len(sentenceGraph.tokens)):
            tokenMap[sentenceGraph.tokens[i]] = goldGraph.tokens[i]
        return tokenMap
    
    def getNXEdge(self, graph, t1, t2, element):
        for edge in graph.edges(data=True):
            if edge[0] == t1 and edge[1] == t2 and edge[2]["element"] == element:
                return edge
        return None
    
    def makeExampleGraphWithGold(self, builder, sentenceGraph, goldGraph, sentenceIndex):
        exampleGraph = NX10.MultiDiGraph()
        for token in goldGraph.tokens:
            exampleGraph.add_node(token)
        arcStyles = {}
        labelStyles = {}
        extraByToken = {}
        edgeTypes = {}
        stats = {"entities":0,"edges":0,"tp":0,"fp":0,"tn":0,"fn":0}
        
        entityMap = EvaluateInteractionXML.mapEntities(sentenceGraph.entities, goldGraph.entities, goldGraph.tokens)
        tokenMap = self.getTokenMap(sentenceGraph, goldGraph)
        toEntitiesWithPredictions = set()
        for entityFrom, entitiesTo in entityMap.iteritems():
            stats["entities"] += 1
            entityFromHeadToken = sentenceGraph.entityHeadTokenByEntity[entityFrom]
            for entityTo in entitiesTo:
                toEntitiesWithPredictions.add(entityTo)
                entityToHeadToken = goldGraph.entityHeadTokenByEntity[entityTo]
                style = None
                eFromType = entityFrom.get("type")
                eToType = entityTo.get("type")
                if extraByToken.has_key(entityToHeadToken):
                    style = extraByToken[entityToHeadToken]
                if eFromType == eToType:
                    if eToType != "neg":
                        if style == None:
                            style = [entityTo.get("type"),{"fill":"green"}]
                        elif style[1]["fill"] == "#79BAEC":
                            style = [entityTo.get("type"),{"fill":"green"}]
                        if entityTo.get("isName") == "True":
                            style = [entityTo.get("type"),{"fill":"brown"}]
                        else:
                            stats["tp"] += 1
                else:
                    if eToType == "neg":
                        pass
                extraByToken[entityToHeadToken] = style
            if len(entitiesTo) == 0:
                stats["fp"] += 1
                if extraByToken.has_key(tokenMap[entityFromHeadToken]):
                    style = extraByToken[tokenMap[entityFromHeadToken]]
                    if style[1]["fill"] != "green":
                        style = [entityFrom.get("type"),{"fill":"red"}]
                    extraByToken[tokenMap[entityFromHeadToken]] = style
                else:
                    extraByToken[tokenMap[entityFromHeadToken]] = [entityFrom.get("type"),{"fill":"red"}]
        for entity in goldGraph.entities:
            if entity not in toEntitiesWithPredictions:
                stats["fn"] += 1
                extraByToken[goldGraph.entityHeadTokenByEntity[entity]] = [entity.get("type"),{"fill":"#79BAEC"}]
        
        toInteractionsWithPredictions = set()            
        for interactionFrom in sentenceGraph.interactions:
            if interactionFrom.get("type") == "neg":
                continue
            stats["edges"] += 1
            
            e1s = entityMap[sentenceGraph.entitiesById[interactionFrom.get("e1")]]
            e1Ids = []
            for e1 in e1s:
                e1Ids.append(e1.get("id"))
            e2s = entityMap[sentenceGraph.entitiesById[interactionFrom.get("e2")]]
            e2Ids = []
            for e2 in e2s:
                e2Ids.append(e2.get("id"))
                
            t1 = tokenMap[sentenceGraph.entityHeadTokenByEntity[sentenceGraph.entitiesById[interactionFrom.get("e1")]]]
            t2 = tokenMap[sentenceGraph.entityHeadTokenByEntity[sentenceGraph.entitiesById[interactionFrom.get("e2")]]]
            iFromType = interactionFrom.get("type")
            
            found = False
            for interactionTo in goldGraph.interactions:
                if interactionTo.get("e1") in e1Ids and interactionTo.get("e2") in e2Ids:
                    toInteractionsWithPredictions.add(interactionTo)
                    
                    iToType = interactionTo.get("type")
                    exampleGraph.add_edge(t1, t2, element=interactionFrom)
                    #edge = exampleGraph.get_edge(t1, t2, data=True)
                    edge = self.getNXEdge(exampleGraph, t1, t2, interactionFrom)
                    
                    if t1 != t2:
                        if iToType == iFromType:
                            edge[2]["arcStyles"] = {"stroke":"green"}
                            edge[2]["labelStyles"] = {"fill":"green"}
                            stats["tp"] += 1
                        else:
                            edge[2]["arcStyles"] = {"stroke":"red"}
                            edge[2]["labelStyles"] = {"fill":"red"}
                            stats["fp"] += 1
                    found = True
            if not found: # false positive prediction
                if t1 != t2:
                    exampleGraph.add_edge(t1, t2, element=interactionFrom)
                    edge = self.getNXEdge(exampleGraph, t1, t2, interactionFrom)
                    edge[2]["arcStyles"] = {"stroke":"red"}
                    edge[2]["labelStyles"] = {"fill":"red"}
                    stats["fp"] += 1
        for interactionTo in goldGraph.interactions:
            if interactionTo not in toInteractionsWithPredictions: # false negative gold
                t1 = goldGraph.entityHeadTokenByEntity[goldGraph.entitiesById[interactionTo.get("e1")]]
                t2 = goldGraph.entityHeadTokenByEntity[goldGraph.entitiesById[interactionTo.get("e2")]]                
                if t1 != t2:
                    exampleGraph.add_edge(t1, t2, element=interactionTo)
                    edge = self.getNXEdge(exampleGraph, t1, t2, interactionTo)
                    edge[2]["arcStyles"] = {"stroke":"#79BAEC"}
                    edge[2]["labelStyles"] = {"fill":"#79BAEC"}
                    stats["fn"] += 1
        
        builder.header("Classification",4)
        svgTokens = GraphToSVG.tokensToSVG(goldGraph.tokens,False,None,extraByToken)
        #arcStyles, labelStyles = self.getMatchingEdgeStyles(exampleGraph, sentenceGraph.interactionGraph, "green", "red" )
        svgEdges = GraphToSVG.edgesToSVG(svgTokens, exampleGraph, "type", None)
        sentenceId = sentenceGraph.getSentenceId()
        svgElement = GraphToSVG.writeSVG(svgTokens, svgEdges, self.outDir+"/svg/"+sentenceId+"-"+str(sentenceIndex)+"_learned.svg")
        builder.svg("../svg/" + sentenceId + "-"+str(sentenceIndex)+"_learned.svg",svgElement.attrib["width"],svgElement.attrib["height"],id="learned_graph")
        builder.lineBreak()
        return stats
    
    def makeExampleGraph(self, builder, sentenceGraph, examples, classificationsByExample, sentenceIndex):
        exampleGraph = NX.XDiGraph()#multiedges = True)
        for token in sentenceGraph.tokens:
            exampleGraph.add_node(token)
        arcStyles = {}
        labelStyles = {}
        extraByToken = {}
        edgeTypes = {}
        if examples != None:
            for example in examples:
                if classificationsByExample.has_key(example[0]):
                    classification = classificationsByExample[example[0]]
                    if example[3]["xtype"] == "edge" and classification[1] != "tn": #and a[1] != "fn":
                        if classification[2] != "multiclass":
                            exampleGraph.add_edge(example[3]["t1"], example[3]["t2"], example[0])
                        else:
                            exampleGraph.add_edge(example[3]["t1"], example[3]["t2"], example[0]) # self.classSet.getName(classification[3]))
                    elif example[3]["xtype"] == "token" and classification[1] != "tn":
                        if classification[1] == "tp":
                            style = {"fill":"green"}
                        if classification[1] == "fp":
                            style = {"fill":"red"}
                        if classification[1] == "fn":
                            style = {"fill":"#79BAEC"}
                        if classification[2] != "multiclass":
                            extraByToken[example[3]["t"]] = (classification[1],style)
                        else:
                            extraByToken[example[3]["t"]] = (self.classSet.getName(classification[3]),style)
        for edge in exampleGraph.edges():
            addType = False
            classification = classificationsByExample[edge[2]][1]
            if classification == "tp":
                arcStyles[edge] = {"stroke":"green"}
                labelStyles[edge] = {"fill":"green"}
                addType = True
            elif classification == "fp":
                arcStyles[edge] = {"stroke":"red"}
                labelStyles[edge] = {"fill":"red"}
                addType = True
            elif classification == "fn":
                arcStyles[edge] = {"stroke":"#79BAEC"}
                labelStyles[edge] = {"fill":"#79BAEC"}
                addType = True
            if addType:
                if classificationsByExample[edge[2]][2] != "multiclass":
                    edgeTypes[edge] = classificationsByExample[edge[2]][0][3]["type"]
                else:
                    edgeTypes[edge] = self.classSet.getName(classificationsByExample[edge[2]][3])
                    if len(edgeTypes[edge]) > 3 and edgeTypes[edge][-4:] == "_rev":
                        edgeTypes[edge] = edgeTypes[edge][:-4]
                        if classificationsByExample[edge[2]][0][3]["deprev"]:
                            edgeTypes[edge] += ">"
                        else:
                            edgeTypes[edge] = "<" + edgeTypes[edge]
                    else:
                        if classificationsByExample[edge[2]][0][3]["deprev"]:
                            edgeTypes[edge] = "<" + edgeTypes[edge]
                        else:
                            edgeTypes[edge] += ">"                    

        builder.header("Classification",4)
        svgTokens = GraphToSVG.tokensToSVG(sentenceGraph.tokens,False,None,extraByToken)
        #arcStyles, labelStyles = self.getMatchingEdgeStyles(exampleGraph, sentenceGraph.interactionGraph, "green", "red" )
        svgEdges = GraphToSVG.edgesToSVG(svgTokens, exampleGraph, arcStyles, labelStyles, None, edgeTypes)
        sentenceId = sentenceGraph.getSentenceId()
        svgElement = GraphToSVG.writeSVG(svgTokens, svgEdges, self.outDir+"/svg/"+sentenceId+"-"+str(sentenceIndex)+"_learned.svg")
        builder.svg("../svg/" + sentenceId + "-"+str(sentenceIndex)+"_learned.svg",svgElement.attrib["width"],svgElement.attrib["height"],id="learned_graph")
        builder.lineBreak()
    
    def makeSentencePage(self, sentenceGraph, examples, classificationsByExample, prevAndNextId=None, goldGraph=None):
        # Store info for sentence list
        sentenceId = sentenceGraph.getSentenceId()
        self.sentences.append([sentenceGraph,0,0,0,0])
        sentenceIndex = len(self.sentences)
        sentenceGraph.stats = {"entities":0,"edges":0,"tp":0,"fp":0,"tn":0,"fn":0}
        visualizationSet = None
        if examples != None:
            for example in examples:
                if visualizationSet == None:
                    visualizationSet = example[3]["visualizationSet"]
                else:
                    assert(visualizationSet == example[3]["visualizationSet"])
                self.sentences[-1][1] += 1
                if classificationsByExample.has_key(example[0]):
                    classification = classificationsByExample[example[0]]
                    self.sentences[-1][2] += 1
                    if classification[1] == "tp":
                        self.sentences[-1][3] += 1
                    elif classification[1] == "fp":
                        self.sentences[-1][4] += 1
            sentenceGraph.visualizationSet = visualizationSet
        
        # Make the page
        entityElements = sentenceGraph.entities
        entityTextById = {}
        for entityElement in entityElements:
            entityTextById[entityElement.get("id")] = entityElement.get("text")
        
        # Boot-it NG
        builder = HtmlBuilder()        
        builder.newPage("Sentence " + sentenceId, "../")
        builder.addScript("../js/highlight_svg.js")
        builder.body.set("onload","for(i in document.forms){document.forms[i].reset();}")
        
        builder.div()
        builder.header("Sentence " + sentenceId,1)
        #builder.lineBreak()
        
        if prevAndNextId != None:
            if prevAndNextId[0] != None:
                builder.link(prevAndNextId[0]+"-"+str(sentenceIndex-1)+".html","previous")
            else:
                builder.span("previous","color:#0000FF;")
            if prevAndNextId[1] != None:
                builder.link(prevAndNextId[1]+"-"+str(sentenceIndex+1)+".html","next")
            else:
                builder.span("next","color:#0000FF;")
    
        builder.span("Original ID: " + self.__getOrigId(sentenceGraph.sentenceElement))
        builder.span("Index: " + str(sentenceIndex))
        builder.closeElement() # div      
        builder.lineBreak()
        
        # Parse SVG
        builder.header("Parse",4)
        svgTokens = GraphToSVG.tokensToSVG(sentenceGraph.tokens, True)
        nxDepGraph = NX10.MultiDiGraph()
        for edge in sentenceGraph.dependencyGraph.edges:
            nxDepGraph.add_edge(edge[0], edge[1], element=edge[2])
        svgDependencies = GraphToSVG.edgesToSVG(svgTokens, nxDepGraph)
        svgElement = GraphToSVG.writeSVG(svgTokens, svgDependencies,self.outDir+"/svg/"+sentenceId+"-"+str(sentenceIndex)+".svg")
        builder.svg("../svg/" + sentenceId + "-"+str(sentenceIndex)+".svg",svgElement.attrib["width"],svgElement.attrib["height"],id="dep_graph")
        builder.lineBreak()
        
        
        # Annotation SVG
        builder.header("Annotation",4)
        if goldGraph != None:
            # Check for named entities
            isNameByToken = {}
            for token in goldGraph.tokens:
                if goldGraph.getTokenText(token) == "NAMED_ENT":
                    isNameByToken[token] = True
                else:
                    isNameByToken[token] = False
            #arcStyles, labelStyles = self.getMatchingEdgeStyles(goldGraph.interactionGraph, goldGraph.dependencyGraph, "orange", "#F660AB" )
            svgTokens = GraphToSVG.tokensToSVG(goldGraph.tokens, False, goldGraph.entitiesByToken, None, isNameByToken)
            nxGraph = NX10.MultiDiGraph()
            for edge in goldGraph.interactionGraph.edges:
                nxGraph.add_edge(edge[0], edge[1], element=edge[2])
            svgInteractionEdges = GraphToSVG.edgesToSVG(svgTokens, nxGraph)
            svgElement = GraphToSVG.writeSVG(svgTokens, svgInteractionEdges,self.outDir+"/svg/"+sentenceId+"-"+str(sentenceIndex)+"_ann.svg")
        elif sentenceGraph.interactionGraph != None:
            # Check for named entities
            isNameByToken = {}
            for token in sentenceGraph.tokens:
                if sentenceGraph.getTokenText(token) == "NAMED_ENT":
                    isNameByToken[token] = True
                else:
                    isNameByToken[token] = False
            #arcStyles, labelStyles = self.getMatchingEdgeStyles(sentenceGraph.interactionGraph, sentenceGraph.dependencyGraph, "orange", "#F660AB" )
            svgTokens = GraphToSVG.tokensToSVG(sentenceGraph.tokens, False, sentenceGraph.entitiesByToken, None, isNameByToken)
            nxGraph = NX10.MultiDiGraph()
            for edge in goldGraph.interactionGraph.edges:
                nxGraph.add_edge(edge[0], edge[1], element=edge[2])
            svgInteractionEdges = GraphToSVG.edgesToSVG(svgTokens, nxGraph)
            svgElement = GraphToSVG.writeSVG(svgTokens, svgInteractionEdges,self.outDir+"/svg/"+sentenceId + "-"+str(sentenceIndex)+"_ann.svg")
        builder.svg("../svg/" + sentenceId + "-"+str(sentenceIndex)+"_ann.svg",svgElement.attrib["width"],svgElement.attrib["height"],id="ann_graph")
        builder.lineBreak()
        
        # Classification svg
        if classificationsByExample != None:
            self.makeExampleGraph(builder, sentenceGraph, examples, classificationsByExample, sentenceIndex)      
        elif goldGraph != None:
            sentenceGraph.stats = self.makeExampleGraphWithGold(builder, sentenceGraph, goldGraph, sentenceIndex)
        
        builder.table(0,align="center",width="100%")
        builder.tableRow()
        # interactions
        pairElements = sentenceGraph.interactions
        builder.tableData(valign="top")
        builder.header("Interactions",4)
        builder.table(1,True)
        builder.tableHead()
        builder.tableRow()
        builder.tableHeader("id", True)
        builder.tableHeader("type", True)
        builder.tableHeader("e1", True)
        builder.tableHeader("e2", True)
        builder.tableHeader("e1 word", True)
        builder.tableHeader("e2 word", True)
        #builder.tableHeader("interaction", True)
        #th = builder.tableHeader("view",True)
        #th.set("class","{sorter: false}")
        builder.closeElement()
        builder.closeElement() # close tableHead
        builder.tableBody()
        for pairElement in sentenceGraph.interactions:
            tr = builder.tableRow()
            #tr.set( "onmouseover", getPairHighlightCommand("main_parse",pairElement.get("e1"),pairElement.get("e2"),entityTokens,"highlightPair") )
            #tr.set( "onmouseout", getPairHighlightCommand("main_parse",pairElement.get("e1"),pairElement.get("e2"),entityTokens,"deHighlightPair") )
            builder.tableData(pairElement.get("id").split(".")[-1][1:], True)
            builder.tableData(pairElement.get("type"), True)
            builder.tableData(pairElement.get("e1").split(".")[-1][1:], True)
            builder.tableData(pairElement.get("e2").split(".")[-1][1:], True)
            builder.tableData(entityTextById[pairElement.get("e1")], True)
            builder.tableData(entityTextById[pairElement.get("e2")], True)
            #builder.tableData("Dummy", True)
            #builder.tableData()
            #builder.form()
            #input = builder.formInput("checkbox")
            ##input.set("onClick",getPairHighlightCommand("main_parse",pairElement.get("e1"),pairElement.get("e2"),entityTokens,"toggleSelectPair",pairElement.get("id")) )
            #builder.closeElement() # form
            #builder.closeElement() # tableData
            builder.closeElement()
        builder.closeElement() # close tableBody
        builder.closeElement() # close table
        
        # entities
        builder.tableData(valign="top")
        builder.header("Entities",4)
        builder.table(1,True)
        builder.tableHead()
        builder.tableRow()
        builder.tableHeader("id", True)
        builder.tableHeader("text", True)
        builder.tableHeader("type", True)
        builder.tableHeader("charOffset", True)
        builder.closeElement() # close tableRow
        builder.closeElement() # close tableHead
        entityElements = sentenceGraph.entities
        builder.tableBody()
        for entityElement in entityElements:
            builder.tableRow()
            builder.tableData(entityElement.get("id").split(".")[-1][1:], True)
            builder.tableData(entityElement.get("text"), True)
            if entityElement.attrib["isName"] == "True":
                builder.tableData("["+entityElement.get("type")+"]", True)
            else:
                builder.tableData(entityElement.get("type"), True)
            charOffset = entityElement.get("charOffset")
            charOffsetSplits = charOffset.split(",")
            headOffset = entityElement.get("headOffset")
            charOffset = ""
            headFound = False
            for charOffsetSplit in charOffsetSplits:
                if charOffset != "":
                    charOffset += ","
                if charOffsetSplit == headOffset:
                    charOffset += "<u>" + charOffsetSplit + "</u>"
                    headFound = True
                else:
                    charOffset += charOffsetSplit
            if not headFound:
                charOffset += " (<u>" + headOffset + "</u>)"
            builder.tableData(charOffset, True)
            builder.closeElement()
        builder.closeElement() # close tableBody
        builder.closeElement() # close table
        
        builder.closeElement() # close row
        builder.closeElement() # close table
        
        builder.closeElement() # close row
        builder.closeElement() # close table
        
        # Examples
        if examples != None:
            builder.header("Examples",4)
            for example in examples:
                string = example[0]
                if classificationsByExample.has_key(example[0]):
                    string += " (" + classificationsByExample[example[0]][1] + ")"
                string += ":"
                features = example[2]
                if self.featureSet != None:
                    featureNames = []
                    for key in features.keys():
                        featureNames.append(self.featureSet.getName(key))
                    featureNames.sort()
                    for featureName in featureNames:
                        string += " " + featureName + ":" + str(features[self.featureSet.getId(featureName)])
                else:
                    keys = features.keys()
                    keys.sort()
                    for key in keys:
                        featureName = str(key)
                        string += " " + featureName + ":" + str(features[key])
                #string += "\n"
                builder.span(string)
                builder.lineBreak()
                builder.lineBreak()
            
        builder.write(self.outDir + "/sentences/"+sentenceId+"-"+str(sentenceIndex)+".html")
        repairApostrophes(self.outDir + "/sentences/"+sentenceId+"-"+str(sentenceIndex)+".html")
    
    def makeSentenceListPage(self):
        #print >> sys.stderr, "Making sentence page"
        builder = HtmlBuilder()
        builder.newPage("Sentences","")
        builder.header("Sentences")
        builder.table(1,True)
        builder.tableHead()
        builder.tableRow()
        builder.tableHeader("id",True)
        builder.tableHeader("text",True)
        builder.tableHeader("origId",True)
        #builder.tableHeader("set",True)
        builder.tableHeader("entities",True)
        builder.tableHeader("edges",True)
        #builder.tableHeader("examples",True)
        #builder.tableHeader("classifications",True)
        ##builder.tableHeader("pairs",True)
        ##builder.tableHeader("int",True)
        builder.tableHeader("tp     ",True)
        builder.tableHeader("fp     ",True)
        builder.tableHeader("fn     ",True)
        builder.closeElement() # close tableRow
        builder.closeElement() # close tableHead
        
        builder.tableBody()
        count = 0
        for sentence in self.sentences:
            count += 1
            if sentence == None:
                continue
            #sentence = sentencesById[key]
            sentenceId = sentence[0].getSentenceId()
            builder.tableRow()
            builder.tableData()
            builder.link("sentences/" + sentenceId + "-" + str(count) + ".html", sentenceId)
            builder.closeElement()
            
            text = sentence[0].sentenceElement.attrib["text"]
            if len(text) > 80:
                text = text[:80] + "..."
            builder.tableData(text,True)
            builder.tableData(self.__getOrigId(sentence[0].sentenceElement),True)
            #if hasattr(sentence[0], "visualizationSet"):
            #    builder.tableData(str(sentence[0].visualizationSet),True)
            #else:
            #    builder.tableData("N/A",True)
            #builder.tableData(str(sentence[1]),True)
            #builder.tableData(str(sentence[2]),True)
            builder.tableData(str(sentence[0].stats["entities"]),True)
            builder.tableData(str(sentence[0].stats["edges"]),True)
            builder.tableData(str(sentence[0].stats["tp"]),True)
            builder.tableData(str(sentence[0].stats["fp"]),True)
            builder.tableData(str(sentence[0].stats["fn"]),True)
            #builder.tableData(str(len(sentence.annotationDependencies)),True)
            #builder.tableData(str(len(sentence.entities)),True)
            #pairs = sentence.pairs
            #builder.tableData(str(len(pairs)),True)
            #numInteractions = 0
            #for pair in pairs:
            #    if pair.get("interaction") == "True":
            #        numInteractions += 1
            #builder.tableData(str(numInteractions),True)
            #tp = sentence[3]
            #fp = sentence[4]
            #builder.tableData(str(tp),True)
            #builder.tableData(str(fp),True)
            builder.closeElement() # close tableRow
        builder.closeElement() # close tableBody
        builder.closeElement() # close table
        
        builder.write(self.outDir+"/sentences.html")

def repairApostrophes(filename):
    f = open(filename)
    lines = f.readlines()
    f.close()
    
    for i in range(len(lines)):
        apos = lines[i].find("&apos;")
        while apos != -1:
            lines[i] = lines[i][:apos] + "'" + lines[i][apos + 6:]
            apos = lines[i].find("&apos;")
        
        lt = lines[i].find("&lt;")
        while lt != -1:
            lines[i] = lines[i][:lt] + "<" + lines[i][lt + 4:]
            lt = lines[i].find("&lt;")

        gt = lines[i].find("&gt;")
        while gt != -1:
            lines[i] = lines[i][:gt] + ">" + lines[i][gt + 4:]
            gt = lines[i].find("&gt;")
    
    f = open(filename,"wt")
    f.writelines(lines)
    f.close()

if __name__=="__main__":
    import sys, os, shutil
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import Core.ExampleUtils as Example
    try:
        import xml.etree.cElementTree as ET
    except ImportError:
        import cElementTree as ET
    from InteractionXML.CorpusElements import CorpusElements
    from Core.SentenceGraph import *
    from Visualization.CorpusVisualizer import CorpusVisualizer
    from optparse import OptionParser
    import Settings

    optparser = OptionParser(usage="%prog [options]\nCreate an html visualization for a corpus.")
    optparser.add_option("-i", "--input", default=Settings.DevelFile, dest="input", help="Corpus in analysis format", metavar="FILE")
    optparser.add_option("-g", "--gold", default=None, dest="gold", help="Gold standard in interaction XML", metavar="FILE")
    optparser.add_option("-o", "--output", default=None, dest="output", help="Output directory, useful for debugging")
    optparser.add_option("-t", "--tokenization", default="split-McClosky", dest="tokenization", help="tokenization")
    optparser.add_option("-p", "--parse", default="split-McClosky", dest="parse", help="parse")
    (options, args) = optparser.parse_args()
    
    corpusElements = loadCorpus(options.input, options.parse, options.tokenization)
    sentences = []
    for sentence in corpusElements.sentences:
        #print "ent", len(sentence.entities)
        #print "int", len(sentence.interactions)
        sentences.append( [sentence.sentenceGraph,None] )
    
    goldElements = None
    if options.gold != None:
        print >> sys.stderr, "Loading Gold Standard Corpus"
        goldElements = loadCorpus(options.gold, options.parse, options.tokenization)
    
    print >> sys.stderr, "Visualizing"
    visualizer = CorpusVisualizer(options.output, True)
    for i in range(len(sentences)):
        sentence = sentences[i]
        if sentence[0] != None:
            print >> sys.stderr, "\rProcessing sentence", sentence[0].getSentenceId(), "          ",
        else:
            continue
        prevAndNextId = [None,None]
        if i > 0 and sentences[i-1][0] != None:
            prevAndNextId[0] = sentences[i-1][0].getSentenceId()
        if i < len(sentences)-1 and sentences[i+1][0] != None:
            prevAndNextId[1] = sentences[i+1][0].getSentenceId()
        if goldElements != None:
            visualizer.makeSentencePage(sentence[0],sentence[1],None,prevAndNextId,goldElements.sentencesById[sentence[0].getSentenceId()].sentenceGraph)
        else:
            visualizer.makeSentencePage(sentence[0],sentence[1],None,prevAndNextId)
    visualizer.makeSentenceListPage()
    print >> sys.stderr