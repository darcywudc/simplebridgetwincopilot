# 直接复制并修正bridge_model_enhanced.py中的缩进问题
# 这是快速修复方案

import numpy as np
import pandas as pd
import xara
import logging

class BridgeModelXara:
    """
    A class to model a bridge using the xara/OpenSees framework, 
    with enhanced capabilities for handling complex support conditions and loads.
    """
    
    def __init__(self, num_spans, span_lengths, pier_start_position, 
                 pier_heights, num_elements_per_span, support_configs,
                 E, section_height, section_width, density):
        
        # --- MODEL INITIALIZATION ---
        self.model = xara.Model()
        self.model.model('basic', '-ndm', 2, '-ndf', 3)
        
        # Validate inputs
        if len(span_lengths) != num_spans or len(num_elements_per_span) != num_spans:
            raise ValueError("Mismatch between num_spans and length of span_lengths or num_elements_per_span")

        # Core Parameters
        self.num_spans = num_spans
        self.span_lengths = span_lengths
        self.pier_start_position = pier_start_position
        self.pier_heights = pier_heights
        self.num_elements_per_span = num_elements_per_span
        self.support_configs = support_configs
        self.E = E
        self.section_height = section_height
        self.section_width = section_width
        self.density = density
        self.total_length = sum(span_lengths)

        # Calculate section properties
        self.A = self.section_width * self.section_height
        self.I = (self.section_width * self.section_height**3) / 12

        # Node and element storage
        self.nodes = []
        self.elements = []
        self.support_data = {}
        
        # Load management
        self.load_pattern_id = 1
        self.time_series_id = 1
        self.loads = []  # Store additional loads
        
        # Build the model
        self._create_model_geometry()
        self._define_materials_and_sections()
        self._create_elements()
        self._create_supports()
        
    def _create_model_geometry(self):
        """
        Creates all nodes for the bridge model.
        """
        print(f"DEBUG: Creating all beam nodes at reference Y-elevation: 8.0000m")
        
        x_pos = self.pier_start_position
        node_id = 1
        
        for i in range(self.num_spans):
            span_len = self.span_lengths[i]
            num_elems = self.num_elements_per_span[i]
            dx = span_len / num_elems
            
            # Create nodes for the span
            for j in range(num_elems):
                if not any(n[1] == x_pos for n in self.nodes):
                    self.model.node(node_id, x_pos, 8.0)
                    self.nodes.append((node_id, x_pos, 8.0))
                    node_id += 1
                x_pos += dx
        
        # Add the final node at the end of the last span
        if not any(n[1] == x_pos for n in self.nodes):
            self.model.node(node_id, x_pos, 8.0)
            self.nodes.append((node_id, x_pos, 8.0))

    def _define_materials_and_sections(self):
        """Define material and section properties for the bridge beam."""
        self.model.geomTransf('Linear', 1)
        self.model.section('Elastic', 1, self.E, self.A, self.I)

    def _create_elements(self):
        """Create beam elements connecting the previously defined nodes."""
        for i in range(len(self.nodes) - 1):
            ele_id = i + 1
            node_i = self.nodes[i][0]
            node_j = self.nodes[i+1][0]
            self.model.element('elasticBeamColumn', ele_id, node_i, node_j, 1, 1)
            self.elements.append((ele_id, node_i, node_j))
            
    def _find_node_at(self, x_pos, tolerance=1e-5):
        """Find a node at a given x-position."""
        for node_id, nx, _ in self.nodes:
            if abs(nx - x_pos) < tolerance:
                return node_id
        return None

    def _create_supports(self):
        """
        Creates supports using the 'Forced Fit' geometric method.
        """
        num_piers = self.num_spans + 1
        pier_positions = [self.pier_start_position] + [self.pier_start_position + sum(self.span_lengths[:i+1]) for i in range(self.num_spans)]
        
        print(f"DEBUG: Creating supports for {num_piers} piers using 'Forced Fit' geometric method.")

        for i in range(num_piers):
            pier_pos = pier_positions[i]
            pier_height = self.pier_heights[i]
            bridge_node_id = self._find_node_at(pier_pos)
            
            if bridge_node_id is None:
                print(f"WARNING: No node found at pier position {pier_pos}m. Skipping support creation.")
                continue

            print(f"DEBUG: Creating support for pier_{i+1} at X={pier_pos:.2f}m. Bridge node {bridge_node_id} (Y=8.0000) -> Ground (Y={pier_height:.4f})")
            
            ground_node_id = 10000 + bridge_node_id
            self.model.node(ground_node_id, pier_pos, pier_height)
            self.model.fix(ground_node_id, 1, 1, 1)
            
            # Get configuration by index (if pier_id not available)
            if i < len(self.support_configs):
                config = self.support_configs[i]
            else:
                print(f"WARNING: No support configuration found for pier {i+1}. Skipping.")
                continue

            kx, ky, kr = config['kx'], config['ky'], config['kr']
            
            mat_x, mat_y, mat_r = 20000 + i, 30000 + i, 40000 + i
            ele_x, ele_y, ele_r = 50000 + i, 60000 + i, 70000 + i

            self.model.uniaxialMaterial('Elastic', mat_x, kx if kx > 0 else 1e-9)
            self.model.uniaxialMaterial('Elastic', mat_y, ky)
            self.model.uniaxialMaterial('Elastic', mat_r, kr if kr > 0 else 1e-9)

            self.model.element('zeroLength', ele_x, bridge_node_id, ground_node_id, '-mat', mat_x, '-dir', 1)
            self.model.element('zeroLength', ele_y, bridge_node_id, ground_node_id, '-mat', mat_y, '-dir', 2)
            self.model.element('zeroLength', ele_r, bridge_node_id, ground_node_id, '-mat', mat_r, '-dir', 3)
            
            self.support_data[bridge_node_id] = {
                'ground_node_id': ground_node_id, 
                'spring_eles': {'x': ele_x, 'y': ele_y, 'r': ele_r},
                'config': config
            }

        print(f"DEBUG: Successfully created {len(self.support_data)} supports.")

    def run_analysis(self):
        """
        Run the complete structural analysis.
        """
        try:
            print("\n--- Starting New Analysis Run ---")
            
            self.model.wipeAnalysis()
            self._apply_loads()
            
            print("DEBUG: Model constructed. Starting OpenSees analysis...")
            self.model.constraints('Plain')
            self.model.numberer('RCM')
            self.model.system('BandGeneral')
            self.model.test('NormDispIncr', 1.0e-6, 10)
            self.model.algorithm('Linear')
            self.model.integrator('LoadControl', 1.0)
            self.model.analysis('Static')
            
            ok = self.model.analyze(1)
            
            if ok != 0:
                print("ERROR: OpenSees analysis failed to converge.")
                return {'analysis_ok': False}

            print("DEBUG: OpenSees analysis completed successfully.")
            self._last_results = self._extract_results()
            return self._last_results.get('analysis_ok', False)

        except Exception as e:
            print(f"FATAL ERROR in analysis run: {e}")
            import traceback
            traceback.print_exc()
            return {'analysis_ok': False}

    def _extract_results(self):
        """Extracts and processes results from the analysis."""
        # Get all reactions
        self.model.reactions()
        
        reactions_kn = []
        for bridge_node_id, data in self.support_data.items():
            # Get reaction from ground node
            ground_node_id = data['ground_node_id']
            reaction = self.model.nodeReaction(ground_node_id)
            
            # Handle different possible return formats
            if isinstance(reaction, (list, tuple)):
                force_y = reaction[1]  # Y-direction force (index 1)
            else:
                force_y = reaction  # If it's a single value
                
            reactions_kn.append([0, force_y / 1000.0, 0])  # [Fx, Fy, Mz] in kN
        
        # reactions_kn is already in correct order based on bridge_node_id iteration
        
        return {
            'analysis_ok': True,
            'reactions_kn': reactions_kn
        }
        
    def _apply_loads(self):
        """Applies all defined loads to the model."""
        self.model.timeSeries('Linear', self.time_series_id)
        self.model.pattern('Plain', self.load_pattern_id, self.time_series_id)
        self._add_self_weight()
        self._add_additional_loads()
        
    def add_distributed_load(self, load_per_length):
        """Add distributed load to the bridge (N/m)"""
        self.loads.append(('distributed', load_per_length))
        print(f"DEBUG: Added distributed load: {load_per_length/1000:.1f} kN/m")
        
    def _add_self_weight(self):
        """Add self-weight of the bridge"""
        g = 9.81
        self_weight_per_length = -self.density * self.A * g  # N/m
        
        for ele_tag in [e[0] for e in self.elements]:
            self.model.eleLoad('-ele', ele_tag, '-type', 'beamUniform', self_weight_per_length, 0.0)
        
        print(f"DEBUG: Applied self-weight of {self_weight_per_length:.2f} N/m to pattern {self.load_pattern_id}.")
        
    def _add_additional_loads(self):
        """Add additional loads stored in self.loads"""
        for load_type, load_value in self.loads:
            if load_type == 'distributed':
                for ele_tag in [e[0] for e in self.elements]:
                    self.model.eleLoad('-ele', ele_tag, '-type', 'beamUniform', load_value, 0.0)
                print(f"DEBUG: Applied additional distributed load: {load_value/1000:.1f} kN/m")
                
    def get_reaction_summary(self):
        """Get formatted reaction summary compatible with analysis scripts"""
        # This method should be called after run_analysis()
        if not hasattr(self, '_last_results'):
            # Get current results
            self._last_results = self._extract_results()
            
        if not self._last_results.get('analysis_ok', False):
            return None
            
        reactions_kn = self._last_results['reactions_kn']
        
        # Format reactions as expected by analysis scripts
        formatted_reactions = []
        for i, reaction in enumerate(reactions_kn):
            formatted_reactions.append(reaction[1])  # Just the vertical force (Fy)
            
        total_vertical = sum(formatted_reactions)
        
        return {
            'reactions': formatted_reactions,
            'total_vertical': total_vertical,
            'analysis_ok': True
        }