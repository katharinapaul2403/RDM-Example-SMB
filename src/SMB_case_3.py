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
# (Example_3_SMB)=
# # Ternary separation

# %% [markdown]
# Case study III examines the separation of the three components 2’-deoxycytidine `A`, 2’-deoxyguanosine `B`, and 2’-deoxyadenosine `C`. The SMB system with a  standard five-zone scheme is assumed. (No partial-feeding and partial-closing) 

# %% [markdown]
# ```{figure} ./figures/case_study3.jpg
# :width: 600px
# <div style="text-align: center">
# (Fig. 4, He et al.) Integrated five-zone SMB scheme with two extract ports
# <div>

# %% [markdown]
# (Ternary separation with a five zone system is particularly effective when the target component is present in much higher abundance than the more strongly retained component.)
# The 

# %%
from CADETProcess.processModel import ComponentSystem
from CADETProcess.processModel import Linear
from CADETProcess.processModel import Inlet, Outlet, GeneralRateModel

# Component System
component_system = ComponentSystem(['A', 'B', 'C'])

# Binding Model
binding_model = Linear(component_system)
binding_model.is_kinetic = True
binding_model.adsorption_rate = [3.15, 7.40, 23.0]  # Henry_1 = 3.15; Henry_2 = 7.40, Henry_3 = 23.0
binding_model.desorption_rate = [1, 1, 1]

# Column
column = GeneralRateModel(component_system, name='column')
column.binding_model = binding_model
column.length = 0.150 # L [m]
column.diameter = 1.0e-2  # d [m]
column.bed_porosity = 0.80  # ε_c [-]
column.particle_porosity = 1.0e-5  # ε_p [-] 
column.particle_radius = 1.50e-5  # r_p [m]
column.film_diffusion = component_system.n_comp * [1.6e4]  # k_f [m / s]  
column.pore_diffusion = component_system.n_comp * [5e-5]  # D_p [m² / s]
column.axial_dispersion = 3.81e-10  # D_ax [m² / s]
column.discretization.npar = 1  # N_r
column.discretization.ncol = 40  # N_z

eluent = Inlet(component_system, name='eluent')
eluent.c = [0, 0, 0]  # c_in_D [mol / m^3]
eluent.flow_rate = 2.34e-7  # Q_D [m^3 / s]

feed = Inlet(component_system, name='feed')
feed.c = [4.41e3, 3.75e3, 3.98e3]  # c_in [mol / m^3]  
feed.flow_rate = 1.67e-8  # Q_F [m^3 / s]

# %% [markdown]
# All zones are connected to each other in series `SerialZone`
# ```
# zone_I -> extract_1 + zone_II
# Q_I = Q_E + Q_II 
#
# zone_II -> extract_2 + zone_III
# Q_II * A = Q_E2 * A_extract2 + Q_III * A
#
# zoneIV -> raffinate + zone_V
# Q_IV * A = Q_R * A_raffinate + Q_V * A
#
# w_e1 = Q_E / Q_I = 0.6438
# w_e2 = Q_E2 / Q_II = 0.4419
# w_r = Q_R / Q_IV = 0.224

# %%


#A_extract1 / A = 0.9946
#A_extract2 / A = 1.0065
print(1.667e-8 * 	1.009)
Q_R = 1.68e-8  # Operating point a, Table 3 Mun et al.
Q_E = 1.88e-7  # Operating point a, Table 3
Q_E2 = 4.64e-8  
Q_I = 2.92e-7
Q_II = 1.05e-7
Q_IV =7.50e-8
Q_V = 5.82e-8
A_raffinate
Q_E / Q_I 
Q_E2 / Q_II 
Q_R / Q_IV 

# %%
extract_1 = Outlet(component_system, name = 'extract_1')
extract_2 = Outlet(component_system, name = 'extract_2')
raffinate = Outlet(component_system, name = 'raffinate')
from CADETProcess.modelBuilder import SerialZone

zone_I = SerialZone(component_system, 'zone_I', n_columns=1, valve_dead_volume=1e-9)
zone_II = SerialZone(component_system, 'zone_II', n_columns=1, valve_dead_volume = 1e-9)
zone_III = SerialZone(component_system, 'zone_III', n_columns=1, valve_dead_volume = 1e-9)
zone_IV = SerialZone(component_system, 'zone_IV', n_columns=1, valve_dead_volume = 1e-9)
zone_V = SerialZone(component_system, 'zone_V', n_columns=1, valve_dead_volume = 1e-9)

from CADETProcess.modelBuilder import CarouselBuilder

builder = CarouselBuilder(component_system, 'smb')
builder.column = column
builder.add_unit(eluent)
builder.add_unit(feed)
builder.add_unit(extract_1)
builder.add_unit(extract_2)
builder.add_unit(raffinate)

builder.add_unit(zone_I)
builder.add_unit(zone_II)
builder.add_unit(zone_III)
builder.add_unit(zone_IV)
builder.add_unit(zone_V)

builder.add_connection(eluent, zone_I)

builder.add_connection(zone_I, extract_1)
builder.add_connection(zone_I, zone_II)
w_e1 = 0.6438
builder.set_output_state(zone_I, [w_e1, 1 - w_e1])

builder.add_connection(zone_II, extract_2)
builder.add_connection(zone_II, zone_III)
w_e2 = 0.4419
builder.set_output_state(zone_II, [w_e2, 1 - w_e2])

builder.add_connection(zone_III, zone_IV)
builder.add_connection(feed, zone_IV)

builder.add_connection(zone_IV, raffinate)
builder.add_connection(zone_IV, zone_V)
w_r = 0.224
builder.set_output_state(zone_IV, [w_r, 1 - w_r])

builder.add_connection(zone_V, zone_I)

builder.switch_time = 264  # Fig 8 - standard mode at 200.99 steps n = step number/switching number

process = builder.build_process()

# %%
from CADETProcess.simulator import Cadet
process_simulator = Cadet()
#process_simulator.evaluate_stationarity = True  # langsam
process_simulator.n_cycles = 1  # lässt die conc. ordinate von e-14 auf e-8 steigen, konzentrationen gehen nicht mehr ins negative, peaks fangen erst ab 8min an?
# cycle_time = self.n_columns * self.switch_time
simulation_results = process_simulator.simulate(process)

_ = simulation_results.solution.raffinate.inlet.plot()
_ = simulation_results.solution.extract_1.inlet.plot()
_ = simulation_results.solution.extract_2.inlet.plot()
#_ = simulation_results.sensitivity['column.axial_dispersion'].column.outlet.plot()
#simulation_results.time_elapsed()

# %%
