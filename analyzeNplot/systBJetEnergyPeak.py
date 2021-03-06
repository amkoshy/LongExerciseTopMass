
#!/usr/bin/env python

import optparse
import os,sys
import json
import pickle
import ROOT
from subprocess import Popen, PIPE

"""
Perform the analysis on a single file
"""
def runBJetEnergyPeak(inFileURL, outFileURL, xsec=None):

    print '...analysing %s' % inFileURL
    
    #book some histograms for systematic samples
    histos={ 
        # nominal (for xcheck)
        'bjetenls_nominal':ROOT.TH1F('bjetenls_nominal',';log(E);  1/E dN_{b jets}/dlog(E)',20,3.,7.),

        # JER
        'bjetenls_jer_up':ROOT.TH1F('bjetenls_jer_up',';log(E);  1/E dN_{b jets}/dlog(E)',20,3.,7.),
        'bjetenls_jer_down':ROOT.TH1F('bjetenls_jer_down',';log(E);  1/E dN_{b jets}/dlog(E)',20,3.,7.),

        # JEC: uncorrelated group


        # JEC: in-situ correlation group

        # JEC: inter-calibration

        # JEC: pile-up

        # JEC: flavour
        
        # Other Systematics

        }

    for key in histos:
        histos[key].Sumw2()
        histos[key].SetDirectory(0)

    #open file and loop over events tree
    fIn=ROOT.TFile.Open(inFileURL)
    tree=fIn.Get('data')
    totalEntries=tree.GetEntriesFast()

    for i in xrange(0,totalEntries):

        tree.GetEntry(i)
        if i%100==0 : sys.stdout.write('\r [ %d/100 ] done' %(int(float(100.*i)/float(totalEntries))) )

        #generator level weight only for MC                                   
        evWgt=[]
        if xsec              :
            evWgt  = [xsec*tree.LepSelEffWeights[0]*tree.PUWeights[0],
                      xsec*tree.LepSelEffWeights[1]*tree.PUWeights[0],
                      xsec*tree.LepSelEffWeights[2]*tree.PUWeights[0],
                      xsec*tree.LepSelEffWeights[0]*tree.PUWeights[1],
                      xsec*tree.LepSelEffWeights[0]*tree.PUWeights[2],
                      xsec*tree.LepSelEffWeights[0]*tree.PUWeights[0]*tree.TopPtWgt]
        else:
            evWgt = [1.0,1.0,1.0,1.0,1.0,1.0]
            
        xsecWgt_up = 1
        xsecWgt_down = 1

        #25% uncertainty on ttgamma xsec
        if 'SingleT' in inFileURL:
            # xsecWgt_up = ???
            # xsecWgt_down = ???
        # 100% uncertainty on WJets xsec
        if 'WJets' in inFileURL:
            # xsecWgt_up = ???
            # xsecWgt_down = ???
        # 50% uncertainty on other processes 
        if 'DY' in inFileURL or 'WZ' in inFileURL or 'ZZ' in inFileURL or 'WZ' in inFileURL:
            # xsecWgt_up = ???
            # xsecWgt_down = ???

        if tree.nGenWeight>0 :
            for i in range(0,len(evWgt)):
                evWgt[i] *= tree.GenWeights[0]

        nLeptons = 0
        leptonsP4=[]

        for ij in xrange(0,tree.nLepton):

            #get the kinematics and select the lepton                                                                
            lp4=ROOT.TLorentzVector()
            lp4.SetPtEtaPhiM(tree.Lepton_pt[ij],tree.Lepton_eta[ij],tree.Lepton_phi[ij],0)
            if lp4.Pt()<20 or ROOT.TMath.Abs(lp4.Eta())>2.4 : continue

            #count selected jet                                                                                   
            nLeptons +=1

            leptonsP4.append(lp4)

        if nLeptons<2 : continue


        #Fill histograms for JEC variations
        for iJEC in range (0,27):

            #require at least two jets
            nJets, nBtags = 0, 0
            taggedJetsP4=[]
            taggedJetsP4_up=[]
            taggedJetsP4_down=[]
            matchedJetsP4=[]
        
            for ij in xrange(0,tree.nJet):

                #get the kinematics and select the jet
                jp4=ROOT.TLorentzVector()
                jp4.SetPtEtaPhiM(tree.Jet_pt[ij],tree.Jet_eta[ij],tree.Jet_phi[ij],tree.Jet_mass[ij])


                ### access JEC variations from tree.Jet_unc branch
                w_jec_up= 1.
                w_jec_down= 1.

                if jp4.Pt()<30 or ROOT.TMath.Abs(jp4.Eta())>2.4 : continue

                #count selected jet
                nJets +=1

                #save P4 for b-tagged jet
                if tree.Jet_CombIVF[ij]>0.8484: # medium cut
                    nBtags+=1
                    taggedJetsP4.append(jp4)
                    taggedJetsP4_up.append(jp4*w_jec_up)
                    taggedJetsP4_down.append(jp4*w_jec_down)
                    if abs(tree.Jet_flavour[ij]) == 5:
                        matchedJetsP4.append(jp4)
        
            # nJet and nBJet cut
            if nJets<2 : continue
            if nBtags!=1 and nBtags!=2 : continue

            ## fill JEC histograms
            for ij in xrange(0,len(taggedJetsP4)):
                if ij>1 : break
                if iJEC > 0 :
                    #fill JEC histograms
                else :
                    #fill JER histogram

                
        #save P4 for b-tagged jet
        #use up to two leading b-tagged jets
        for ij in xrange(0,len(taggedJetsP4)):
            if ij>1 : break
            #fill other histograms (nominal and weight based)

            #histos['bjetenls_nominal'].Fill(....)


    fIn.Close()

    #save histograms to file
    fOut=ROOT.TFile.Open(outFileURL,'RECREATE')
    for key in histos: histos[key].Write()
    fOut.Close()


