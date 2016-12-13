__author__ = 'blee13'
import pandas as pd
import numpy as np
from Scheduler.Scheduler import Scheduler
from datetime import datetime, timedelta
from MonteCarloSimulators.Vasicek.vasicekMCSim import MC_Vasicek_Sim

class IRSwap(object):
    def __init__(self, startDate, endDate, referenceDate, effectiveDate, freq, notional, recovery=0.4):
        """
            effective date is the start of the payments, startDate is when the contract is entered, endDate is maturity
            referenceDate is the date when the PV is taken
            We are paying a fixed rate to receive a floating rate
        """
        self.recovery=recovery
        self.simNum = 10
        self.xR = []
        self.xQ = []
        # use MC to generate scenarios for exposure
        self.mcSim = MC_Vasicek_Sim()
        #self.mcSim.setVasicek(minDay=startDate,maxDay=endDate,x=xR,t_step=1.0/365, simNumber=self.simNum)
        # z is discount curve
        self.zCurve =[]
        self.swapRate = []
        self.freq = freq
        self.notional=notional
        self.fixedLeg = []
        self.floatingLeg = []
        self.startDate = startDate
        self.endDate = endDate
        self.referenceDate = referenceDate
        self.effctiveDate = effectiveDate
        self.initialSpread =[]
        self.myScheduler = Scheduler()
        self.datelist = pd.date_range(start=effectiveDate,end=endDate, freq=freq)

    def getScheduleComplete(self):
        self.datelist = self.myScheduler.getSchedule(start=self.startDate,end=self.endDate,freq=self.freq,referencedate=self.referenceDate)
        self.ntimes = len(self.datelist)
        fullset = sorted(set(self.datelist)
                                   .union([self.referenceDate])
                                   .union([self.startDate])
                                   .union([self.endDate])
                                   .union([self.referenceDate])
                                   )
        return fullset,self.datelist

    def setLibor(self,libor):
        self.zCurve = libor/libor.loc[self.referenceDate]

    def setxR(self,xR):
        self.xR = xR
        self.mcSim.setVasicek(minDay=self.startDate, maxDay=self.endDate, x=xR, t_step=1.0 / 365, simNumber=self.simNum)

    def setSwapRate(self):
        # getting initial spread at time zero
        floatLegPV= (self.zCurve.loc[self.effctiveDate,0]) - (self.zCurve.loc[self.endDate,0])
        fixedLegPV=0
        delta = (self.datelist[1]-self.datelist[0]).days/365
        for payDate in self.datelist:
                fixedLegPV += delta*self.zCurve.loc[payDate.date(),0]
        swapRate = floatLegPV/fixedLegPV
        self.swapRate = swapRate
        return

    def setCashFlows(self):
        fixedLegCF = np.ones(len(self.datelist))*self.swapRate
        floatLegCF=[]
        delta = (self.datelist[1] - self.datelist[0]).days / 365
        for payDate in self.datelist:
            if payDate.date()==self.endDate:
                floatLegCF.append(((self.zCurve.loc[payDate.date(),0]/self.zCurve.loc[payDate.date()+timedelta(delta*365),0])-1)/delta)
            else:
                floatLegCF.append((self.zCurve.loc[payDate.date(),0]/self.zCurve.loc[(payDate+1).date(),0] - 1)/delta)
        fixedLegCF = pd.DataFrame(data=fixedLegCF,index=self.datelist)
        floatLegCF = pd.DataFrame(data=floatLegCF,index=self.datelist)
        self.fixedLeg = fixedLegCF
        self.floatingLeg = floatLegCF
        return

    def getExposure(self):
        fullDate = pd.date_range(start=self.startDate,end=self.endDate, freq=self.freq)
        EE = np.zeros((len(fullDate), self.simNum))
        for i in range(0, self.simNum):
            zCurveNew = self.mcSim.getLibor()
            row = 0
            for day in fullDate:
                if day<self.datelist[0]:
                    npv = (np.sum((self.floatingLeg-self.fixedLeg).values.ravel()*zCurveNew.loc[self.datelist,0].values))
                elif day>=self.datelist[0] and day<self.datelist[-1]:
                    fixedPartial = self.fixedLeg.loc[day.date():]
                    floatPartial = self.floatingLeg.loc[day.date():]
                    npv = (np.sum((floatPartial-fixedPartial).values.ravel()*zCurveNew.loc[fixedPartial.index,0].values))
                else:
                    npv = 0
                if npv < 0:
                    npv = 0
                EE[row,i] = npv
                row+=1
        EE = pd.DataFrame(data=EE, index=fullDate)
        self.fullDate = fullDate
        self.fullExposure = EE
        self.avgExposure = EE.mean(axis=1)
        return

    def getCVA(self, survCurve):
        # CVA = LGD * EE * PD * Discount, LGD =1-R
        CVA = self.notional * (1-self.recovery) * self.avgExposure.values * survCurve.loc[self.fullDate,self.freq].values * self.zCurve.loc[self.fullDate,0].values
        CVA = pd.DataFrame(data= CVA, index=self.fullDate)
        self.CVA =CVA
        return
