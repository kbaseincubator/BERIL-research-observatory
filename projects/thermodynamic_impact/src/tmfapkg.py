# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
from math import sqrt
from scipy.constants import R, calorie, kilo, physical_constants
from numpy import log as ln
from modelseedpy.fbapkg.basefbapkg import BaseFBAPkg
from modelseedpy.core.fbahelper import FBAHelper

logger = logging.getLogger(__name__)

FARADAY = physical_constants["Faraday constant"][0]  # C/mol


class TMFAPkg(BaseFBAPkg):
    """TMFA (Henry et al. 2007, Biophys J 92:1792-1805) as a ModelSEEDpy FBA package.

    Two modes:
      A) reaction-level dG from dGPredictor JSON (kJ/mol, pH-corrected)
      B) compound-level dG from ModelSEED Database (kcal/mol, converted to kJ/mol)
    """

    @staticmethod
    def default_concentration():
        return {
            "cpd00067_c0": [1e-7, 1e-7],       # H+ at pH 7
            "cpd00067_e0": [3.16228e-7, 3.16228e-7],  # H+ at pH 6.5
            "cpd00007_c0": [1e-7, 8.2e-6],     # O2 intracellular
            "cpd00011_c0": [1e-8, 0.0014],      # CO2 intracellular
            "cpd00009_e0": [0.056, 0.056],       # phosphate extracellular
            "cpd00048_e0": [0.003, 0.003],       # sulfate extracellular
            "cpd00013_e0": [0.019, 0.019],       # ammonia extracellular
            "cpd00971_e0": [0.16, 0.16],         # sodium extracellular
            "cpd00205_e0": [0.022, 0.022],       # potassium extracellular
            "cpd10515_e0": [0.062, 0.062],       # Fe2+ extracellular
            "cpd00011_e0": [0.0001, 0.0001],     # CO2 extracellular
            "cpd00007_e0": [8.2e-6, 8.2e-6],    # O2 extracellular
            "cpd00027_e0": [0.02, 0.02],         # glucose extracellular
        }

    @staticmethod
    def default_compartment_potential():
        return {"e0": 0, "c0": -160}  # mV

    def __init__(self, model):
        BaseFBAPkg.__init__(
            self,
            model,
            "tmfa",
            {
                "z_fwd": "reaction",
                "z_rev": "reaction",
                "lnconc": "metabolite",
                "dGrxn": "reaction",
                "dGerr": "reaction",
            },
            {
                "flux_fwd": "reaction",
                "flux_rev": "reaction",
                "exclusion": "reaction",
                "dgdecomp": "reaction",
                "thermo_fwd": "reaction",
                "thermo_rev": "reaction",
            },
        )

    def build_package(self, parameters):
        self.validate_parameters(
            parameters,
            [],
            {
                "dg_data": None,
                "modelseed_path": None,
                "temperature": 298.15,
                "default_max_conc": 0.02,
                "default_min_conc": 1e-6,
                "K": None,
                "custom_concentrations": {},
                "compartment_potential": {},
                "filter": None,
                "error_multiplier": 2,
            },
        )

        if self.parameters["dg_data"] is None and self.parameters["modelseed_path"] is None:
            raise ValueError("At least one of 'dg_data' or 'modelseed_path' must be provided")

        # Mode A excludes H+ from lnconc sum (dG_mean already pH-transformed)
        self._exclude_protons = self.parameters["dg_data"] is not None

        if self.parameters["modelseed_path"] is not None:
            self.parameters["_modelseed_api"] = FBAHelper.get_modelseed_db_api(
                self.parameters["modelseed_path"]
            )

        # Merge concentration defaults
        self._concentrations = self.default_concentration()
        self._concentrations.update(self.parameters["custom_concentrations"])

        # Merge compartment potentials
        self._comp_pot = self.default_compartment_potential()
        self._comp_pot.update(self.parameters["compartment_potential"])

        # Auto-compute K from data range
        K = self.parameters["K"]
        if K is None:
            K = self._auto_compute_K()
        self._K = K

        # RT in kJ/mol
        self._RT = R / kilo * self.parameters["temperature"]

        # Build lnconc variables for all metabolites
        for met in self.model.metabolites:
            self._build_lnconc_variable(met)

        # Build TMFA constraints for each reaction
        constrained = 0
        skipped = 0
        for rxn in self.model.reactions:
            if self._build_reaction_tmfa(rxn):
                constrained += 1
            else:
                skipped += 1
        logger.info(f"TMFAPkg: constrained {constrained} reactions, skipped {skipped}")

    def _auto_compute_K(self):
        dg_data = self.parameters["dg_data"]
        if dg_data:
            max_abs_dg = max(
                (abs(entry["dG_mean"]) for entry in dg_data.values()),
                default=10000,
            )
        else:
            max_abs_dg = 10000
        # Add buffer for concentration and error terms
        return max(10000, max_abs_dg * 1.2 + 1000)

    def _build_lnconc_variable(self, met):
        msid = FBAHelper.modelseed_id_from_cobra_metabolite(met)
        if msid == "cpd00001":  # water: activity = 1
            return None
        if self._exclude_protons and msid == "cpd00067":
            return None

        lb = ln(self.parameters["default_min_conc"])
        ub = ln(self.parameters["default_max_conc"])
        if met.id in self._concentrations:
            lb = ln(self._concentrations[met.id][0])
            ub = ln(self._concentrations[met.id][1])
        return BaseFBAPkg.build_variable(self, "lnconc", lb, ub, "continuous", met)

    def _get_reaction_dg(self, rxn):
        """Returns (dG_mean_kJ, dG_std_kJ) or (None, None)."""
        msid = FBAHelper.modelseed_id_from_cobra_reaction(rxn)

        # Mode A: reaction-level dG from JSON
        if self.parameters["dg_data"] is not None:
            if msid and msid in self.parameters["dg_data"]:
                entry = self.parameters["dg_data"][msid]
                return entry["dG_mean"], entry.get("dG_std", 0)
            return None, None

        # Mode B: compound-level dG from ModelSEED DB
        api = self.parameters["_modelseed_api"]
        total_dg = 0.0
        total_var = 0.0
        for met, stoich in rxn.metabolites.items():
            met_msid = FBAHelper.modelseed_id_from_cobra_metabolite(met)
            if met_msid is None:
                return None, None
            mscpd = api.get_seed_compound(met_msid)
            if mscpd is None or mscpd.deltag == 10000000:
                return None, None
            total_dg += stoich * mscpd.deltag * calorie  # kcal → kJ
            if hasattr(mscpd, "deltagerr") and mscpd.deltagerr is not None:
                total_var += (stoich * mscpd.deltagerr * calorie) ** 2
            else:
                total_var += (stoich * 5.0) ** 2  # default 5 kJ/mol per compound
        return total_dg, sqrt(total_var)

    def _compute_transport_correction(self, rxn):
        """Membrane potential correction for transport reactions (kJ/mol)."""
        if len(rxn.compartments) <= 1:
            return 0.0
        correction = 0.0
        for met, stoich in rxn.metabolites.items():
            psi_mV = self._comp_pot.get(met.compartment, 0)
            # F (C/mol) * psi (mV) → J/mol * 1e-3 → / kilo for kJ/mol
            correction += stoich * met.charge * FARADAY * psi_mV / kilo / kilo
        return correction

    def _build_reaction_tmfa(self, rxn):
        """Build TMFA variables and constraints for one reaction. Returns True if constrained."""
        if FBAHelper.is_ex(rxn) or FBAHelper.is_biomass(rxn):
            return False
        if self.parameters["filter"] is not None and rxn.id not in self.parameters["filter"]:
            return False

        dG_mean, dG_std = self._get_reaction_dg(rxn)
        if dG_mean is None:
            return False

        can_fwd = rxn.upper_bound > 0
        can_rev = rxn.lower_bound < 0
        if not can_fwd and not can_rev:
            return False

        K = self._K

        # Binary use variables
        if can_fwd:
            BaseFBAPkg.build_variable(self, "z_fwd", 0, 1, "binary", rxn)
        if can_rev:
            BaseFBAPkg.build_variable(self, "z_rev", 0, 1, "binary", rxn)

        # Reaction dG variable
        BaseFBAPkg.build_variable(self, "dGrxn", -K, K, "continuous", rxn)

        # Error variable
        err_mult = self.parameters["error_multiplier"]
        err_bound = err_mult * dG_std if dG_std and dG_std > 0 else 0
        BaseFBAPkg.build_variable(self, "dGerr", -err_bound, err_bound, "continuous", rxn)

        # dG decomposition: dGrxn = dG° + RT*Σ(n_ij*ln(x_j)) + transport + dGerr
        # Rearranged: dGrxn - RT*Σ(n_ij*lnconc_j) - dGerr = dG° + transport
        transport = self._compute_transport_correction(rxn)
        constant = dG_mean + transport

        coef = {
            self.variables["dGrxn"][rxn.id]: 1,
            self.variables["dGerr"][rxn.id]: -1,
        }
        for met, stoich in rxn.metabolites.items():
            if met.id in self.variables["lnconc"]:
                coef[self.variables["lnconc"][met.id]] = -self._RT * stoich

        BaseFBAPkg.build_constraint(self, "dgdecomp", constant, constant, coef, rxn)

        # Flux coupling: v_fwd ≤ v_max * z_fwd
        if can_fwd:
            v_max_fwd = rxn.upper_bound
            BaseFBAPkg.build_constraint(
                self, "flux_fwd", None, 0,
                {rxn.forward_variable: 1, self.variables["z_fwd"][rxn.id]: -v_max_fwd},
                rxn,
            )

        # Flux coupling: v_rev ≤ v_max * z_rev
        if can_rev:
            v_max_rev = abs(rxn.lower_bound)
            BaseFBAPkg.build_constraint(
                self, "flux_rev", None, 0,
                {rxn.reverse_variable: 1, self.variables["z_rev"][rxn.id]: -v_max_rev},
                rxn,
            )

        # Thermodynamic feasibility: dG + K*z_fwd ≤ K → dG ≤ 0 when z_fwd=1
        if can_fwd:
            BaseFBAPkg.build_constraint(
                self, "thermo_fwd", None, K,
                {self.variables["dGrxn"][rxn.id]: 1, self.variables["z_fwd"][rxn.id]: K},
                rxn,
            )

        # Thermodynamic feasibility: -dG + K*z_rev ≤ K → dG ≥ 0 when z_rev=1
        if can_rev:
            BaseFBAPkg.build_constraint(
                self, "thermo_rev", None, K,
                {self.variables["dGrxn"][rxn.id]: -1, self.variables["z_rev"][rxn.id]: K},
                rxn,
            )

        # Mutual exclusion: z_fwd + z_rev ≤ 1
        if can_fwd and can_rev:
            BaseFBAPkg.build_constraint(
                self, "exclusion", None, 1,
                {self.variables["z_fwd"][rxn.id]: 1, self.variables["z_rev"][rxn.id]: 1},
                rxn,
            )

        return True
