
"""

@author: rbaed


PV – Battery – Islanded Microgrid Simulation (OpenDSS + Python)

This script simulates an Residential microgrid under different islanding
scenarios using OpenDSS and Python. It focuses on understanding how photovoltaic
(PV) systems and a mobile battery energy storage system (BESS) help the network
survive faults and operate in islanded mode.

The script runs several predefined scenarios (Scenario 1-2–3–4) on the same feeder
model and automatically generates publication-ready figures:

  - Power balance: PV, battery, total load, and total local supply
  - Voltage behavior: minimum, maximum, and mean voltage across all houses
  - Battery state of charge (SoC) aligned with voltage stability
  
Can be modified to spesific scenarios.
"""



import os
import math
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple, Callable

import numpy as np
import matplotlib.pyplot as plt
import opendssdirect as dss




MASTER_DSS = "master.dss"          # relative path
RESULTS_DIR = "results"            # all plots saved here

MINUTES = 1440                     # 24h * 60min
HOMES = ["home1","home2","home3","home4","home5","home6","home7","home8","home9","home10"]


RESERVE_PCT = 20.0                 # reserve threshold (20%)
SOC_HYST = 0.5
TARGET_LOAD_KW = 15.0              
PV_CHARGE_KW = 10.0
PV_CHARGE_MIN_KW = 2.0
SOC_MAX_CHARGE = 95.0



@dataclass
class ScenarioConfig:
    
    name: str
    description: str
    pv_shape: str            
    pv_enabled: bool         
    bess_enabled: bool       
    events: Dict[int, List[str]]


def scenario_1() -> ScenarioConfig:
    
    """ Scenario 1: No PV, No BESS.  """
    return ScenarioConfig(
        name="scenario_1_no_support",
        description="Baseline case: fault without PV or BESS support.",
        pv_shape="pvshape2",
        pv_enabled=False,
        bess_enabled=False,
        events={
            120: ["edit line.sw2 enabled=no"],  

        },
    )



def scenario_2() -> ScenarioConfig:
    
    """  Scenario 2: Only BESS   """
    return ScenarioConfig(
        name="scenario_2_bess_only",
        description="Fault + island support using BESS only (PV disabled).",
        pv_shape="pvshape2",
        pv_enabled=False,
        bess_enabled=True,
        events={
            120: ["edit line.sw2 enabled=no"],
            400: [
                "edit vsource.dummy_1 enabled=yes",
                "edit line.mbs_s1 enabled=yes",
            ],
        },
    )


def scenario_3() -> ScenarioConfig:
    
    """ Scenario 3: PV + BESS synergy."""
    return ScenarioConfig(
        name="scenario_3_pv_bess_synergy",
        description="Synergistic PV+BESS islanded autonomy.",
        pv_shape="pvshape1",
        pv_enabled=True,
        bess_enabled=True,
        events={
            120: [
                "edit line.sw2 enabled=no",
                "edit line.mbs_s2 enabled=no",  
            ],
            400: [
                "edit vsource.dummy_1 enabled=yes",
                "edit line.mbs_s1 enabled=yes",
            ],
        },
    )


def scenario_4() -> ScenarioConfig:
    
    """ Scenario 4: """
    return ScenarioConfig(
        name="scenario_4_distributed_faults",
        description="Adaptive resilience against distributed network faults (multi-event).",
        pv_shape="pvshape1",
        pv_enabled=True,
        bess_enabled=True,
        events={
            120: ["edit line.sw2 enabled=no"],
            300: ["edit vsource.dummy_1 enabled=yes", "edit line.mbs_s1 enabled=yes"],
            700: ["edit line.mbs_s1 enabled=no", "edit vsource.dummy_1 enabled=no"],
            720: ["edit line.sw4 enabled=no"],
            920: ["edit vsource.dummy_1 enabled=yes", "edit line.mbs_s2 enabled=yes"],
        },
    )




def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def limit_power(val: float) -> float:
    """Avoid NaN / numeric blow-ups """
    if val is None:
        return 0.0
    if isinstance(val, float) and (math.isnan(val) or abs(val) > 1e6):
        return 0.0
    return float(val)


def compile_model(master_dss: str) -> None:
    """Compile DSS model"""
    dss.Command("clear")
    dss.Command(f"compile '{master_dss}'")
    dss.Command("set mode=daily stepsize=1m number=1")


def set_pv_profile(shape_name: str) -> None:
    dss.Command(f"edit pvsystem.pv1 daily={shape_name}")


def set_pv_enabled(enabled: bool) -> None:
    dss.Command(f"edit pvsystem.pv1 enabled={'yes' if enabled else 'no'}")


def is_islanded_via_dummy() -> bool:
    
    """Detect islanding via dummy source being enabled."""
    ok = dss.Circuit.SetActiveElement("vsource.dummy_1")
    return bool(ok and dss.CktElement.Enabled())


