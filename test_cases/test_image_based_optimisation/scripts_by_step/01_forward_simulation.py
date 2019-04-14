"""
Run forward simulation on 2D atlas
"""
import logging
import os

import test_cases.test_image_based_optimisation.testing_config as test_config

from simulation.simulation_tumor_growth_brain_quad import TumorGrowthBrain
from simulation.helpers.helper_classes import Boundary
import fenics_local as fenics
import utils.file_utils as fu
import utils.data_io as dio

# ==============================================================================
# Logging settings
# ==============================================================================

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
if fenics.is_version("<2018.1.x"):
    fenics.set_log_level(fenics.WARNING)
else:
    fenics.set_log_level(fenics.LogLevel.WARNING)
# ==============================================================================
# Load 2D Mesh from IMAGE
# ==============================================================================

labelfunction, mesh, subdomains, boundaries = dio.load_function_mesh(test_config.path_to_2d_labelfunction)
# verify that loaded correctly
# plott.show_img_seg_f(function=function, show=True,
#                      path=os.path.join(config.output_path, 'image_label_from_fenics_function_2.png'))

# ==============================================================================
# Problem Settings
# ==============================================================================

tissue_id_name_map = {    0: 'outside',
                          1: 'CSF',
                          3: 'WM',
                          2: 'GM',
                          4: 'Ventricles'}

# Boundaries & BCs
boundary = Boundary()
boundary_dict = {'boundary_all': boundary}

dirichlet_bcs = {'clamped_0': {'bc_value': fenics.Constant((0.0, 0.0)),
                                'subdomain_boundary': 'outside_CSF',
                                'subspace_id': 0},
                 # 'clamped_1': {'bc_value': fenics.Constant((0.0, 0.0)),
                 #               'subdomain_boundary': 'outside_WM',
                 #               'subspace_id': 0},
                 # 'clamped_2': {'bc_value': fenics.Constant((0.0, 0.0)),
                 #               'subdomain_boundary': 'outside_GM',
                 #               'subspace_id': 0}
                      }

von_neuman_bcs = {}


# Initial Values
u_0_conc_expr = fenics.Expression('exp(-a*pow(x[0]-x0, 2) - a*pow(x[1]-y0, 2))', degree=1, a=0.5,
                                  x0=test_config.seed_position[0], y0=test_config.seed_position[1])
u_0_disp_expr = fenics.Constant((0.0, 0.0))

ivs = {0:u_0_disp_expr, 1:u_0_conc_expr}

# ==============================================================================
# Parameters
# ==============================================================================
sim_time = test_config.params_sim["sim_time"]
sim_time_step = test_config.params_sim["sim_time_step"]

E_GM = test_config.params_fix["E_GM"]
E_WM = test_config.params_fix["E_WM"]
E_CSF = test_config.params_fix["E_CSF"]
E_VENT = test_config.params_fix["E_VENT"]
nu_GM = test_config.params_fix["nu_GM"]
nu_WM = test_config.params_fix["nu_WM"]
nu_CSF = test_config.params_fix["nu_CSF"]
nu_VENT = test_config.params_fix["nu_VENT"]

D_WM = test_config.params_target["D_WM"]
D_GM = test_config.params_target["D_GM"]
rho_WM = test_config.params_target["rho_WM"]
rho_GM = test_config.params_target["rho_GM"]
coupling = test_config.params_target["coupling"]

# ==============================================================================
# TumorGrowthBrain
# ==============================================================================

sim = TumorGrowthBrain(mesh)

sim.setup_global_parameters(label_function=labelfunction,
                             domain_names=tissue_id_name_map,
                             boundaries=boundary_dict,
                             dirichlet_bcs=dirichlet_bcs,
                             von_neumann_bcs=von_neuman_bcs
                             )

sim.setup_model_parameters(iv_expression=ivs,
                           sim_time=sim_time, sim_time_step=sim_time_step,
                           E_GM=E_GM, E_WM=E_WM, E_CSF=E_CSF, E_VENT=E_VENT,
                           nu_GM=nu_GM, nu_WM=nu_WM, nu_CSF=nu_CSF, nu_VENT=nu_VENT,
                           D_GM=D_GM, D_WM=D_WM,
                           rho_GM=rho_GM, rho_WM=rho_WM,
                           coupling=coupling)

output_path = test_config.path_01_forward_simulation
fu.ensure_dir_exists(output_path)
sim.run(save_method=None ,plot=False, output_dir=output_path, clear_all=True)