"""
Wrapper to be used when run in parallel
"""
def runBJetEnergyPeakPacked(args):
    
    try:
        return runBJetEnergyPeak(inFileURL=args[0],
                                 outFileURL=args[1],
                                 xsec=args[2])
    except :
        print 50*'<'
        print "  Problem  (%s) with %s continuing without"%(sys.exc_info()[1],args[0])
        print 50*'<'
        return False


"""
steer the script
"""
def main():

    #configuration
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)
    parser.add_option('-j', '--json',        dest='json'  ,      help='json with list of files',      default=None,        type='string')
    parser.add_option('-i', '--inDir',       dest='inDir',       help='input directory with files',   default=None,        type='string')
    parser.add_option('-o', '--outDir',      dest='outDir',      help='output directory',             default='analysis',  type='string')
    parser.add_option('-n', '--njobs',       dest='njobs',       help='# jobs to run in parallel',    default=0,           type='int')
    (opt, args) = parser.parse_args()

    #read list of samples
    jsonFile = open(opt.json,'r')
    samplesList=json.load(jsonFile,encoding='utf-8').items()
    jsonFile.close()

    #prepare output
    if len(opt.outDir)==0    : opt.outDir='./'
    os.system('mkdir -p %s' % opt.outDir)
        
    #create the analysis jobs
    taskList = []
    for sample, sampleInfo in samplesList: 
        inFileURL  = 'root://cmseos.fnal.gov//%s/%s.root' % (opt.inDir,sample)
        #if not os.path.isfile(inFileURL): continue
        xsec=sampleInfo[0] if sampleInfo[1]==0 else None        
        outFileURL = '%s/%s.root' % (opt.outDir,sample)
        taskList.append( (inFileURL,outFileURL,xsec) )

    #run the analysis jobs
    if opt.njobs == 0:
        for inFileURL, outFileURL, xsec in taskList:
            runBJetEnergyPeak(inFileURL=inFileURL, outFileURL=outFileURL, xsec=xsec)
    else:
        from multiprocessing import Pool
        pool = Pool(opt.njobs)
        pool.map(runBJetEnergyPeakPacked,taskList)

    #all done here
    print 'Analysis results are available in %s' % opt.outDir
    exit(0)



"""
for execution from another script
"""
if __name__ == "__main__":
    sys.exit(main())
