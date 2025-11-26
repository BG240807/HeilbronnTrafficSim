from typing import Dict
import logging

class HybridServer:
    def __init__(self, matsim_runner, sumo_runner):
        self.matsim = matsim_runner
        self.sumo = sumo_runner

    def reintegrate(self, matsim_res, micro_results: Dict):
        # For each MATSim link, if micro result is available, compute corrected travel time multiplier
        corrections = {}
        for link in matsim_res.get('link_stats', []):
            lid = link.get('linkId')
            if lid in micro_results:
                micro = micro_results[lid]
                # simplistic: corrected_tt = original_tt + micro.avg_delay
                try:
                    orig_tt = float(link.get('time', 0))
                except:
                    orig_tt = 0
                corrected = orig_tt + float(micro.get('avg_delay', 0))
                corrections[lid] = {'orig': orig_tt, 'corrected': corrected}
        return corrections