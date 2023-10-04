# LWR FT Use case
## Description of cases and files
### Use case description
LWR FT: Light Water Reactor with Fischer-Tropsch use case
Locations: 
- braidwood
- cooper
- davis-besse
- prairie-island
- stp (South Texas Project)

location_baseline corresponds to the BAU case of the NPP selling electricity to the grid
location_sweep corresponds to the synfuel IES case

All results are in location_case/gold

### Sensitivities
location_sensitivity folder name convention
Sensitivities explored: 
- capex_0.75 and capex_1.25: CAPEX of the synfuel production processes perturbed x0.75 and x1.25
- co2_cost_high and co2_cost_med: additional $60 and $30/ton-co2
- elec_0.75 and elec_1.25: electricity prices perturbed x0.75 and x1.25
- om_0.75 and om_1.25: O&M of the synfuel production processes perturbed x0.75 and x1.25
- ptc_000, ptc_100, ptc_270: Hydrogen production tax credit reduced to $0, $1, and $2.7/kg-h2
- synfuels_0.75 and synfuels_1.25: Syfnuel prices perturbed x0.75 and x1.25



