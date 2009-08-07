import sys,os,time
sys.path.append("..")
from ExampleBuilders.GeneralEntityTypeRecognizer import GeneralEntityTypeRecognizer
from ExampleBuilders.GeneralEntityTypeRecognizerGztr import GeneralEntityTypeRecognizerGztr
from ExampleBuilders.MultiEdgeExampleBuilder import MultiEdgeExampleBuilder
from Classifiers.SVMMultiClassClassifier import SVMMultiClassClassifier as Cls
from Evaluators.AveragingMultiClassEvaluator import AveragingMultiClassEvaluator as Ev
import Core.SentenceGraph as SentenceGraph
import Core.ExampleUtils as ExampleUtils
import InteractionXML as ix
import Evaluators.EvaluateInteractionXML as EvaluateInteractionXML
from Core.OptimizeParameters import optimize
import Utils.Stream as Stream
import atexit, shutil
from Core.RecallAdjust import RecallAdjust
from Core.Gazetteer import Gazetteer
from Murska.CSCConnection import CSCConnection
sys.path.append("../../../../GeniaChallenge/unflattening")
import prune
import unflatten
sys.path.append("../../../../GeniaChallenge/formatConversion")
from gifxmlToGenia import gifxmlToGenia
sys.path.append("../../../../GeniaChallenge")
import evaluation.EvaluateSharedTask
evaluateSharedTask = evaluation.EvaluateSharedTask.evaluate

def workdir(path, deleteIfExists=True):
    if os.path.exists(path):
        if deleteIfExists:
            print >> sys.stderr, "Output directory exists, removing", path
            shutil.rmtree(path)
            os.mkdir(path)
    else:
        os.mkdir(path)
    origDir = os.getcwd()
    os.chdir(path)
    atexit.register(os.chdir, origDir)

def log():
    Stream.setLog("log.txt", True)
    Stream.setTimeStamp("[%H:%M:%S]", True)
    print >> sys.stderr, "####### Log opened at ", time.ctime(time.time()), "#######"

# Import Psyco if available
try:
    import psyco
    psyco.full()
    print >> sys.stderr, "Found Psyco, using"
except ImportError:
    print >> sys.stderr, "Psyco not installed"
