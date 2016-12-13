__author__ = 'beomlee'
import pandas as pd
import numpy as np
from Scheduler.Scheduler import Scheduler
from MonteCarloSimulators.Vasicek.vasicekMCSim import MC_Vasicek_Sim
from scipy import optimize

class CDS(object):
    def __init__(self, start, end, reference, recovery, rating, notional, freq="1M"):
        self.numSim =10
        self.t_step = 1.0/365
        #z curve is for discounting
        self.zCurve=[]
        #q curve is for survival prob of the reference entity
        self.qCurve=[]
        self.start=start
        self.end =end
        self.reference = reference
        self.freq=freq
        self.rating = rating
        self.notional = notional
        # mcSim used for simulating default prob, interest rate
        # xR should already be calibrated
        self.xR = []
        # xQ we need to calibrate inside CDS
        self.xQ = []
        self.mcSim = MC_Vasicek_Sim()
        self.mcSimSurvival = MC_Vasicek_Sim()

        #self.mcSim.setVasicek(minDay=startDate, maxDay=endDate, x=xR, t_step=1.0 / 365, simNumber=self.simNum)
        #self.mcSimSurvival.setVasicek(minDay=startDate, maxDay=endDate, x=xR, t_step=1.0 / 365, simNumber=self.simNum)

        self.dateList = pd.date_range(start=start,end=end,freq=freq)
        self.recovery =recovery

    def setCorpData(self, corpData):
        self.corpData = corpData.loc[self.rating,:,"1 MO"]

    def setLibor(self,libor):
        self.zCurve = libor/libor.loc[self.reference]

    def setxR(self,xR):
        self.xR = xR
        self.mcSim.setVasicek(minDay=self.start, maxDay=self.end,x=self.xR, simNumber=self.numSim, t_step=self.t_step)

    def setxQ(self,xQ):
        res = optimize.fmin(func=self.mcSimSurvival.errorFunction, x0=np.array([xQ[0],xQ[1]]), args=(self.corpData.values[:-1], self.corpData.values[1:], self.t_step))
        xQSigma = np.std(self.corpData.values[:-1]- self.corpData.values[1:])
        self.xQ = np.append(res,np.array([xQSigma,xQ[3]]))
        self.mcSimSurvival.setVasicek(minDay=self.start, maxDay=self.end, x=self.xQ, simNumber=self.numSim, t_step=self.t_step)

    def setQCurve(self):
        self.qCurve = self.mcSimSurvival.getLibor().loc[:,0]
        return

    def getDefaultLegPV(self):
        interimSum = 0
        for payDates in self.dateList[1:]:
            interimSum += self.zCurve.loc[payDates.date(),0]*(self.qCurve.loc[(payDates-1).date()] -
                                                              self.qCurve.loc[payDates.date()])
        defaultLeg = (1-self.recovery)*interimSum
        return defaultLeg

    def getFeeLegPV(self):
        delta = (self.dateList[1] - self.dateList[0]).days/365
        interimSum =0
        for payDate in self.dateList[1:]:
            interimSum += self.zCurve.loc[payDate.date(), 0]*delta*(self.qCurve.loc[(payDate-1).date()] +
                                                                    self.qCurve.loc[payDate.date()])
        feeLeg = 0.5*interimSum
        return feeLeg
    def getSpread(self):
        spread = self.getDefaultLegPV()/self.getFeeLegPV()
        self.spread=spread
        return spread

    def setCF(self):
        feeLegCF = np.ones(len(self.dateList)) * self.spread
        defaultLegCF = np.ones(len(self.dateList))*(1-self.recovery)*self.qCurve.loc[self.dateList].values
        self.feeLeg = pd.DataFrame(data=feeLegCF, index=self.dateList)
        self.defaultLeg = pd.DataFrame(data=defaultLegCF, index=self.dateList)
        return

    def getExposure(self):
        #PV of protection leg - fee leg
        #use survivalCurve passed in as the survival prob of the reference entitity
        #simulate the default probability of the counterparty - newQcurve
        fullDate = pd.date_range(start=self.start,end=self.end,freq=self.freq)
        EE = np.zeros((len(self.dateList), self.numSim))
        for i in range(0, self.numSim):
            row=0
            newZCurve = self.mcSim.getLibor()
            newQCurve = self.mcSimSurvival.getLibor()
            survivalCurve = self.qCurve
            for day in fullDate:
                if day == fullDate[0]:
                    #feePV - pay fee as long as counter and reference do not default
                    feePV = np.transpose(self.feeLeg.values).ravel()*newZCurve.loc[self.dateList,0].values*survivalCurve.loc[self.dateList].values*newQCurve.loc[self.dateList,0].values
                    #defaultPV - recover a portion of the notional given the refernce defaults and the counterparty does NOT
                    defaultPV = (1-self.recovery)*np.transpose(self.defaultLeg.values).ravel()*self.zCurve.loc[self.dateList,0].values*(np.ones(len(self.dateList))-survivalCurve.loc[self.dateList].values)*newQCurve.loc[self.dateList,0].values

                elif day>fullDate[0] and day<fullDate[-1]:
                    partialFee = self.feeLeg.loc[day.date():]
                    partialDefault = self.defaultLeg.loc[day.date():]
                    feePV = np.transpose(partialFee.values).ravel() * newZCurve.loc[partialFee.index, 0].values * survivalCurve.loc[
                        partialFee.index].values * newQCurve.loc[partialFee.index, 0].values
                    defaultPV = (1-self.recovery) * np.transpose(partialDefault.values).ravel() * self.zCurve.loc[partialFee.index, 0].values * (
                    np.ones(len(partialFee.index)) - survivalCurve.loc[partialFee.index].values) * newQCurve.loc[
                        partialFee.index, 0].values
                else:
                    feePV = 0
                    defaultPV = 0
                npv = np.sum(defaultPV - feePV)
                if npv<0:
                    npv =0
                EE[row, i] = npv
                row +=1
        EE = pd.DataFrame(data=EE, index=fullDate)
        self.fullDate = fullDate
        self.fullExposure = EE
        self.avgExposure = EE.mean(axis=1)
    def getCVA(self):
        self.CVA = self.notional * (1-self.recovery) * self.avgExposure.values * self.zCurve.loc[self.fullDate,0].values * self.qCurve.loc[self.fullDate].values
        return