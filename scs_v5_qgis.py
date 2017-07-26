#-*-coding:utf-8-*-;
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib import gridspec
from math import ceil, trunc
import datetime

def interpola_dt(dt,array):
    aT = np.arange(np.amin(array[0,:]),np.amax(array[0,:])*dt+dt,dt)
    aQ = np.interp(aT, array[0,:], array[1,:])
    return np.vstack((aT,aQ))

def blocos_alt(idf,dur,dt,TR):
    aDur = np.arange(dt,dur+dt,dt)
    #print aDur, len(aDur)
    #Int = (idf[0]*TR**idf[1])/((idf[2]+idf[3])**idf[4])
    aInt = (idf[0]*TR**idf[1])/((aDur+idf[2])**idf[3])
    aPmm = np.multiply(aInt,aDur/60.0)
    aDeltaPmm = np.append(aPmm[0],np.diff(aPmm))
    if (len(aDur) % 2 == 0): #even
        aOrd = np.append(np.arange(len(aDur)-1,0,-2),np.arange(2,len(aDur)+1,2))
    else:
        aOrd = np.append(np.arange(len(aDur),0,-2),np.arange(2,len(aDur)+1,2))
    #print aOrd, len(aOrd)
    prec = np.asarray([aDeltaPmm[x-1] for x in aOrd])
    a=np.append(np.zeros(1),aDur)
    b=np.append(np.zeros(1),prec)
    result = np.vstack((a,b))
    return result

def scsparam(CN):
    S = (25400.0-254.0*CN)/CN
    Ia = 0.05*S
    #Ia = Ia*((100.0-Imp)/100.0)
    return round(S,3), round(Ia,3)

def potRet(Pa, S,Ia, CN,Imp):
    Ia = float(Ia)
    nP = 1.0-(Imp/100.0)
    Pa2 = nP*Pa
    #print 'Pa=%s / Pa2=%s / Ia=%s'%(Pa,Pa2,Ia)
    if Pa>Ia:
        Fa = (S*(Pa2-Ia))/(Pa2-Ia+S)
        aPe = Pa2-Ia-Fa
        if aPe>Pa:
            print 'ERRO NA PERDA - P=%s - Pa*np=%s - Fa=%s = aPe=%s'%(Pa,Pa2,Fa,aPe)
        #aPe = ((Pa-Ia)**2)/(Pa-Ia+S)
    else:
        aPe =0
    #print 'Pa=%s\tPa2=%s\tIa=%s\taPe=%s\tLoss=%s' %(Pa,Pa2,Ia,aPe,(Pa-aPe))
    return float(aPe)

def roundup(x,m):
    m = float(m)
    return int(ceil(x / m)) * m

def get_data():
    varsIn = [u'Área (km2)',u'Tempo de conc.(min.)',u'Tempo de Recorrência (anos)',
            u'Duração da chuva (min.)',u'Delta T (min)',u'CN:',
            u'Impermeabilização (%):']
    lstD = []
    for v in varsIn:
        vA = raw_input(u'Entre com a varíável\n'+v+u'\n>>> ')
        lstD.append(float(vA))
    return lstD

def trataCurva(matriz):
    iZeros = np.where(matriz[1]==0)
    lstBuracos=[]
    for i in iZeros[0].tolist()[1:]:
            if np.sum(matriz[1,:i])!=0:
                    if np.sum(matriz[1,i:])!=0:
                            lstBuracos.append(int(i))
    aHidroFC=np.copy(matriz)
    for b in lstBuracos:
        ant = -np.argmax(matriz[1,:b+1][::-1]>0)
        pos = np.argmax(matriz[1,b:]>0)
        xp = [aHidroFC[0,ant+b],aHidroFC[0,pos+b]]
        fp = [aHidroFC[1,ant+b],aHidroFC[1,pos+b]]
        interp=np.interp(aHidroFC[0,ant+b],xp,fp)
        aHidroFC[1,b]=interp
    lastIndex = np.where(aHidroFC[1]!=0)[0][-1]+1
    return aHidroFC[0:lastIndex,0:lastIndex]

def escreveCSV(nomearq,lstP1):
    A,CNIni,Imp,TC,TR,idf,DUR,DT,aTab = lstP1
    campos = [u'Área (km²)','CN','Ia(mm)','Imperm.(%)','Tc(min.)','Tlag(min.)']
    valoresC = [str(d) for d in [A,CNIni,scsparam(CNIni)[1],Imp, TC,TC*0.6]]
    campos2 = ['TR(anos)','IDF: K', 'a','b','c',u'Duração(min.)','DeltaT(min.)']
    valoresC2 = [str(d2) for d2 in [TR,idf[0],idf[1],idf[2], idf[3],DUR,DT]]
    tit = u't(horas),P(mm),Perdas(mm),Prec.Efet.(mm),Q(m³/s),Vol. (mm)'
    header = '\n'.join([','.join(d3) for d3 in [campos,valoresC,campos2,valoresC2]])+'\n\n'+tit
    #now = datetime.datetime.now()
    #fname= 'SCSUH_'+now.strftime('%d-%m-%Y_%Hh%Mm')+'.csv'
    np.savetxt(nomearq, aTab, fmt='%.3f', delimiter=',', newline='\n', header=header.encode('latin-1'), footer='', comments='')



