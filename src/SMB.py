# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# (Example_SMB)=
# # Simulated Moving Bed

# %% [markdown]
# The following example is a reproduction of part of the research results published in "Efficient numerical simulation of simulated moving bed chromatography with a single-column solver" (Qiao-Le He, Samuel Leweke, Eric von Lieres, Computers & Chemical Engineering 2018; 111:183-198. doi:10.1016/j.compchemeng.2017.12.022.) <br>
# https://www.sciencedirect.com/science/article/pii/S0098135417304520
#

# %% [markdown]
# The first case study depicted in the paper evaluates the separation of the two components fructose `A` and glucose `B` in a four-zone simulated moving bed (SMB) system with eight columns. The binding behavior follows a linear isotherm.  
#
# In addition to the columns a SMB system contains four different external units connected to the columns:
# 1. Feed: component mixture
# 2. Raffinate: faster eluting component (elutes before feed plug flow)
# 3. Extract: slower eluting component (elutes after feed plug flow), interacts more strongly with the column solid phase
# 4. Desorbant (Eluent): Solution to elute extract from column before raffinate plug flow enters the column again to prevent mixing of the separated components
#
#

# %% [markdown]
# A continuous process can be approximated by periodically switching the inlet and outlet valves of the columns in the system ("column switching"). The position of each column relative to these external units determine their specific "Zone" in the SMB system. Based on thier external units, every zone has a different function in the seperation process and a different flow rate within the columns. 
#

# %% [markdown]
# ```{figure} ./figures/case_study1_practical_setup.jpg
# :width: 600px
# <div style="text-align: center">
# (Fig. 5, He et al.) Four-zone SMB schemes with eight columns indicating positions of the associated hold-up volumes
# <div>

# %% [markdown]
# As seen in Fig. 5, hold up-volumes between all columns and external units exist and should ideally be considered in thier effect on the SMB elution. (triangle theory) They generally increase retention time and dispersion. (The hold-up volume on either side of a column, i.e., tubing and frits, can be described by a CSTR that is moved through the network together with that column. )(four categories: (1) tubing between multi-port valve and column inlet plus frit before packed bed, (2) frit after packed bed plus tubing between column outlet and multi-port valve, (3) tubing between injection point and multi-port valve, and (4) tubing between multi-port valve and detector. Each of these categories can be modeled as one or more PFR, CSTR and/or DPFR in series. )
# -> CADET-SMB allows to consider hold-up volumes in the column network. This is demonstrated by introducing CSTR models, Eq. (10), in case study I as illustrated by Fig. 5. The residence time, τCSTR, is varied between 0s, 5s and 10s. Fig. 14 shows the impact of these hold-up volumes on the column states in CSS.

# %% [markdown]
# To simulate the SMB process, first the physical properties of the columns and the Inlet are defined. The mass transfer within the column is characterized by the equilibrium-dispersive model (EDM) which can be derived from the `GeneralRateModel` by defining the spatial discretization `column.discretization.npar` as 1. In the finite volume method, only one radial cell is assumed. The axial column dimension `column.discretization.ncol` is set to 40 axial cells. All numerical values are taken from Table 1.(4. Case Studies). The Henry coefficient can be assumed to equal the equilibrium constant under ideal, linear conditions. 

# %%
from CADETProcess.processModel import ComponentSystem
from CADETProcess.processModel import Linear
from CADETProcess.processModel import Inlet, Outlet, GeneralRateModel

# Component System
component_system = ComponentSystem(['A', 'B'])

# Binding Model
binding_model = Linear(component_system)
binding_model.is_kinetic = False
binding_model.adsorption_rate = [0.54, 0.28]  # Henry_1 = 	0.54; Henry_2 = 0.28
binding_model.desorption_rate = [1, 1]
 

# Column
column = GeneralRateModel(component_system, name='column')
column.binding_model = binding_model

column.length = 0.536  # L [m]
column.diameter = 2.6e-2  # d [m]
column.bed_porosity = 0.38  # ε_c [-]

column.particle_porosity = 1.0e-5  # ε_p [-] 
column.particle_radius = 1.63e-3  # r_p [m]
column.film_diffusion = component_system.n_comp * [1.6e4]  # k_f [m / s]
column.pore_diffusion = component_system.n_comp * [5e-5]  # D_p [m² / s]
column.axial_dispersion = 3.81e-6  # D_ax [m² / s]
column.discretization.npar = 1  # N_r
column.discretization.ncol = 40  # N_z

