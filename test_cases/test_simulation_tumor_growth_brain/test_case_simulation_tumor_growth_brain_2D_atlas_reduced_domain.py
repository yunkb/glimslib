"""
Example demonstrating usage of :py:meth:`simulation.simulation_tumor_growth_brain`:
 - forward simulation
 - 2D test domain from brain atlas, 4 tissue subdomains + 'outside'
 - spatially heterogeneous parameters, as defined in simulation.simulation_tumor_growth_brain
 - no displacement bc between 'outside' and other subdomains
"""

import logging
import os

import test_cases.test_simulation_tumor_growth_brain.testing_config as test_config

from glimslib.simulation import TumorGrowthBrain
from glimslib import fenics_local as fenics, config
import glimslib.utils.file_utils as fu
import glimslib.utils.data_io as dio

# ==============================================================================
# Logging settings
# ==============================================================================

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
fenics.set_log_level(fenics.CRITICAL)

# ==============================================================================
# Load 2D Mesh from IMAGE
# ==============================================================================
path_to_hdf5_mesh = os.path.join(config.test_data_dir, 'brain_atlas_mesh_2d_reduced_domain.h5')
mesh, subdomains, boundaries = dio.read_mesh_hdf5(path_to_hdf5_mesh)

# ==============================================================================
# Problem Settings
# ==============================================================================

class Boundary(fenics.SubDomain):
    def inside(self, x, on_boundary):
        return on_boundary

tissue_id_name_map = {    1: 'CSF',
                          3: 'WM',
                          2: 'GM',
                          4: 'Ventricles'}

# Boundaries & BCs
boundary = Boundary()
boundary_dict = {'boundary_all': boundary}

dirichlet_bcs = {'clamped_0': {'bc_value': fenics.Constant((0.0, 0.0)),
                                'named_boundary': 'boundary_all',
                                'subspace_id': 0}
                      }

von_neuman_bcs = {}


# Initial Values
u_0_conc_expr = fenics.Expression('exp(-a*pow(x[0]-x0, 2) - a*pow(x[1]-y0, 2))', degree=1, a=0.5, x0=148, y0=-67)
u_0_disp_expr = fenics.Constant((0.0, 0.0))


# ==============================================================================
# Class instantiation & Setup
# ==============================================================================
sim_time = 20
sim_time_step = 1

sim = TumorGrowthBrain(mesh)

sim.setup_global_parameters(subdomains=subdomains,
                             domain_names=tissue_id_name_map,
                             boundaries=boundary_dict,
                             dirichlet_bcs=dirichlet_bcs,
                             von_neumann_bcs=von_neuman_bcs
                             )


ivs = {0:u_0_disp_expr, 1:u_0_conc_expr}
sim.setup_model_parameters(iv_expression=ivs,
                           sim_time=sim_time, sim_time_step=sim_time_step,
                           E_GM=3000E-6, E_WM=3000E-6, E_CSF=1000E-6, E_VENT=1000E-6,
                           nu_GM=0.45, nu_WM=0.45, nu_CSF=0.45, nu_VENT=0.3,
                           D_GM=0.01, D_WM=0.05,
                           rho_GM=0.05, rho_WM=0.05,
                           coupling=0.1)

# ==============================================================================
# Run Simulation
# ==============================================================================
output_path = os.path.join(test_config.output_path, 'test_case_simulation_tumor_growth_brain_2D_atlas_reduced_domain')
fu.ensure_dir_exists(output_path)
sim.run(save_method='vtk',plot=False, output_dir=output_path, clear_all=True)

print("============= FINISHED SIMULATION ================")

path_to_h5_file = os.path.join(output_path, 'solution_timeseries.h5')
sim.reload_from_hdf5(path_to_h5_file)

# ==============================================================================
# PostProcess
# ==============================================================================

# dio.merge_VTUs(output_path, sim_time_step, sim_time, remove=True, reference=None)
# selection = slice(0,-1,5)
sim.init_postprocess(os.path.join(output_path, 'postprocess', 'plots'))
# sim.postprocess.plot_all(deformed=False, selection=selection)
# sim.postprocess.plot_all(deformed=True, selection=selection)

import numpy as np
qmin, qmax = fenics.MeshQuality.radius_ratio_min_max(sim.mesh)
print('Minimal radius ratio:', qmin)
print('Maximal radius ratio:', qmax)

sim.postprocess.update_mesh_displacement(20)
qmin, qmax = fenics.MeshQuality.radius_ratio_min_max(sim.mesh)
print('Minimal radius ratio:', qmin)
print('Maximal radius ratio:', qmax)

last_recording_step = max(sim.results.get_recording_steps())
conc = sim.postprocess.get_solution_concentration(last_recording_step)
print("Min conc: ", np.min(conc.vector().array()))
print("Max conc: ", np.max(conc.vector().array()))