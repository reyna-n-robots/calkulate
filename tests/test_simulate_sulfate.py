import copy
import numpy as np, pandas as pd
import PyCO2SYS as pyco2, calkulate as calk


# Function inputs
dic = np.array([2000.0])
pH_free = np.array([8.1])
salinity = 35.0
# For the titration
analyte_mass = 0.2  # kg
titrant_molinity = 0.15  # mol/kg
titrant_mass = np.arange(0, 2.51, 0.05) * 1e-3  # kg
temperature = np.full_like(titrant_mass, 25.0)
titrant_alkalinity_factor = 2  # for H2SO4
emf0 = 300  # mV
# ===============

# Assemble inputs into dicts
if np.isscalar(temperature):
    temperature = np.array([temperature])
if np.isscalar(salinity):
    salinity = np.array([salinity])
kwargs_core = dict(
    temperature=temperature[0],
    salinity=salinity,
    opt_pH_scale=3,
    opt_k_carbonic=16,
    opt_total_borate=1,
)

# Calculate total alkalinity
co2sys_core = pyco2.sys(dic, pH_free, 2, 3, **kwargs_core)
alkalinity_core = co2sys_core["alkalinity"]

# Dilute things with the titrant
dilution_factor = analyte_mass / (analyte_mass + titrant_mass)
alkalinity_titration = (
    1e6
    * (
        analyte_mass * co2sys_core["alkalinity"] * 1e-6
        - titrant_alkalinity_factor * titrant_mass * titrant_molinity
    )
    / (analyte_mass + titrant_mass)
)
dic_titration = dic * dilution_factor
kwargs_titration = copy.deepcopy(kwargs_core)
kwargs_titration.update(
    total_borate=co2sys_core["total_borate"],
    total_fluoride=co2sys_core["total_fluoride"],
    total_sulfate=co2sys_core["total_sulfate"],
)
for k in [
    "total_borate",
    "total_fluoride",
]:
    kwargs_titration[k] = kwargs_titration[k] * dilution_factor

# Sulfate gets added by the H2SO4 titrant, not diluted
kwargs_titration["total_sulfate"] = (
    kwargs_titration["total_sulfate"] * analyte_mass
    + titrant_molinity * titrant_mass * 1e6
) / (analyte_mass + titrant_mass)

# Simulate titration with PyCO2SYS
co2sys_titrations = pyco2.sys(
    alkalinity_titration, dic_titration, 1, 2, **kwargs_titration
)
pH_titrations = co2sys_titrations["pH_free"]

# Export .dat file(s) for Calkulate
emf = calk.convert.pH_to_emf(pH_titrations, emf0, kwargs_titration["temperature"])
file_name = "tests/data/test_simulate_sulfate.dat"
calk.write_dat(
    file_name,
    titrant_mass * 1000,  # g
    emf,  # mV
    temperature,  # °C
    mode="w",
    measurement_fmt=".4f",
)

# Get totals and k_constants
totals, totals_pyco2 = calk.interface.get_totals(salinity, dic=dic)
totals = calk.convert.dilute_totals_H2SO4(
    totals, titrant_molinity, titrant_mass, analyte_mass
)
totals_pyco2 = calk.convert.dilute_totals_pyco2_H2SO4(
    totals_pyco2, titrant_molinity, titrant_mass, analyte_mass
)
k_constants = calk.interface.get_k_constants(totals_pyco2, salinity, temperature)

# Solve!
opt_result = calk.core.solve_emf_complete_H2SO4(
    titrant_molinity, titrant_mass, emf, temperature, analyte_mass, totals, k_constants,
)
alkalinity_solved, emf0_solved = opt_result["x"]
alkalinity_solved *= 1e6


def test_core_solver_H2SO4():
    """Does the core H2SO4 solver correctly solve a simulated titration?"""
    assert np.isclose(alkalinity_core, alkalinity_solved, rtol=0, atol=1e-8)
    assert np.isclose(emf0, emf0_solved, rtol=0, atol=1e-8)


# test_core_solver_H2SO4()

# # Import as a Calkulate Dataset
# ds = pd.DataFrame({"file_name": [file_name]})
# ds["salinity"] = co2sys_core["salinity"]
# ds["analyte_mass"] = analyte_mass
# ds["titrant_molinity"] = titrant_molinity
# ds["titrant_amount_unit"] = "g"
# ds["opt_total_borate"] = 1
# ds["opt_k_carbonic"] = 16
# ds["dic"] = co2sys_core["dic"]
# ds["titrant"] = "H2SO4"
# ds = calk.Dataset(ds)
# ds.solve()
# co2sys_core["alkalinity_titration"] = alkalinity_solved = ds.alkalinity.to_numpy()[0]
# co2sys_core["emf0"] = ds.emf0.to_numpy()
# co2sys_core["alkalinity_offset"] = co2sys_core["alkalinity_titration"] - alkalinity_core


# def test_simulate_then_solve():
#     assert np.isclose(co2sys_core["emf0"], emf0, rtol=0, atol=1e-4)
#     assert np.isclose(co2sys_core["alkalinity_offset"], 0, rtol=0, atol=1e-3)


# # test_simulate_then_solve()