column.solution_recorder.write_solution_bulk = True

eluent = Inlet(component_system, name='eluent')
eluent.c = [0, 0]  # c_in_D [mol / m^3]
eluent.flow_rate = 4.14e-8  # Q_D [m^3 / s]

feed = Inlet(component_system, name='feed')
feed.c = [2.78e3, 2.78e3]  # c_in [mol / m^3]
feed.flow_rate = 2.0e-8  # Q_F [m^3 / s]

# %% [markdown]
# The unit system of the SMB is implemented using the `CarouselBuilder` from CADETProcess. Four zones with two columns in each zone and the connections to their respective external units are implemented as seen in Fig. 5. For more information please refer: [here](https://cadet-process.readthedocs.io/en/stable/user_guide/tools/carousel_builder.html#). (Not using SMB builder because `n_columns` = 2) <br>
# The percentile of the volume flow that leaves `zone_I` for `extract`(`w_e`) or `zone_II` (`1-w_e`) can be deducted by examining the differences in the volumetric flow rate as all columns have the same cross section `A`(Table 1.). The same can be done for the percentile of the volume flow that leaves `zone_III` for `raffinate`(`w_r`) and `zone_IV` (`1-w_r`) <br>
# The continuity equation for laminar flow is assumed:
# `A_1 * v_1 = A_2 * v_2`
# ```
# zone_I -> extract + zone_II
# Q_I * A = Q_E * A_extract + Q_II * A
# 1.4e-7 * 5.31e-4 = 3.48e-8 * A_extract + 1.05e-7 * 5.31e-4 
# A_extract = (1.4e-7  - 1.05e-7 ) / (3.48e-8 / 5.31e-4) = 5.34e-4
# A_extract / A = 1.006
# w_e = (Q_E / Q_I 
# w_e = (3.48e-8 * 1.006) / (1.4e-7) = 0.25
#
# zoneIII -> raffinate + zone_IV
# Q_III * A = Q_R * A_raffinate + Q_IV * A
# 1.25e-7 * 5.31e-4 = 2.66e-8 * A_raffinate + 9.81e-8 * 5.31e-4
# A_raffinate = (1.25e-7 - 9.81e-8) / (2.66e-8 / 5.31e-4) = 5.37e-4
# A_raffinate / A = 1.011
# w_r = (Q_R * Q_III 
# w_r = (2.66e-8 * 1.011) / (1.25e-7) = 0.215
# ``` 

# %%
column.volume_liquid

# %%
extract = Outlet(component_system, name='extract')
raffinate = Outlet(component_system, name='raffinate')
from CADETProcess.modelBuilder import SerialZone, ParallelZone

zone_I = SerialZone(component_system, 'zone_I', n_columns = 2, valve_dead_volume=1e-9)
zone_II = SerialZone(component_system, 'zone_II', n_columns = 2, valve_dead_volume=1e-9)
zone_III = SerialZone(component_system, 'zone_III', n_columns = 2, valve_dead_volume=1e-9)
zone_IV = SerialZone(component_system, 'zone_IV', n_columns = 2, valve_dead_volume=1e-9)

from CADETProcess.modelBuilder import CarouselBuilder

builder = CarouselBuilder(component_system, 'smb')
builder.valve_dead_volume = 1e-9
builder.column = column
builder.add_unit(eluent)
builder.add_unit(feed)

builder.add_unit(extract)
builder.add_unit(raffinate)

builder.add_unit(zone_I)
builder.add_unit(zone_II)
builder.add_unit(zone_III)
builder.add_unit(zone_IV)

builder.add_connection(eluent, zone_I)

builder.add_connection(zone_I, extract)
builder.add_connection(zone_I, zone_II)
w_e = 0.248
builder.set_output_state(zone_I, [w_e, 1-w_e])

builder.add_connection(zone_II, zone_III)

builder.add_connection(feed, zone_III)

builder.add_connection(zone_III, raffinate)
builder.add_connection(zone_III, zone_IV)
w_r = 0.213
builder.set_output_state(zone_III, [w_r, 1-w_r])