def geraHidro(A,TC,TR,DUR,DT,CNIni,Imp,idf):
    ### CALCULO DA PREC EFETIVA
    nImp = (100.0-float(Imp))/100.0
    np.set_printoptions(formatter={'float': '{: 0.2f}'.format},threshold=np.nan)
    CN = CNIni + (Imp/100.0)*(100-CNIni)
    #CN = CNIni

    t_tp=np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2, 2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4, 4.5, 5])
    q_qp=np.array([0, 0.03, 0.1, 0.19, 0.31, 0.47, 0.66, 0.82, 0.93, 0.99, 1, 0.99, 0.93, 0.86, 0.78, 0.68, 0.56, 0.46, 0.39, 0.33, 0.28, 0.207, 0.147, 0.107, 0.077, 0.055, 0.04, 0.029, 0.021, 0.015, 0.011, 0.005, 0])

    blalt = blocos_alt(idf,DUR,DT,TR)
    S, Ia = scsparam(CN)

    print 'A=%skm2 - CN=%s - S=%s - Ia=%smm - Imperm.=%s - Tlag=%smin' %(A,CN, S, Ia, Imp,TC*.6)
    aPacum = np.cumsum(blalt[1,:])
    vRetPot = np.vectorize(potRet)

    aPeAc = vRetPot(aPacum, S, Ia,CN,Imp)
    aPe = np.add(np.append(aPeAc[0],np.diff(aPeAc)),(Imp/100.0)*blalt[1,:])
    aLoss = np.subtract(blalt[1,:],aPe)

    ind = blalt[0,:]

    ## SCS UH
    Tlag = 0.6*TC
    Tp = (DT/2.0)+Tlag
    qp = (2.08*A)/(Tp/60.0)
    print Tp, qp
    UH = np.vstack((t_tp*Tp,q_qp*qp))
    PeT= np.vstack((blalt[0,:],aPe))
    UHDT = interpola_dt(DT,UH)
    rows = PeT.shape[0]
    cols = PeT.shape[1]

    ### IGUALAR O TAMANHO DAS MATRIZES UHDT E PRECIP, PARA MULTIPLICAR
    if UHDT.shape[1]<PeT.shape[1]:
        nVal = PeT.shape[1]-UHDT.shape[1]
        primVal = UHDT[0][-1]+DT
        ultVal = nVal*DT+primVal
        tCompl = np.arange(primVal,ultVal,DT)
        new_t = np.append(np.copy(UHDT[0,:]),tCompl)
        new_q = np.copy(UHDT[1,:])
        new_q.resize(PeT.shape[1], refcheck=False)
        UHDT = np.vstack((new_t,new_q))

    ### FAZ UMA LISTA COM TODOS OS HIDROGRAMAS UNITARIOS    
    lstUHs = []
    for l in xrange(cols):
        at = PeT[0][l]+UHDT[0,:]
        aQ = UHDT[1,:]*PeT[1][l]/10
        UHat = np.vstack((at,aQ))
        #print l,UHat
        lstUHs.append(UHat)

    ### SOMA TODOS OS HIDROGRAMAS, A CADA PASSO DE TEMPO
    tamQ = np.append(ind,np.arange(ind[-1]+DT,roundup(np.amax(lstUHs[-1], axis=1)[0],DT)))
    aHidroF = np.vstack([tamQ, np.zeros(tamQ.shape[0])])
    for d in tamQ:
        soma = 0
        for mat in lstUHs: 
            if mat[0][0]<=d:    #se a matriz comeca antes do tempo d
                soma += np.sum(mat[1,np.where(mat[0]==d+DT)])            
        #print 't=%s / Qtot=%s'%(d, soma)
        aHidroF[1,np.where(aHidroF[0]==d)]=soma

    ### INTERPOLA ZEROS PERDIDOS
    aHidroF = trataCurva(aHidroF)

    ## ENCHE DE ZERO ATÉ FICAR COM O TAMANHO DA MATRIZ DE VAZOES
    aLoss2 = np.copy(aLoss)
    aLoss2.resize(aHidroF[1,:].shape, refcheck=False)
    aPe.resize(aHidroF[1,:].shape, refcheck=False)
    aP = np.copy(blalt[1,:])
    aP.resize(aHidroF[1,:].shape, refcheck=False)
    aVolmm = ((np.copy(aHidroF[1,:])*(DT*60.0))/(A*(1000000.0)))*1000
    aVolm3 = np.copy(aHidroF[1,:])*(DT*60.0)
    aTab =np.column_stack((aHidroF[0,:]/60.0,aP,aLoss2,aPe,aHidroF[1,:],aVolmm))

    return aTab,blalt,aLoss,aHidroF,DT,aVolm3


