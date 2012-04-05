from operator import itemgetter
import math
import time                                                

def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '%r: %2.2f sec' % \
              (method.__name__, te-ts)
        return result

    return timed

def unique(list):
    set = {}
    return [ set.setdefault(x,x) for x in list if x not in set ]

def avance(current,total,goal):
    percent = float(current)/float(total)
    if percent >= goal: 
        print "   -> "+str(round(percent*100))+"%"+" ("+str(current)+")" 
        return goal + 0.03, current + 1
    
    return goal,current + 1

def get_n_top_val(n, topic_score):

    f_min = -10000000
    ts = topic_score.items()
    ts.sort(key = itemgetter(1), reverse=True)
    return ts[0:n]

def get_max_val(dic):
    maxval = 0  
    label = "No hay maximo!" 
    for i in dic:
        if maxval < dic[i]:
            maxval = dic[i]
            label = i
    return label

def tfidf(local_frec,n_words,K,n_doc_app):
    return float(local_frec)/float(n_words)*(math.log(K/n_doc_app))

def getbest(lista,nbests):
    
    bests = {}    
    id_lista = 1
    for l in lista:
        bests[id_lista] = l                
        id_lista += 1
    
    keys = sorted(bests.items(), key=itemgetter(1), reverse=True)
    keys = keys[:nbests]

    return keys

def normTopicValue(value,isHot = False):
    if value < 0.000099:
        return 0
    else:
        value = int(round(value*10000))

        if isHot and isHotTopic(value) == 1:
            return 100
        else:
            return value

def isHotTopic(value):
    if value > 13:
        return 1
    else:
        return 0
    
def naiveBayesMultinomial(value,frequency,adjustment = 1):
    if not value: return 0
    lim = 80
    if frequency > 92:
        return math.log(math.pow(value*adjustment,lim)/math.factorial(lim))
    else:
        return math.log(math.pow(value*adjustment,frequency)/math.factorial(frequency))
