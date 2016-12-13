from datetime import date
from unittest import TestCase
from scipy import optimize
import numpy as np
import pandas as pd
from MonteCarloSimulators.Vasicek.vasicekMCSim import MC_Vasicek_Sim
from Curves.Corporates.CorporateDaily import CorporateRates, OIS


from parameters import WORKING_DIR

periods = '1Y'
freq = '1M'
t_step = 1.0 / 365.0
simNumber = 10
start = date(2005, 3, 30)
trim_start = date(2000, 1, 1)
trim_end = date(2000, 12, 31)
referenceDate = date(2005, 3, 30)

# kappa theta sigma r_0
xR = [3.0, 0.05, 0.09, 0.08]
xQ = [0.1,0.05,0.13,0.2]
# CashFlow Dates
myMC = MC_Vasicek_Sim()
myMC.setVasicek(minDay=trim_start,maxDay=trim_end,x=xR,simNumber=simNumber, t_step=t_step)
testSched = pd.date_range(trim_start,trim_start)
scheduleComplete = pd.date_range(start=trim_start,end=trim_end)
myCorp = CorporateRates()
myCorp.getCorporatesFred(trim_start,trim_end)
myCorp.OIS = OIS()
myCorp.OIS.getOIS()
rateCurve = myCorp.OIS.OIS.loc[:,"1 MO"].values
rateCurveOffset = rateCurve[1:]
rateCurveOffset = np.append(rateCurveOffset,rateCurve[-1])
res = optimize.fmin(func = myMC.errorFunction, x0=np.array([3, 0.05]), args=(rateCurve,rateCurveOffset))
xR[0],xR[1] = res
xR[2] = np.std(rateCurveOffset-rateCurve)

a=1
'''testRatings = myCorp.getCorporateData("AAA",testSched)
testSurvival = myCorp.getCorporateQData("AAA",scheduleComplete,0.4)
myCorp.getSimCurve(x=xQ,minDay=trim_start, maxDay=trim_end, simNum=simNumber, tStep=t_step)
print(myCorp.simCurve)
xQ_Calibrated = myCorp.calibrate(testSurvival.loc[:,"1 MO"])
myCorp.pickleMe()'''



class TestCorporateRates(TestCase):
    def test_getOIS(self):
        OIS = myCorp.getOISData(datelist=scheduleComplete)
        print('AAA', np.shape(OIS))

    def test_getCorporateData1(self):
        AAA = myCorp.getCorporateData(rating='AAA')
        print(np.shape(AAA))

    def test_getCorporateData2(self):
        OIS = myCorp.getCorporateData(rating='OIS', datelist=scheduleComplete)
        print('OIS', np.shape(OIS))

    def test_pickleMe(self):
        return
        fileName = WORKING_DIR + '/myCorp'
        myCorp.pickleMe(fileName)

    def test_unPickleMe(self):
        fileName = WORKING_DIR + '/myCorp.dat'
        myCorp.unPickleMe(fileName)

    def test_saveMeExcel(self):
        fileName = WORKING_DIR + '/myCorp.xlsx'
        myCorp.saveMeExcel(whichdata=myCorp.corporates, fileName=fileName)