def geraPlot(nome, blalt,aLoss,aHidroF,DT,aVolm3):
    ind = blalt[0,:]
    a = blalt[1,:]
    b = aLoss
    hid = aHidroF

    fig = plt.figure()
    gs = gridspec.GridSpec(2, 1, height_ratios=[1, 2])
    ax = plt.subplot(gs[1])

    ax.plot(hid[0],hid[1])
    ax.set_ylabel(u'Q(m³/s)', color='b')
    ax.set_xlabel('Tempo (min.)')
    ax.tick_params(axis='y', colors='b')

    xMax, yMax = hid[:,np.argmax(hid[1])]
    yMax = round(yMax,2)
    if int(yMax/10)<1:
        yMaxM = 1
    else:
        yMaxM = int(yMax/10)

    yLimM = roundup(yMax*1.2,yMaxM)
    ax.set_ylim([0,yLimM])
    xLimM = roundup(np.max(hid[0])*1.1,10)
    ax.set_xlim([0,xLimM])
    propX = xMax/hid[0][-1]
    propY = yMax/yLimM

    hr = '%d:%d'%(trunc(xMax //60),trunc(xMax-trunc(xMax //60)*60))
    txtQ = u't=%shs\n %smin\nQmax=%sm³/s'%(hr,xMax,yMax)
    ax.annotate(txtQ, xy=(xMax, yMax),  xycoords='data',
                xytext=(propX+.02, propY+.15), textcoords='axes fraction',
                arrowprops=dict(facecolor='black', shrink=0.005,width=.08),
                horizontalalignment='left', verticalalignment='top',
                )
    ax.annotate('Volume Total=\n'+str(round(np.sum(aVolm3),2))+u'm³',xy=(xLimM*.98,yLimM*.98),horizontalalignment='right',verticalalignment='top')

    #ax.set_xticks(hid[0])
    ax.set_xticklabels(hid[0])
    ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
    ax.xaxis.grid(b=True, which='major', color='.7', linestyle='-')
    ax.yaxis.grid(b=True, which='major', color='.7', linestyle='-')


    ax2 = plt.subplot(gs[0])
    #ax2 = ax.twinx()
    size = fig.get_size_inches()*fig.dpi
    #width = (size/roundup(np.max(hid[0])*1.1,10))[0]*10
    #print 'width=%s'%width
    ax2.bar(ind, a, DT, color='#b0c4de',edgecolor = "none")
    ax2.bar(ind, b, DT, color='#deb0b0',edgecolor = "none")
    yMax2 = round(np.max(a),2)
    yLimM2 = roundup(yMax2,1)
    ax2.set_ylim([0,yLimM2])
    ax2.set_xlim([0,roundup(np.max(hid[0])*1.1,10)])
    ax2.xaxis.grid(b=True, which='major', color='.7', linestyle='-')
    ax2.yaxis.grid(b=True, which='major', color='0.7', linestyle='-')
    ax2.set_ylabel('P(mm)')

    plt.setp(ax2.get_xticklabels(), visible=False)
    #ax2.axes.get_xaxis().set_visible(False)
    plt.tight_layout()
    #ax.xticks(rotation='80')
    ax2.invert_yaxis()
    plt.gcf().subplots_adjust(bottom=0.15)
    plt.savefig(nome,format='pdf')
    plt.close(fig)


'''        
###########  DADOS DE ENTRADA
A = .1492  #km2
TC = 25 #min
TR = 25.0
DUR= 240.0 #min
DT = 1.0    #min
idf =[1133.836,.183,20.667,0.807]
CN = 68.0
Imp = 0.0
##############################

idf =[1133.836,.183,20.667,0.807]
A,TC,TR,DUR,DT,CNIni,Imp = get_data()
aTab,blalt,aLoss,aHidroF,DT,aVolm3 = geraHidro(A,TC,TR,DUR,DT,CNIni,Imp,idf)
### GRAVA TABELA EM CSV
escreveCSV(A,CNIni,Imp,TC,TR,idf,DUR,DT,aTab)
#########PLOT
geraPlot(blalt,aLoss,aHidroF,DT,aVolm3)
'''
