"""Food Endurance as Deterrence - a stochastic time-to-shortfall model of Taiwan's
food system under blockade scenarios.

Modules
-------
data        : load the calibration tables (MOA food balance sheet, AFA rice survey, MOI population)
params      : prior distributions for uncertain parameters, scenario definitions, Sobol problem
model       : vectorised daily stock-flow simulator (national level)
county      : county-level extension (22 counties/cities) with limited inter-county transfers
survival    : Kaplan-Meier, RMST, Weibull accelerated-failure-time (AFT) estimation
experiments : the experiment grid used in the report (scenarios x levers, onset, phi sweep, Sobol)
plots       : figures (English and Traditional Chinese labels)
"""

__version__ = "1.0.0"
