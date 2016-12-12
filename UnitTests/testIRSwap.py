__author__ = 'blee13'
from unittest import TestCase
from MonteCarloSimulators.Vasicek.vasicekMCSim import MC_Vasicek_Sim
from Products.Rates.CouponBond import CouponBond
from Curves.Corporates.CorporateDaily import CorporateRates
from Scheduler.Scheduler import Scheduler
import matplotlib.pyplot as plt
from Products.Credit.IRSwap import IRSwap
import pandas as pd
from datetime import date


myScheduler = Scheduler()
periods = '1Y'
freq = '1M'
t_step = 1.0 / 365.0
simNumber = 10
trim_start = date(2000, 1, 1)
trim_end = date(2000, 12, 31)
trim_endMC = date(2001, 12, 31)
effDay = date(2000, 4, 1)
referenceDate = date(2000, 1, 1)
testSched = pd.date_range(trim_start,trim_start)
scheduleComplete = pd.date_range(start=trim_start,end=trim_end)
xR = [3.0, 0.05, 0.04, 0.03]
datelist = myScheduler.getSchedule(start=trim_start, end=trim_end, freq=freq, referencedate=referenceDate)
myMC = MC_Vasicek_Sim()
myMC.setVasicek(x=xR, minDay=trim_start, maxDay=trim_endMC, simNumber=simNumber, t_step=t_step)
myMC.getLibor()
myCorp = CorporateRates()
myCorp.getCorporatesFred(trim_start,trim_end)
testRatings = myCorp.getCorporateData("AAA",testSched)
testSurvival = myCorp.getCorporateQData("AAA",scheduleComplete,0.4)

mySwap = IRSwap(zCurve=myMC.getLibor(),startDate=trim_start,endDate=trim_end,referenceDate=referenceDate,effectiveDate=effDay, rating="AAA", freq=freq, notional=1000, xR= xR)
initSpread = mySwap.setSwapRate()
mySwap.setCashFlows()
mySwap.getExposure()
mySwap.getCVA(testSurvival)
a=1