def get_pv_kw() -> float:
    """Read PV power (kW). Convention: -Powers()[0] gives generation in your scripts"""
    p = 0.0
    if dss.Circuit.SetActiveElement("PVSystem.pv1") and dss.CktElement.Enabled():
        p = limit_power(-dss.CktElement.Powers()[0])
    return p


def get_total_load_kw(homes: List[str]) -> float:
    """Sum total household demand (kW) similarly to your approach"""
    total = 0.0
    for h in homes:
        if dss.Circuit.SetActiveElement(f"Load.{h}"):
            pw = dss.CktElement.Powers()
            if pw:
                # single-phase may still return list; keep your pattern
                total += abs(limit_power(sum(pw[0:6:2])))
    return total


def get_bus_voltage_v(bus_name: str) -> float:
    dss.Circuit.SetActiveBus(bus_name)
    vm = dss.Bus.VMagAngle()
    if (vm is None) or (len(vm) < 1):
        return 0.0
    v = vm[0]
    if math.isnan(v) or v > 1e4:
        return 0.0
    return float(v)


def get_bess_soc_and_power() -> Tuple[float, float]:
    
    """
    Read Storage.mobilebat SoC and power. 
    """
    soc = 0.0
    p_bat = 0.0

    if dss.Circuit.SetActiveElement("Storage.mobilebat"):
        try:
            soc_raw = float(dss.Properties.Value("%stored"))
            soc = soc_raw if not math.isnan(soc_raw) else soc
        except Exception:
            pass

        pw = dss.CktElement.Powers()
        if pw:
            p_bat = abs(limit_power(sum(pw[0:6:2])))

    return soc, p_bat


def bess_control_step(is_island: bool, pv_kw: float, prev_soc: float, enabled: bool) -> float:
    
    """
      - In island: discharge to meet target (TARGET_LOAD - PV)
      - Stop/idle if SoC below reserve threshold (RESERVE_PCT + SOC_HYST)
      - In grid-connected: optionally charge from PV if available & SoC < SOC_MAX_CHARGE
    """
    if not enabled:
        dss.Command("edit Storage.mobilebat State=IDLING kW=0")
        return prev_soc

    # read current soc
    soc, _ = get_bess_soc_and_power()
    if soc <= 0:
        soc = prev_soc if prev_soc > 0 else 40.0

    if is_island:
        soc_stop = RESERVE_PCT + (SOC_HYST or 0.0)
        if soc <= soc_stop:
            dss.Command("edit Storage.mobilebat State=IDLING kW=0")
        else:
            discharge_kw = max(0.0, TARGET_LOAD_KW - pv_kw)
            dss.Command(f"edit Storage.mobilebat State=DISCHARGING kW={discharge_kw}")
    else:
        # charge only if PV exists and SoC not full
        if pv_kw > PV_CHARGE_MIN_KW and soc < SOC_MAX_CHARGE:
            dss.Command(f"edit Storage.mobilebat State=CHARGING kW={PV_CHARGE_KW}")
        else:
            dss.Command("edit Storage.mobilebat State=IDLING kW=0")

        if soc >= SOC_MAX_CHARGE:
            dss.Command("edit Storage.mobilebat State=IDLING kW=0")

    return soc




@dataclass
class ScenarioResults:
    minutes: int
    homes: List[str]

    pv_kw: List[float]
    bat_kw: List[float]
    soc_pct: List[float]
    load_kw: List[float]
    supply_kw: List[float]
    island_flag: List[int]
    voltages: Dict[str, List[float]]

    stability_minutes: int  


def init_results(minutes: int, homes: List[str]) -> ScenarioResults:
    return ScenarioResults(
        minutes=minutes,
        homes=homes,
        pv_kw=[],
        bat_kw=[],
        soc_pct=[],
        load_kw=[],
        supply_kw=[],
        island_flag=[],
        voltages={h: [] for h in homes},
        stability_minutes=0,
    )



# PLOTS

