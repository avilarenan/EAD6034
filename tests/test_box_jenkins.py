import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.stats.diagnostic import acorr_ljungbox
from ead6034.segmented_arma import SegmentedARMA, min_root
from ead6034.box_jenkins import residual_correlogram, training_frames
from test_multiscale import _complete_minutes


class TestSegmentedLikelihood(unittest.TestCase):
    def test_matches_independent_kalman_likelihood_with_short_segments(self):
        rng=np.random.default_rng(46034)
        segments=[rng.normal(size=n) for n in [2,3,25,35]]
        model=SegmentedARMA(segments)
        ar,ma=np.array([.3,-.1]),np.array([.15,.07,-.06])
        ll,mu,s2=model.profile(ar,ma)
        reference=sum(SARIMAX(y-mu,order=(2,0,3),trend="n").loglike(np.r_[ar,ma,s2]) for y in segments)
        self.assertAlmostEqual(ll,reference,places=7)

    def test_segment_permutation_preserves_likelihood(self):
        rng=np.random.default_rng(77)
        x=[rng.normal(size=n) for n in [17,35,25]]
        a=SegmentedARMA(x).profile([.4],[.2])
        b=SegmentedARMA([x[2],x[0],x[1]]).profile([.4],[.2])
        np.testing.assert_allclose(a,b,atol=1e-12)

    def test_changing_one_segment_does_not_change_other_innovations(self):
        rng=np.random.default_rng(67)
        x=[rng.normal(size=25),rng.normal(size=25)]
        model=SegmentedARMA(x)
        fit=model.fit(1,0,starts=1)
        original=model.residuals(fit)[1]
        other=SegmentedARMA([x[0]+100,x[1]]).residuals(fit)[1]
        np.testing.assert_array_equal(original,other)

    def test_white_noise_solution_and_parameter_penalty(self):
        x=[np.array([1.,2.,3.]),np.array([-2.,4.])]
        fit=SegmentedARMA(x).fit(0,0)
        self.assertAlmostEqual(fit.mu,np.concatenate(x).mean())
        self.assertAlmostEqual(fit.sigma2,np.concatenate(x).var())
        self.assertEqual(fit.k,2)
        self.assertAlmostEqual(fit.bic,-2*fit.llf+2*np.log(5))

    def test_transformation_enforces_stationarity_and_invertibility(self):
        raw=np.random.default_rng(6034).normal(size=10)
        ar,ma=SegmentedARMA.transform(raw,5)
        self.assertGreater(min_root(ar),1)
        self.assertGreater(min_root(ma,ar=False),1)


class TestPortmanteau(unittest.TestCase):
    def test_reduces_to_ordinary_ljungbox_for_one_series(self):
        x=np.random.default_rng(34).normal(size=150)
        result=residual_correlogram([x],10)
        reference=acorr_ljungbox(x,lags=list(range(1,11)))
        np.testing.assert_allclose(result.q,reference.lb_stat,rtol=1e-10)

    def test_pair_counts_exclude_session_boundaries(self):
        x=[np.array([1.,4.,2.,3.]),np.array([-5.,2.,1.,8.])]
        result=residual_correlogram(x,3)
        self.assertEqual(result.valid_pairs.tolist(),[6,4,2])
        np.testing.assert_allclose(result.acf,residual_correlogram(x[::-1],3).acf)


class TestHoldoutIsolation(unittest.TestCase):
    def test_poisoned_future_cannot_change_training_or_coverage(self):
        training=_complete_minutes([("2024-01-02","WING24",100000.)])
        future=_complete_minutes([("2025-01-02","WING25",200000.)])
        future.loc[:,"close"]=-1.  # Would fail the audit if the holdout entered it.
        contaminated=pd.concat([training,future],ignore_index=True)
        with patch("ead6034.box_jenkins.load_win_minutes",return_value=(training,{})):
            first,coverage,_=training_frames("unused")
        with patch("ead6034.box_jenkins.load_win_minutes",return_value=(contaminated,{})):
            second,other_coverage,_=training_frames("unused")
        pd.testing.assert_frame_equal(coverage,other_coverage)
        for scale in first:
            pd.testing.assert_frame_equal(first[scale],second[scale])


if __name__=="__main__":
    unittest.main()