builder.add_connection(zone_IV, zone_I)

builder.switch_time = 1552

process = builder.build_process()

# %%
#process = smb_builder.build_process()

from CADETProcess.simulator import Cadet
process_simulator = Cadet()
#process_simulator.evaluate_stationarity = True
process_simulator.n_cycles = 1
#process_simulator.timeout = 15*60
#simulate first 8 switch times (1 iteration), conc bis 1mol

process_simulator.time_integrator_parameters.abstol = 1e-10
process_simulator.time_integrator_parameters.reltol = 1e-6
process_simulator.time_integrator_parameters.init_step_size = 1e-14
process_simulator.time_integrator_parameters.max_step_size = 5e6

simulation_results = process_simulator.simulate(process)

_ = simulation_results.solution.raffinate.inlet.plot(start = 0, end = 8 * builder.switch_time)
_ = simulation_results.solution.extract.inlet.plot(start = 0, end = 8 * builder.switch_time)
#lief für 75min ohne ergebnis :C

# %% [markdown]
# ((CSS - cyclic steady state: dynamic trajectory is repeated after every switch => all columns have same state after specific time laps ))

# %%
raff = simulation_results.solution.raffinate.inlet.solution
ext = simulation_results.solution.extract.inlet.solution
t = simulation_results.time_complete

# %%
import matplotlib.pyplot as plt
import numpy as np

plt.plot(t, ext*np.pi*0.536*(2.6e-2/2)**2)
plt.ylim(0,1)

# %%
plt.plot(t, raff*np.pi*0.536*(2.6e-2/2)**2)
plt.ylim(0,1)


# %%
#class CarouselSolutionBulk(SolutionBase):
#plot_at_time 
from CADETProcess.modelBuilder.carouselBuilder import CarouselSolutionBulk
axial_conc = CarouselSolutionBulk(builder, simulation_results)
axial_conc.component_system
axial_conc.solution
axial_conc.axial_coordinates
axial_conc.time
simulation_results.solution
axial_conc.plot_at_time(t = 1552)

#switching time -> bisher nur 1x geswitched -> nur einmal wurde column 7 zu column 6, müssen mindestens 8x switchen(für jede säule 1x damit  SMB Process 1x durhgelaufen)
#8x switching time = 1 cycle
#machen ein paar cyclen damit sich der CSS eingestellt hat -> Säulen sind komplett gefüllt etc



# %%
#process = smb_builder.build_process()

from CADETProcess.simulator import Cadet
process_simulator = Cadet()
#process_simulator.evaluate_stationarity = True
process_simulator.n_cycles = 6
process_simulator.use_dll = True
#process_simulator.timeout = 15*60
#simulate first 8 switch times (1 iteration), conc bis 1mol

process_simulator.time_integrator_parameters.abstol = 1e-10
process_simulator.time_integrator_parameters.reltol = 1e-6
process_simulator.time_integrator_parameters.init_step_size = 1e-14
process_simulator.time_integrator_parameters.max_step_size = 5e6

simulation_results = process_simulator.simulate(process)
#QUATSCH! mit dem cycle+1
cycle = 6
_ = simulation_results.solution.raffinate.inlet.plot(start = cycle * 0, end = (cycle+1) * 8 * builder.switch_time)
_ = simulation_results.solution.extract.inlet.plot(start = 0, end = 8 * builder.switch_time)
#lief für 75min ohne ergebnis :C

# %%
cycle = 6
_ = simulation_results.solution.extract.inlet.plot(start = cycle * 0, end = (cycle) * 8 * builder.switch_time) 
#haben kontamination von komponente B die in den Extrakt reinfließt, sieht so aus als wäre switching time um einen switch 1/8 nach hinten verschoben

# %%
#class CarouselSolutionBulk(SolutionBase):
#plot_at_time 
#machen CSS, zur Endzeit, sieht aus als wäre es um einen Switch verschoben
from CADETProcess.modelBuilder.carouselBuilder import CarouselSolutionBulk
axial_conc = CarouselSolutionBulk(builder, simulation_results)
axial_conc.component_system
axial_conc.solution
axial_conc.axial_coordinates
axial_conc.time
simulation_results.solution
axial_conc.plot_at_time(t = 74496.0)

# %%