def plot_power_flow(res: ScenarioResults, title: str, out_png: str) -> None:
  
    """
    Plot PV, BESS, total load, total supply.
    """
    plt.figure(figsize=(12, 6), dpi=160)
    plt.plot(res.pv_kw, label="PV Output (kW)", linewidth=2.0)
    plt.plot(res.bat_kw, label="BESS Discharge (kW)", linestyle="--", linewidth=2.0)
    plt.plot(res.load_kw, label="Total Demand (kW)", linestyle="-.", linewidth=2.0)
    plt.plot(res.supply_kw, label="Total Supply (PV + BESS)", linestyle=":", linewidth=2.5)

    plt.title(title, fontsize=13, fontweight="bold")
    plt.xlabel("Time (minutes)")
    plt.ylabel("Power (kW)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, bbox_inches="tight")
    plt.close()


def plot_voltage_band_and_soc(res: ScenarioResults, title: str, out_png: str, vref: float = 230.0) -> None:

    """
      TOP: voltage band  + mean voltage + reference line
      BOTTOM: SoC (%)
    """
    t = np.arange(res.minutes)

    V = np.vstack([np.array(res.voltages[h], dtype=float) for h in res.homes])
    v_min = np.nanmin(V, axis=0)
    v_max = np.nanmax(V, axis=0)
    v_mean = np.nanmean(V, axis=0)

    fig, (axV, axS) = plt.subplots(
        2, 1,
        figsize=(12, 6),
        dpi=180,
        sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.0]}
    )

    LW = 2
    axV.fill_between(t, v_min, v_max, alpha=0.20, label="Voltage range", linewidth=0)
    axV.plot(t, v_mean, linewidth=LW, label="Mean voltage")
    axV.axhline(vref, linestyle="--", linewidth=LW, label=f"{vref:.0f} V reference")

    axV.set_ylabel("Voltage (V)")
    axV.grid(True, alpha=0.3)
    axV.set_title(title, fontsize=12, fontweight="bold")

    axS.plot(t, res.soc_pct, linewidth=LW, label="Battery SoC (%)")
    axS.fill_between(t, res.soc_pct, alpha=0.20)
    axS.set_ylabel("SoC (%)")
    axS.set_xlabel("Time (minutes)")
    axS.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_png, bbox_inches="tight")
    plt.close()


#SIMULATION

def run_scenario(cfg: ScenarioConfig) -> ScenarioResults:
    """
    PSEUDO-ALGORITHM (expanded):
      1) Compile model
      2) Bind PV profile + enable/disable PV
      3) Initialize containers
      4) For each minute:
          4.1) Apply scheduled events (faults, island transitions, battery relocation)
          4.2) Solve one time step
          4.3) Determine island mode (dummy source enabled?)
          4.4) Read PV power
          4.5) Execute BESS control step
          4.6) Read BESS SoC + power
          4.7) Read voltages at all homes
          4.8) Read total load
          4.9) Aggregate supply and stability duration
      5) Return results
    """
    compile_model(MASTER_DSS)
    set_pv_profile(cfg.pv_shape)
    set_pv_enabled(cfg.pv_enabled)

    res = init_results(MINUTES, HOMES)

    prev_soc = 40.0  # safe default

    for t in range(MINUTES):

        
        if t in cfg.events:
            for cmd in cfg.events[t]:
                dss.Command(cmd)

        
        dss.Command("solve")

        
        island = is_islanded_via_dummy()
        res.island_flag.append(1 if island else 0)

        
        pv_kw = get_pv_kw()
        res.pv_kw.append(pv_kw)


        soc_after = bess_control_step(island, pv_kw, prev_soc, enabled=cfg.bess_enabled)

        soc, bat_kw = get_bess_soc_and_power()
        soc = soc if soc > 0 else soc_after
        res.soc_pct.append(soc)
        res.bat_kw.append(bat_kw)
        prev_soc = soc

        if island and (soc > (RESERVE_PCT + SOC_HYST)):
            res.stability_minutes += 1

  
        for h in HOMES:
            res.voltages[h].append(get_bus_voltage_v(h))


        load_kw = get_total_load_kw(HOMES)
        res.load_kw.append(load_kw)

        res.supply_kw.append(max(0.0, pv_kw + bat_kw))

    return res


def main() -> None:
    ensure_dir(RESULTS_DIR)
    scenarios = [scenario_2(), scenario_3(), scenario_4()]
    summary = {}

    for cfg in scenarios:
        
        res = run_scenario(cfg)

        summary[cfg.name] = {
            "description": cfg.description,
            "pv_shape": cfg.pv_shape,
            "pv_enabled": cfg.pv_enabled,
            "bess_enabled": cfg.bess_enabled,
            "stability_minutes": res.stability_minutes,
        }

        # Plots
        pf_png = os.path.join(RESULTS_DIR, f"{cfg.name}_powerflow.png")
        vs_png = os.path.join(RESULTS_DIR, f"{cfg.name}_voltage_band_soc.png")

        plot_power_flow(
            res,
            title=f"{cfg.name}: Power Flow",
            out_png=pf_png
        )

        plot_voltage_band_and_soc(
            res,
            title=f"{cfg.name}: Voltage Band + Mean Voltage | SoC (Stability={res.stability_minutes} min)",
            out_png=vs_png,
            vref=230.0
        )

        print(f"Saved: {pf_png}")
        print(f"Saved: {vs_png}")

    with open(os.path.join(RESULTS_DIR, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\nAll done. Results saved in ./results/")


if __name__ == "__main__":
    main()
