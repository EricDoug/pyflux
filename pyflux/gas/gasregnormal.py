import sys
if sys.version_info < (3,):
    range = xrange

import numpy as np
import pandas as pd
import scipy.stats as ss
import matplotlib.pyplot as plt
import seaborn as sns

from ..parameter import Parameter, Parameters
from .. import inference as ifr
from .. import tsm as tsm
from .. import distributions as dst
from .. import data_check as dc

from .scores import *
from .gasreg import *

class GASRegNormal(GASReg):
    """ Inherits time series methods from TSM class.

    **** GAS NORMAL REGRESSION MODELS ****

    Parameters
    ----------

    formula : string
        patsy string describing the regression

    data : pd.DataFrame or np.array
        Field to specify the data that will be used
    """

    def __init__(self,formula,data):

        # Initialize TSM object     
        super(GASRegNormal,self).__init__(formula=formula,data=data)

        self.model_name = "Normal-distributed GAS Regression"
        self.dist = 'Normal'
        self.link = np.array
        self.scale = True
        self.shape = False

        for parm in range(len(self.parameters.parameter_list)):
            self.parameters.parameter_list[parm].start = -9.0

        self.parameters.add_parameter('Normal Scale',ifr.Uniform(transform='exp'),dst.q_Normal(0,3))

        self.param_no += 1

    def score_function(self,X,y,mean,scale,shape):
        return X*(y-mean)

    def draw_variable(self,loc,scale,shape,nsims):
        return np.random.normal(loc, scale, nsims)

    def neg_loglik(self,beta):
        theta, Y, scores,_ = self._model(beta)
        return -np.sum(ss.norm.logpdf(Y,loc=self.link(theta),scale=self.parameters.parameter_list[-1].prior.transform(beta[-1])))

    def predict_is(self,h=5):
        """ Makes dynamic in-sample predictions with the estimated model

        Parameters
        ----------
        h : int (default : 5)
            How many steps would you like to forecast?

        Returns
        ----------
        - pd.DataFrame with predicted values
        """     

        predictions = []

        for t in range(0,h):
            data1 = self.data_original.iloc[:-(h+t),:]
            data2 = self.data_original.iloc[-h+t:,:]
            x = GASRegNormal(formula=self.formula,data=self.data_original[:(-h+t)])
            x.fit(printer=False)
            if t == 0:
                predictions = x.predict(1,oos_data=data2)
            else:
                predictions = pd.concat([predictions,x.predict(h=1,oos_data=data2)])
        
        predictions.rename(columns={0:self.y_name}, inplace=True)
        predictions.index = self.index[-h:]

        return predictions