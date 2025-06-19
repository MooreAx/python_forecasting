#class for listings

from datetime import datetime
from globals import *

import pandas as pd
from statsmodels.tsa.holtwinters import SimpleExpSmoothing

class Listing:
    def __init__(self, part, prov, actuals_type,
                 loadin, loadzeros, launchpush, input_baseline, input_start, input_exit,
                 lor1, lor2, lor3, lor4, lor5, lor6,
                 lifecycle_name, lifecycle, lifecycle_start,
                 promo_name, promo, promo_start,
                 season_name, season, season_start,
                 shipments, depletions, first_ship, last_ship):
        self.part = part
        self.prov = prov
        self.short_status = None
        self.long_status = None
        self.actuals_type = actuals_type
        self.loadin = loadin
        self.loadzeros = loadzeros

        #lors
        self.lors = [lor1, lor2, lor3, lor4, lor5, lor6]
        self.cleaned_lors = []

        self.launchpush = launchpush
        self.input_baseline = input_baseline
        
        self.input_start = input_start
        if pd.isna(self.input_start):
            self.input_start = MINDATE
    
        self.input_exit = input_exit
        if isinstance(self.input_exit, str) and self.input_exit == "Past":
            self.input_exit = MINDATE  # arbitrary past date
        elif pd.isna(self.input_exit):
            self.input_exit = MAXDATE  # arbitrary future date

        
        self.season_name = season_name
        self.season = season
        self.season_start = season_start

        self.lifecycle_name = lifecycle_name
        self.lifecycle_name = lifecycle        
        self.lifecycle_start = lifecycle_start
        
        self.promo_name = promo_name
        self.promo = promo
        self.promo_start = promo_start
        
        self.shipments = shipments
        self.depletions = depletions
        
        self.n_shipments = len(self.shipments) if not self.shipments.empty and self.shipments is not None else 0
        self.n_depletions = len(self.depletions) if not self.depletions.empty and self.shipments is not None else 0

        self.first_ship = first_ship
        self.last_ship = last_ship

        self.pos = []

        #initialize params
        self.calc_baseline = None
        self.calc_exit = None

        #initialize outputs
        self.fc = []
        self.log = ""

        #register this listing with its parent part
        self.part.listings.append(self)

        self._calculate_status()
        self._clean_lors()


    def _calculate_status(self):

        # status preprocessing
        exit_future = self.input_exit > FCSTART
        exit_past = self.input_exit < FCSTART
        start_future = self.input_start >= FCSTART
        start_now = self.input_start == CURRENTWK
        start_past = self.input_start < CURRENTWK
        no_ship = self.first_ship is None
        planned_exit = self.input_exit == MAXDATE
        
        if self.part.pstatus == "X":
            self.short_status = "X"
            self.long_status = "X - product unavailable"
        
        elif no_ship and exit_future:
            # No shipment, still in future
            self.short_status = "NPD"
            if start_future:
                self.long_status = "NPD - future launch"
            elif start_now:
                self.long_status = "NPD - launch now"
            elif start_past:
                self.long_status = "NPD - late launch"
            else:
                raise ValueError(f"Unable to calculate status for {self.part.name}{self.prov}")

        elif exit_past:
            # Exit in past
            self.short_status = "X"
            self.long_status = "X - never shipped" if no_ship else "X - historical"
        
        elif start_past and exit_future and not no_ship:
            # Active
            age_weeks = (CURRENTWK - self.first_ship).days // 7
            maturity = "NPD" if age_weeks <= 12 else "mature"
            permanency = "exiting" if planned_exit else "permanent"
            self.short_status = "Active"
            self.long_status = f"Active - {maturity} - {permanency}"
        
        else:
            raise ValueError(f"Unable to calculate status for {self.part.name}{self.prov}")

    def calculate_baseline(self):
        self.depletions_baseline = self._run_ses("Depletions")
        self.shipments_baseline = self._run_ses("Shipments")

        if self.short_status == "X":
            self.calc_baseline = "na"
            return

        if not pd.isna(self.input_baseline):
            self.calc_baseline = self.input_baseline
        elif self.actuals_type == "Depletions":
            self.calc_baseline = self.depletions_baseline
        elif self.actuals_type == "Shipments":
            self.calc_baseline = self.shipments_baseline
        else:
            raise ValueError(f"Invalid actuals_type for listing {self.part.name}{self.prov}: {self.actuals_type}")

    def _run_ses(self, demandtype):

        #run ses
        #convert depletions to time series

        if demandtype == "Depletions":
            demand = self.depletions
        elif demandtype == "Shipments":
            demand = self.shipments
        else:
            #throw error
            #might be better to continue running, and to append this to log?
            raise ValueError(f"Invalid actuals_type for listing {self.part.name}{self.prov}: {self.actuals_type}")

        forecast_value = "na"  # default if forecast fails or no data

        try:
            ts_dep = (
                demand
                .set_index('sow')
                .asfreq('W-MON')  # explicitly assign weekly frequency
                ['demand']
            )
            if len(ts_dep) >= 3:  # minimum data to fit SES
                model = SimpleExpSmoothing(ts_dep).fit(smoothing_level=0.3, optimized=False)
                forecast = model.forecast(1)
                forecast_value = round(forecast.iloc[0])
        except Exception:
            forecast_value = "na"

        return forecast_value


    def _clean_lors(self):   
        for lor in self.lors:
            if not pd.isna(lor):
                self.cleaned_lors.append(int(lor))
            else:
                return
        

    def apply_profile(self):
        #initially make this specific to seasonality, then generalize.

        #for error flags:
        has_name = not pd.isna(self.season_name)
        has_profile = self.season is not None
        has_start = not pd.isna(self.season_start)

        if not has_name:
            #no profile, exit
            return
        elif has_name and not has_profile:
            self.addtolog(f"[ERROR]: profile {self.season_name} not defined")
            return
        elif has_name and not has_start:
            self.addtolog(f"[WARNING]: no season start; starting at {FCSTART}")
            self.season_start = FCSTART

        adjusted_fc = []
        for fc_week, fcvalue, fctype in self.fc:

            if fctype == "loadin":
                newfc = fcvalue
            else:
                diff_weeks = (fc_week - self.season_start).days // 7
                profile_index = diff_weeks % len(self.season)
                newfc = fcvalue * self.season.loc[profile_index, self.season_name]
            
            adjusted_fc.append((fc_week, newfc, fctype))

        self.fc = adjusted_fc

    def addtolog(self, message):
        #method to add to log
        self.log += message

    def generate_forecast(self):
        """
        Builds self.fc (forecast series) as a list of (date, units, isloadin) tuples.
        Uses loadin for NPDs, baseline otherwise.
        """

        #inactive SKUs
        if self.short_status == "X":
            #no forecast req'd - return empty list
            return

        #Active SKUs
        if self.short_status == "Active":
            fc_weeks = pd.date_range(start=FCSTART, end=self.input_exit, freq="W-MON")
            forecast = []
            
            if not pd.isna(self.input_baseline):
                # Use input baseline if provided
                baseline = int(self.input_baseline)
            elif self.calc_baseline != "na":
                # No input baseline, use calculated baseline if available
                baseline = int(self.calc_baseline)
            else:
                self.addtolog("[ERROR]: Unable to fc; check baseline.")
                return
            
            for _, week in enumerate(fc_weeks):
                #False means not a loadin
                forecast.append((week, baseline, "baseline"))

            self.fc = forecast
            return
            #need to add something here for Active-NPDs

        #NPDs
        if self.short_status == "NPD":
            if self.long_status == "NPD - late launch":
                if  self.launchpush != "Yes":
                    self.addtolog("[WARNING]: Late launch; consider pushing.")
                elif self.launchpush == "Yes":
                    #push the startdate back to the next available date
                    self.input_start = FCSTART
                    self.addtolog("Late launch; pushing.")

            forecast = []
            fc_weeks = pd.date_range(start=self.input_start, end=self.input_exit, freq="W-MON")

            #check for conflicting loadin info:

            #preprocessing:
            has_lors = len(self.cleaned_lors) > 0
            has_traditional_load = not pd.isna(self.loadin) or not pd.isna(self.loadin)

            if has_lors and has_traditional_load:
                #conflicting inputs
                self.addtolog("[ERROR]: Conflicting NPD loadin data.")
                return
            elif not has_lors and not has_traditional_load:
                #no load inputs
                self.addtolog("[WARNING]: no loadin data.")
            
            if has_lors:
                #use lor data
                for i, week in enumerate(fc_weeks):
                    if i < len(self.cleaned_lors):
                        forecast.append((week, self.cleaned_lors[i], "loadin"))
                    else:
                        forecast.append((week, self.input_baseline, "loadin"))
                self.fc = forecast
                return
            else:
                # Week 1 is loadin, others are baseline
                for i, week in enumerate(fc_weeks):
                    if i == 0 and not pd.isna(self.loadin):
                        forecast.append((week, self.loadin, "loadin"))
                    elif not pd.isna(self.loadzeros) and i <= self.loadzeros:
                        forecast.append((week, 1, "loadin"))
                    else:
                        forecast.append((week, self.input_baseline, "baseline"))
                
                self.fc = forecast
                return
