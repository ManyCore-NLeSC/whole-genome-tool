from praline.core import Manager, BeginMessage, CompleteMessage, ProgressMessage
from praline.component import TreeMultipleSequenceAligner
from praline import write_alignment_clustal
from praline.core import *
from praline.container import Sequence, ScoreMatrix, TRACK_ID_INPUT
from praline.container import ProfileTrack, PlainTrack
from praline.container import TRACK_ID_PREPROFILE, TRACK_ID_PROFILE
from praline.container import SequenceTree, Alignment
from praline.component import PairwiseAligner
from praline.util import auto_align_mode
import numpy as np

import requests
import time

SERVER = "http://localhost:4567"

from os.path import expanduser
home = expanduser("~")

with open(home + '/bowbeforeme', 'r') as myfile:
  host = myfile.read()

SERVER = "http://" + host + ":4567"

use_our_stuff = True

_INTERCEPT_TIDS = {TreeMultipleSequenceAligner.tid}

class ConstellationManager(Manager):
    def execute_many(self, requestss, parent_tag):

        print requestss
        print "Hallo!"
        not_msa = not use_our_stuff
        for tid, inputs, tag, env in requestss:
          if not tid in _INTERCEPT_TIDS:
            print tid
            not_msa = True
        if not_msa:
          gen = super(ConstellationManager, self).execute_many(requestss,parent_tag)
          for message in gen:
            yield message

          return
        
          
        trees = []
            # We're not handling these tasks in this manager, so execute them
            # normally using the functionality of the superclass.
        for tid, inputs, tag, env in requestss:
   

            # We want to intercept execution of these tasks and send them off
            # to constellation. First pass a message saying we've begun
            # executing the tasks.
            for tid, inputs, tag, env in requestss:
                begin_message = BeginMessage(parent_tag)
                begin_message.tag = tag
                yield begin_message


            # TODO: convert task inputs to constellation format, send it to
            # Constellation and wait for completion. Yield ProgressMessage
            # instances to report progress to the UI if applicable.
            
         # We're not handling these tasks in this manager, so execute them
            # normally using the functionality of the superclass.
            score_matrices = inputs.get("score_matrices", None)
            seqs = inputs.get("sequences", None)
            tree = inputs.get("guide_tree", None)
            track_id_sets = inputs.get("track_id_sets",None)
            gap_series = env['gap_series']
            merge_mode = env['merge_mode']
               
            s = [sm.matrix.astype(np.float32) for sm in score_matrices]
            uniquestr = str(time.time())
            costName = "cost" + uniquestr
            treeName = "tree" + uniquestr
            sendCosts(costName, s)

            uniquestr = str(time.time())
            alignmentsi = {i:[seq] for i, seq in enumerate(seqs)}
            for i, j in tree.merge_orders:
                alignmentsi[i]+=alignmentsi[j]
          
            
            data = ' '.join([str(i) + "," + str(j) for i, j in  tree.merge_orders])

            start_gap, extend_gap = 0, 0
            if len(gap_series) == 2:
              start_gap, extend_gap = gap_series[0], gap_series[1]
            elif len(gap_series) == 1:
              start_gap = extend_gap = gap_series[0]
            else :
              raise ComponentError("NO GAP COST!!!")     
            
            reqstring = "/register/tree/" + treeName + "/" + str(len(seqs)) + "/" + costName + "/" + merge_mode + "/" + str(start_gap) + "/" + str(extend_gap)
            #print data
            req = requests.post(SERVER + reqstring , data=data)

            for i, seq in enumerate(seqs):

                    
                sendSequence(treeName,i,[seq.get_track(t[0]) for t in track_id_sets],s)
            trees+=[treeName]
               
                
        # for tree in trees:
        #  print(tree)
        requests.get(SERVER + "/processtrees")
        for (tid, inputs, tag, env),tree in zip(requestss,trees):
           while True:
              req = requests.get(SERVER + "/retrieve/steps/" + tree)
              # print("not yet" + tree + " " + str(req.status_code))
              if req.status_code == 200:
                  res = np.array([[int(d) for d in c.split(';')] for c in req.text.split(' ')])
                  outputs={}
                  outputs['alignment'] =Alignment(alignmentsi[0], res)

                  complete_message = CompleteMessage(outputs=outputs)
                  complete_message.tag = tag
                  yield complete_message
                  break
       



def sendSequence(tree_name, leaf, tracks,s):
    # nrTracks = len(tracks[0].values)
    
    seqs = [profToSequence(track) for track in tracks ]
    nrTracks = len(tracks)
    nrPos = len(seqs[0])
    
    
        
    data = ' '.join([ str(seqs[t][p]) for t in range(nrTracks) for p in range(nrPos)  ])

    #/send/sequence/:length/toqueue/:queue_name
    reqstring = "/send/sequence/" + str(leaf) + "/" + str(nrPos) + "/totree/" + tree_name
    # print reqstring
    req = requests.post(SERVER + reqstring, data=data)
    #print req
    #print data
    if req.status_code !=  201:
        raise ComponentError("HTTP ERROR"  + req.text)
    


def profToSequence(track):
    if track.tid == PlainTrack.tid :
        return track.values    
    else : 
        prof = track.profile.astype(np.float32)
        i,t = prof.shape
    
        return [getIndex(prof,z,t) for z in range(i)]

def getIndex(prof, i, t):
    for j in range(t):
        if prof[i][j] > 0:
            return j
    return 0
    

def sendCosts(name, matrixes):
    req = requests.get(SERVER + "/register/cost_matrix/" + name + "/" + str(len(matrixes)))
    
    if req.status_code !=  201:
        raise ComponentError("HTTP ERROR" + req.text)

    for i,t in enumerate(matrixes) :
        (x,y) = t.shape 
        if x != y:
            raise ComponentError("Matrix not square!")
        data = ' '.join([ str(t[z,j]) for z in range(x) for j in range(y) ])
        reqstring = "/send/cost_matrix/" + name + "/" + str(i) + "/" + str(x) 
        #print reqstring
        #print data
        req = requests.post(SERVER + reqstring , data=data)
        if req.status_code !=  201:
            raise ComponentError("HTTP ERROR: " + req.text)
