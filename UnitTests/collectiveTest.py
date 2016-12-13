from Products.Rates.CouponBond import *
from Products.Credit.CDS import *
from Products.Credit.IRSwap import *
from MonteCarloSimulators.Vasicek.vasicekMCSim import *
from scipy import optimize
from Curves.Corporates.CorporateDaily import *
from Scheduler.Scheduler import *
from parameters import *
import numpy as np
import pandas as pd

periods = '1Y'
freq = '1M'
t_step = 1.0 / 365.0
simNumber = 10
counterPartyRating = "AAA"

# length of OIS curve we get from FRED
trim_start= date(2000,1,1)
trim_end=date(2010, 12,13)

#contract start date end date
startDate = date(2000,6,30)
referenceDate = date(2000, 7, 31)
effectiveDate = date(2000,9,30)
endDate = date(2002,6, 30)
datelist = pd.date_range(start=startDate,end=endDate,freq=freq)

# kappa theta sigma r_0  and recovery rate as given in the final project description
xR = [3.0, 0.05, 0.09, 0.08]
xQ = [0.1,0.05,0.13,0.2]
R = 0.4

# term struct curve use for discounting/calibrating
myOIS = OIS()
zCurve = myOIS.getOIS()

#survival rate curve for counter Party - survival curve for reference entity will be within each product
#in proxy of CDS spreads, will use corporate bond spreads 1MO
myCorp=CorporateRates()
corporateData = myCorp.getCorporatesFred(trim_start,trim_end)
qCounterParty = myCorp.getCorporateQData(rating=counterPartyRating, datelist=datelist)

#create simulator for interest rates and survival curve
myMCDiscount = MC_Vasicek_Sim()
myMCSurvival = MC_Vasicek_Sim()

#calibrating vasicek params - use 1MO OIS
rateCurve = zCurve.loc["1 MO"].values
offsetRateCurve = rateCurve[1:]
res = optimize.fmin(func = myMC.errorFunction, x0=np.array([xR[0], xR[1]]), args=(rateCurve[:-1],offsetRateCurve))
calibSigma = np.stdev(rateCurve[:-1] - offsetRateCurve)
calibratedVasicekParams = np.array([res, calibSigma, xR[3]])
myMCDiscount.setVasicek(minDay=startDate,maxDay=endDate, x=calibratedVasicekParams, simNumber=simNumber, t_step=t_step)

