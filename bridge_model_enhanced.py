import numpy as np
import pandas as pd
import xara

class BridgeModelXara:
    """
    Enhanced Bridge Digital Twin Model using xara/OpenSees
    Supports configurable spans, pier positions, support types, beam properties, and reaction calculations
    
    Features:
    - Configurable number of spans (2 or 3)
    - Customizable pier starting position
    - Variable support types (Fixed, Pinned, Roller, etc.)
    - Configurable beam properties (materials, sections)
    - Support reaction calculations
    - Comprehensive tabular analysis results
    """
    
    def __init__(self, length=60.0, num_elements=30, E=30e9, section_height=1.5, 
                 section_width=1.0, density=2400, num_spans=3, pier_start_position=0.0, 
                 bearings_per_pier=2, bridge_width=15.0, support_types=None, 
                 beam_segments=None, custom_materials=None):
        """
        Initialize enhanced continuous beam bridge model with configurable supports and beams
        
        Args:
            length: Bridge length in meters (total span)
            num_elements: Number of finite elements
            E: Elastic modulus in Pa (default: 30 GPa for concrete)
            section_height: Cross-section height in meters
            section_width: Cross-section width in meters  
            density: Material density in kg/m³
            num_spans: Number of spans (2 or 3)
            pier_start_position: Starting position of first pier (0.0 to 1.0)
            bearings_per_pier: Number of bearings per pier in transverse direction
            bridge_width: Bridge width in transverse direction in meters (default: 15m)
            support_types: List of support type configs for each pier
            beam_segments: List of beam segment configurations
            custom_materials: Dictionary of custom material properties
        """
        self.length = length
        self.num_elements = num_elements
        self.E = E
        self.section_height = section_height
        self.section_width = section_width
        self.density = density
        self.num_spans = num_spans
        self.pier_start_position = pier_start_position
        self.bearings_per_pier = bearings_per_pier
        self.bridge_width = bridge_width  # Bridge transverse width
        
        # NEW: Support configuration
        self.support_types = support_types or self._default_support_types()
        
        # NEW: Beam segment configuration  
        self.beam_segments = beam_segments or self._default_beam_segments()
        
        # NEW: Custom materials
        self.custom_materials = custom_materials or {}
        
        # Calculate section properties
        self.A = section_height * section_width  # Cross-sectional area
        self.I = (section_width * section_height**3) / 12  # Moment of inertia
        
        # Generate pier configurations based on span configuration
        self.num_piers = num_spans + 1  # Always one more pier than spans
        self.pier_positions = self._generate_pier_positions()
        self.bearing_spacing = 2.0  # Transverse spacing between bearings (m)
        
        # Model and tracking variables (model will be created fresh for each analysis)
        self.model = None
        
        # Node and element tracking
        self.nodes = []
        self.elements = []
        self.loads = []
        self.piers = []
        
        # Analysis results
        self.displacements = []
        self.moments = []
        self.shears = []
        self.reactions = []  # NEW: Support reactions
        
        # Load pattern counters
        self.load_pattern_id = 1
        self.time_series_id = 1
        
        # Create initial model structure
        self._setup_bridge_geometry()
    
    def _default_support_types(self):
        """Generate default support type configuration"""
        if self.num_spans == 2:
            return [
                {'type': 'fixed_pin', 'dx': 1, 'dy': 1, 'rz': 0},      # Left abutment
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0},         # Center pier
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0}          # Right abutment
            ]
        else:  # 3 spans
            return [
                {'type': 'fixed_pin', 'dx': 1, 'dy': 1, 'rz': 0},      # Left abutment
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0},         # First pier
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0},         # Second pier
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0}          # Right abutment
            ]
    
    def _default_beam_segments(self):
        """Generate default beam segment configuration"""
        return [
            {
                'start_ratio': 0.0,
                'end_ratio': 1.0,
                'material_id': 1,
                'E': self.E,
                'section_height': self.section_height,
                'section_width': self.section_width,
                'density': self.density,
                'description': 'Main bridge deck - C30 concrete'
            }
        ]
    
    def _generate_pier_positions(self):
        """Generate pier positions based on span configuration"""
        if self.num_spans == 2:
            # 2-span bridge: left abutment, center pier, right abutment
            if self.pier_start_position == 0.0:
                return [0.0, 0.5, 1.0]  # Default symmetric 2-span
            else:
                # Custom starting position for 2-span
                available_length = 1.0 - self.pier_start_position
                center_pos = self.pier_start_position + available_length / 2
                return [self.pier_start_position, center_pos, 1.0]
        elif self.num_spans == 3:
            # 3-span bridge: left abutment, 2 intermediate piers, right abutment
            if self.pier_start_position == 0.0:
                return [0.0, 0.33, 0.67, 1.0]  # Default symmetric 3-span
            else:
                # Custom starting position for 3-span
                available_length = 1.0 - self.pier_start_position
                span_length = available_length / 3
                pos1 = self.pier_start_position
                pos2 = pos1 + span_length
                pos3 = pos2 + span_length
                return [pos1, pos2, pos3, 1.0]
        else:
            raise ValueError("Only 2 or 3 spans are supported")
    
    def _setup_bridge_geometry(self):
        """Set up bridge geometry and structure (without OpenSees model)"""
        # Create nodes along the bridge deck
        num_nodes = self.num_elements + 1
        dx = self.length / self.num_elements
        
        for i in range(num_nodes):
            x = i * dx
            node_id = i + 1  # OpenSees uses 1-based indexing
            self.nodes.append((node_id, x, 0.0))
        
        # Set up pier information
        for i, pier_pos in enumerate(self.pier_positions):
            pier_x = pier_pos * self.length
            pier_info = {
                'id': i,
                'x_coord': pier_x,
                'position': pier_pos,
                'type': self._get_pier_type(i),
                'bearings_count': self.bearings_per_pier,
                'support_config': self.support_types[i] # Add support config to pier info
            }
            self.piers.append(pier_info)
    
    def _get_pier_type(self, pier_index):
        """Determine pier type based on position"""
        if pier_index == 0:
            return "abutment_left"
        elif pier_index == len(self.pier_positions) - 1:
            return "abutment_right" 
        else:
            return "pier_intermediate"
    
    def _create_fresh_model(self):
        """Create a fresh OpenSees model instance for thread-safe analysis"""
        # Create new model instance
        self.model = xara.Model()
        
        # Initialize OpenSees model space
        self.model.model('basic', '-ndm', 2, '-ndf', 3)
        
        # Create nodes
        for node_id, x, y in self.nodes:
            self.model.node(node_id, x, y)
        
        # Create material
        self.model.uniaxialMaterial('Elastic', 1, self.E)
        
        # Create geometric transformation
        self.model.geomTransf('Linear', 1)
        
        # Create beam elements
        for i in range(self.num_elements):
            element_id = i + 1
            node_i = i + 1
            node_j = i + 2
            
            self.model.element('elasticBeamColumn', element_id, node_i, node_j, 
                             self.A, self.E, self.I, 1)
            self.elements.append((element_id, node_i, node_j))
        
        # Define pier supports
        self._create_pier_supports()
    
    def _create_pier_supports(self):
        """Create pier supports with appropriate boundary conditions for continuous beam bridge"""
        for i, pier_pos in enumerate(self.pier_positions):
            # Find the closest node to pier position
            pier_x = pier_pos * self.length
            node_spacing = self.length / self.num_elements
            pier_node = int(round(pier_x / node_spacing)) + 1  # OpenSees 1-based
            pier_node = max(1, min(pier_node, len(self.nodes)))
            
            # Update pier information with actual node
            if i < len(self.piers):
                self.piers[i]['node'] = pier_node
                self.piers[i]['type'] = self._get_pier_type(i)
            
            # Add support constraints based on support configuration
            support_config = self.support_types[i]
            
            # Apply constraints directly from configuration
            self.model.fix(pier_node, support_config['dx'], support_config['dy'], support_config['rz'])
            
            # Set descriptive constraint type based on support configuration
            if support_config['type'] == 'fixed_pin':
                self.piers[i]['constraint_type'] = 'Fixed Pin (dx=0, dy=0, rz=free)'
            elif support_config['type'] == 'roller':
                self.piers[i]['constraint_type'] = 'Roller (dx=free, dy=0, rz=free)'
            elif support_config['type'] == 'fixed':
                self.piers[i]['constraint_type'] = 'Fixed Support (dx=0, dy=0, rz=0)'
            elif support_config['type'] == 'spring_vertical':
                self.piers[i]['constraint_type'] = 'Vertical Spring (dx=free, dy=elastic, rz=free)'
            else:
                # Generic description based on constraints
                dx_desc = "固定" if support_config['dx'] == 1 else "自由"
                dy_desc = "固定" if support_config['dy'] == 1 else "自由"
                rz_desc = "固定" if support_config['rz'] == 1 else "自由"
                self.piers[i]['constraint_type'] = f'Custom ({dx_desc}-{dy_desc}-{rz_desc})'
    
    def _add_self_weight(self):
        """Add self-weight to the model as distributed load"""
        weight_per_length = self.density * 9.81 * self.A  # N/m
        
        # Create time series and load pattern for self-weight
        ts_id = self.time_series_id
        pattern_id = self.load_pattern_id
        
        self.model.timeSeries('Linear', ts_id)
        self.model.pattern('Plain', pattern_id, ts_id)
        
        # Apply elemental loads (distributed load)
        for i in range(self.num_elements):
            element_id = i + 1
            # Apply negative load (downward)
            self.model.eleLoad('-ele', element_id, '-type', '-beamUniform', -weight_per_length)
        
        # Don't store self-weight in loads list to avoid duplication
        self.time_series_id += 1
        self.load_pattern_id += 1
    
    def _apply_loads(self):
        """Apply all stored loads to the current model"""
        # Reset load counters for fresh application
        self.time_series_id = 1
        self.load_pattern_id = 1
        
        # Always add self-weight first
        self._add_self_weight()
        
        # Apply all other stored loads
        for load in self.loads:
            if load[0] == 'point_load':
                magnitude, position_ratio = load[1], load[2]
                self._apply_point_load(magnitude, position_ratio)
            elif load[0] == 'distributed':
                magnitude = load[1]
                self._apply_distributed_load(magnitude)
    
    def _apply_point_load(self, magnitude, position_ratio):
        """Apply a point load to the model"""
        # Find closest node
        position_x = position_ratio * self.length
        node_spacing = self.length / self.num_elements
        target_node = int(round(position_x / node_spacing)) + 1
        target_node = max(1, min(target_node, len(self.nodes)))
        
        # Create new load pattern
        ts_id = self.time_series_id
        pattern_id = self.load_pattern_id
        
        self.model.timeSeries('Linear', ts_id)
        self.model.pattern('Plain', pattern_id, ts_id)
        
        # Apply nodal load (Fx=0, Fy=magnitude, Mz=0)
        self.model.load(target_node, 0.0, magnitude, 0.0)
        
        self.time_series_id += 1
        self.load_pattern_id += 1
    
    def _apply_distributed_load(self, magnitude):
        """Apply a distributed load to the model"""
        # Create new load pattern
        ts_id = self.time_series_id
        pattern_id = self.load_pattern_id
        
        self.model.timeSeries('Linear', ts_id)
        self.model.pattern('Plain', pattern_id, ts_id)
        
        # Apply to all elements
        for i in range(self.num_elements):
            element_id = i + 1
            self.model.eleLoad('-ele', element_id, '-type', '-beamUniform', magnitude)
        
        self.time_series_id += 1
        self.load_pattern_id += 1
    
    def add_point_load(self, magnitude, position_ratio):
        """
        Add point load at specified position
        
        Args:
            magnitude: Load magnitude in N (negative for downward)
            position_ratio: Position along bridge length (0.0 to 1.0)
        """
        # Store load information for later application
        self.loads.append(('point_load', magnitude, position_ratio))
    
    def add_distributed_load(self, magnitude):
        """
        Add uniformly distributed load over entire bridge
        
        Args:
            magnitude: Load intensity in N/m (negative for downward)
        """
        # Store load information for later application
        self.loads.append(('distributed', magnitude))
    
    def add_vehicle_load(self, axle_loads, axle_spacing, leading_position):
        """
        Add vehicle load with multiple axles
        
        Args:
            axle_loads: List of axle loads in N
            axle_spacing: List of distances between axles in m
            leading_position: Position ratio of leading axle (0.0 to 1.0)
        """
        current_pos = leading_position
        
        for i, load in enumerate(axle_loads):
            if current_pos <= 1.0:
                self.add_point_load(load, current_pos)
            
            # Move to next axle position
            if i < len(axle_spacing):
                current_pos += axle_spacing[i] / self.length
    
    def run_analysis(self):
        """
        Run static analysis using OpenSees and extract results including support reactions
        
        Returns:
            dict: Analysis results including displacements, moments, shears, and reactions
        """
        try:
            # Clear previous results
            self.displacements = []
            self.moments = []
            self.shears = []
            self.reactions = []
            
            # Create fresh model instance for thread-safe analysis
            self._create_fresh_model()
            
            # Apply all stored loads to the fresh model
            self._apply_loads()
            
            # Setup analysis with more robust settings
            self.model.system('ProfileSPD')
            self.model.numberer('Plain')
            self.model.constraints('Transformation')  # More robust constraint handler
            self.model.integrator('LoadControl', 1.0)
            self.model.algorithm('Linear')
            self.model.analysis('Static')
            
            # Run analysis
            ok = self.model.analyze(1)
            
            if ok != 0:
                print("Warning: Analysis did not converge perfectly")
            
            # Extract nodal displacements
            node_displacements = []
            for i in range(len(self.nodes)):
                node_id = i + 1
                try:
                    disp = self.model.nodeDisp(node_id, 2)  # Y-displacement
                    node_displacements.append(disp)
                except:
                    node_displacements.append(0.0)
            
            # Extract element forces
            element_moments = []
            element_shears = []
            element_moments_i = []  # Moments at start of elements
            element_moments_j = []  # Moments at end of elements
            
            for i in range(self.num_elements):
                element_id = i + 1
                try:
                    # Get element forces: [N1, V1, M1, N2, V2, M2]
                    forces = self.model.eleForce(element_id)
                    if len(forces) >= 6:
                        moment_i = forces[2]  # Moment at node i (start)
                        moment_j = forces[5]  # Moment at node j (end)
                        shear_i = forces[1]   # Shear at node i
                        
                        # Store both end moments for accurate moment diagram
                        element_moments_i.append(moment_i)
                        element_moments_j.append(moment_j)
                        
                        # For compatibility, also store average (but prefer using individual moments)
                        avg_moment = (moment_i + moment_j) / 2
                        element_moments.append(avg_moment)
                        element_shears.append(shear_i)
                    else:
                        element_moments_i.append(0.0)
                        element_moments_j.append(0.0)
                        element_moments.append(0.0)
                        element_shears.append(0.0)
                except Exception as e:
                    print(f"Warning: Could not extract forces for element {element_id}: {e}")
                    element_moments_i.append(0.0)
                    element_moments_j.append(0.0)
                    element_moments.append(0.0)
                    element_shears.append(0.0)
            
            # Extract support reactions
            support_reactions = []
            
            # CRITICAL: Must call reactions() before extracting node reactions
            try:
                self.model.reactions()
            except Exception as e:
                print(f"Warning: reactions() command failed: {e}")
            
            for i, pier in enumerate(self.piers):
                if 'node' in pier:
                    node_id = pier['node']
                    try:
                        # Get reaction forces at support nodes: [Fx, Fy, Mz]
                        reaction = self.model.nodeReaction(node_id)
                        if len(reaction) >= 3:
                            reaction_data = {
                                'pier_id': i,
                                'pier_type': pier['type'],
                                'node_id': node_id,
                                'x_coord': pier['x_coord'],
                                'Fx': reaction[0],  # Horizontal reaction (N)
                                'Fy': reaction[1],  # Vertical reaction (N) 
                                'Mz': reaction[2],  # Moment reaction (N⋅m)
                                'support_type': pier['support_config']['type'],
                                'constraint_type': pier.get('constraint_type', 'Unknown')
                            }
                            support_reactions.append(reaction_data)
                        else:
                            # Default zero reaction if extraction fails
                            reaction_data = {
                                'pier_id': i,
                                'pier_type': pier['type'],
                                'node_id': node_id,
                                'x_coord': pier['x_coord'],
                                'Fx': 0.0,
                                'Fy': 0.0,
                                'Mz': 0.0,
                                'support_type': pier['support_config']['type'],
                                'constraint_type': pier.get('constraint_type', 'Unknown')
                            }
                            support_reactions.append(reaction_data)
                    except Exception as e:
                        print(f"Warning: Could not extract reaction for pier {i} node {node_id}: {e}")
                        # Add zero reaction as fallback
                        reaction_data = {
                            'pier_id': i,
                            'pier_type': pier['type'],
                            'node_id': node_id,
                            'x_coord': pier['x_coord'],
                            'Fx': 0.0,
                            'Fy': 0.0,
                            'Mz': 0.0,
                            'support_type': pier['support_config']['type'],
                            'constraint_type': pier.get('constraint_type', 'Unknown')
                        }
                        support_reactions.append(reaction_data)
            
            # Store results
            self.displacements = node_displacements
            self.moments = element_moments
            self.shears = element_shears
            self.reactions = support_reactions
            
            return {
                'analysis_ok': ok == 0,
                'displacements': node_displacements,
                'moments': element_moments,
                'moments_i': element_moments_i,  # Start moments for accurate plotting
                'moments_j': element_moments_j,  # End moments for accurate plotting
                'shears': element_shears,
                'reactions': support_reactions,  # NEW: Support reactions
                'max_displacement': max(abs(d) for d in node_displacements),
                'max_moment': max(abs(m) for m in element_moments) if element_moments else 0,
                'max_shear': max(abs(s) for s in element_shears) if element_shears else 0,
                'max_reaction_vertical': max(abs(r['Fy']) for r in support_reactions) if support_reactions else 0,
                'max_reaction_horizontal': max(abs(r['Fx']) for r in support_reactions) if support_reactions else 0
            }
            
        except Exception as e:
            print(f"Analysis error: {e}")
            return {
                'analysis_ok': False,
                'error': str(e),
                'displacements': [],
                'moments': [],
                'shears': [],
                'reactions': [],
                'max_displacement': 0,
                'max_moment': 0,
                'max_shear': 0,
                'max_reaction_vertical': 0,
                'max_reaction_horizontal': 0
            }
    
    def get_analysis_tables(self):
        """
        Generate comprehensive analysis tables for engineering review
        
        Returns:
            dict: Dictionary containing all analysis tables
        """
        tables = {
            'geometry': self._get_geometry_tables(),
            'loads': self._get_load_tables(),
            'results': self._get_result_tables(),
            'verification': self._get_verification_tables()
        }
        return tables
    
    def _get_geometry_tables(self):
        """Generate geometry information tables"""
        # Nodes table
        nodes_data = []
        for node_id, x, y in self.nodes:
            # Check if this node is a support
            constraint = "Free"
            for pier in self.piers:
                if 'node' in pier and pier['node'] == node_id:
                    if pier['type'] in ['abutment_left', 'abutment_right']:
                        constraint = "Fixed (dx=0, dy=0, rz=0)"
                    else:
                        constraint = "Roller (dy=0)"
                    break
            
            nodes_data.append({
                '节点号': node_id,
                'X坐标 (m)': round(x, 2),
                'Y坐标 (m)': y,
                '约束条件': constraint
            })
        
        nodes_df = pd.DataFrame(nodes_data)
        
        # Elements table
        elements_data = []
        dx = self.length / self.num_elements
        for element_id, node_i, node_j in self.elements:
            elements_data.append({
                '单元号': element_id,
                'I节点': node_i,
                'J节点': node_j,
                '长度 (m)': round(dx, 2),
                '截面积 (m²)': round(self.A, 4),
                '惯性矩 (m⁴)': round(self.I, 6),
                '弹性模量 (GPa)': round(self.E/1e9, 1)
            })
        
        elements_df = pd.DataFrame(elements_data)
        
        # Piers table
        piers_data = []
        for pier in self.piers:
            piers_data.append({
                '支座号': pier['id'] + 1,
                '位置 (m)': round(pier['x_coord'], 2),
                '相对位置': f"{pier['position']:.1%}",
                '支座类型': pier['type'],
                '横向支座数': pier['bearings_count'],
                '支座间距 (m)': self.bearing_spacing
            })
        
        piers_df = pd.DataFrame(piers_data)
        
        return {
            'nodes': nodes_df,
            'elements': elements_df,
            'piers': piers_df
        }
    
    def _get_load_tables(self):
        """Generate load information tables"""
        # Point loads table
        point_loads_data = []
        load_counter = 1
        for load in self.loads:
            if load[0] == 'point_load':
                magnitude, position = load[1], load[2]
                # Find target node
                position_x = position * self.length
                node_spacing = self.length / self.num_elements
                target_node = int(round(position_x / node_spacing)) + 1
                
                point_loads_data.append({
                    '荷载号': load_counter,
                    '荷载值 (kN)': round(magnitude/1000, 1),
                    '位置 (m)': round(position_x, 2),
                    '相对位置': f"{position:.1%}",
                    '作用节点': target_node
                })
                load_counter += 1
        
        point_loads_df = pd.DataFrame(point_loads_data)
        
        # Distributed loads table
        dist_loads_data = []
        for load in self.loads:
            if load[0] == 'distributed':
                magnitude = load[1]
                dist_loads_data.append({
                    '荷载类型': '均布荷载',
                    '荷载强度 (kN/m)': round(magnitude/1000, 2),
                    '作用范围': '全桥',
                    '总荷载 (kN)': round(magnitude * self.length / 1000, 1)
                })
            elif load[0] == 'self_weight':
                magnitude = load[1]
                dist_loads_data.append({
                    '荷载类型': '结构自重',
                    '荷载强度 (kN/m)': round(-magnitude/1000, 2),
                    '作用范围': '全桥',
                    '总荷载 (kN)': round(-magnitude * self.length / 1000, 1)
                })
        
        dist_loads_df = pd.DataFrame(dist_loads_data)
        
        return {
            'point_loads': point_loads_df,
            'distributed_loads': dist_loads_df
        }
    
    def _get_result_tables(self):
        """Generate analysis results tables"""
        # Nodal displacements table
        disp_data = []
        for i, (node_id, x, y) in enumerate(self.nodes):
            if i < len(self.displacements):
                displacement = self.displacements[i]
            else:
                displacement = 0.0
            
            disp_data.append({
                '节点号': node_id,
                'X坐标 (m)': round(x, 2),
                'Y位移 (mm)': round(displacement * 1000, 3),
                '位移幅值 (mm)': round(abs(displacement) * 1000, 3)
            })
        
        disp_df = pd.DataFrame(disp_data)
        
        # Element forces table
        forces_data = []
        dx = self.length / self.num_elements
        for i, (element_id, node_i, node_j) in enumerate(self.elements):
            x_center = (node_i - 1 + 0.5) * dx
            
            if i < len(self.moments):
                moment = self.moments[i]
            else:
                moment = 0.0
                
            if i < len(self.shears):
                shear = self.shears[i]
            else:
                shear = 0.0
            
            forces_data.append({
                '单元号': element_id,
                'X位置 (m)': round(x_center, 2),
                '弯矩 (kN·m)': round(moment/1000, 2),
                '剪力 (kN)': round(shear/1000, 2)
            })
        
        forces_df = pd.DataFrame(forces_data)
        
        return {
            'displacements': disp_df,
            'forces': forces_df
        }
    
    def _get_verification_tables(self):
        """Generate engineering verification tables"""
        # Maximum values summary
        max_disp = max(abs(d) for d in self.displacements) if self.displacements else 0
        max_moment = max(abs(m) for m in self.moments) if self.moments else 0
        max_shear = max(abs(s) for s in self.shears) if self.shears else 0
        
        # Find locations of maximum values
        max_disp_idx = np.argmax([abs(d) for d in self.displacements]) if self.displacements else 0
        max_moment_idx = np.argmax([abs(m) for m in self.moments]) if self.moments else 0
        max_shear_idx = np.argmax([abs(s) for s in self.shears]) if self.shears else 0
        
        dx = self.length / self.num_elements
        max_disp_pos = max_disp_idx * dx
        max_moment_pos = (max_moment_idx + 0.5) * dx
        max_shear_pos = (max_shear_idx + 0.5) * dx
        
        summary_data = [{
            '项目': '最大位移',
            '数值': f"{max_disp*1000:.2f} mm",
            '位置 (m)': round(max_disp_pos, 2),
            '相对位置': f"{max_disp_pos/self.length:.1%}"
        }, {
            '项目': '最大弯矩',
            '数值': f"{max_moment/1000:.2f} kN·m",
            '位置 (m)': round(max_moment_pos, 2),
            '相对位置': f"{max_moment_pos/self.length:.1%}"
        }, {
            '项目': '最大剪力',
            '数值': f"{max_shear/1000:.2f} kN",
            '位置 (m)': round(max_shear_pos, 2),
            '相对位置': f"{max_shear_pos/self.length:.1%}"
        }]
        
        summary_df = pd.DataFrame(summary_data)
        
        # Engineering limits check
        span_length = self.length / self.num_spans
        disp_limit = span_length / 250  # L/250 deflection limit
        
        checks_data = [{
            '检验项目': '挠度限值检查',
            '规范要求': f'≤ L/{250} = {disp_limit*1000:.1f} mm',
            '计算值': f'{max_disp*1000:.2f} mm',
            '检验结果': '✓ 满足' if max_disp <= disp_limit else '✗ 超限'
        }, {
            '检验项目': '桥梁跨数',
            '规范要求': '2跨或3跨连续梁',
            '计算值': f'{self.num_spans}跨',
            '检验结果': '✓ 满足'
        }, {
            '检验项目': '支座配置',
            '规范要求': '每墩≥2个横向支座',
            '计算值': f'{self.bearings_per_pier}个/墩',
            '检验结果': '✓ 满足' if self.bearings_per_pier >= 2 else '⚠ 建议增加'
        }]
        
        checks_df = pd.DataFrame(checks_data)
        
        return {
            'summary': summary_df,
            'checks': checks_df
        }
    
    # Compatibility methods for existing interface
    def get_node_coordinates(self):
        """Get node coordinates for visualization"""
        x_coords = [x for _, x, _ in self.nodes]
        y_coords = [y for _, _, y in self.nodes]
        return x_coords, y_coords
    
    def get_deformed_coordinates(self, scale_factor=100):
        """Get deformed coordinates for visualization"""
        x_coords = [x for _, x, _ in self.nodes]
        y_deformed = []
        
        for i, (_, x, y) in enumerate(self.nodes):
            if i < len(self.displacements):
                y_def = y + self.displacements[i] * scale_factor
            else:
                y_def = y
            y_deformed.append(y_def)
        
        return x_coords, y_deformed
    
    def get_element_centers(self):
        """Get element center coordinates for force plotting"""
        dx = self.length / self.num_elements
        return [i * dx + dx/2 for i in range(self.num_elements)]
    
    def get_support_type_options(self):
        """Get available support type options"""
        return {
            'fixed_pin': {
                'name': '固定铰接 (Fixed Pin)',
                'description': '限制水平和竖向位移，允许转动',
                'constraints': {'dx': 1, 'dy': 1, 'rz': 0}
            },
            'roller': {
                'name': '滑动支座 (Roller)',
                'description': '仅限制竖向位移',
                'constraints': {'dx': 0, 'dy': 1, 'rz': 0}
            },
            'fixed': {
                'name': '固定支座 (Fixed)',
                'description': '限制所有位移和转动',
                'constraints': {'dx': 1, 'dy': 1, 'rz': 1}
            },
            'spring_vertical': {
                'name': '竖向弹性支座 (Vertical Spring)',
                'description': '竖向弹性支撑，其他方向自由',
                'constraints': {'dx': 0, 'dy': 0, 'rz': 0}  # Special handling needed
            }
        }
    
    def get_beam_material_options(self):
        """Get available beam material options"""
        return {
            'C30': {
                'name': 'C30混凝土',
                'E': 30e9,  # Pa
                'density': 2400,  # kg/m³
                'description': '标准C30混凝土'
            },
            'C40': {
                'name': 'C40混凝土',
                'E': 32.5e9,
                'density': 2450,
                'description': '高强C40混凝土'
            },
            'C50': {
                'name': 'C50混凝土',
                'E': 34.5e9,
                'density': 2500,
                'description': '高强C50混凝土'
            },
            'steel': {
                'name': '结构钢',
                'E': 200e9,
                'density': 7850,
                'description': 'Q345钢材'
            },
            'prestressed': {
                'name': '预应力混凝土',
                'E': 36e9,
                'density': 2500,
                'description': '预应力混凝土梁'
            }
        }
    
    def validate_support_configuration(self, support_configs):
        """
        Validate support configuration for structural stability
        
        Args:
            support_configs: List of support configurations
            
        Returns:
            dict: Validation results with warnings and errors
        """
        warnings = []
        errors = []
        
        if len(support_configs) != self.num_piers:
            errors.append(f"支座数量({len(support_configs)})与墩台数量({self.num_piers})不匹配")
        
        # Check for minimum support requirements
        fixed_supports = sum(1 for config in support_configs if config.get('dx', 0) == 1)
        vertical_supports = sum(1 for config in support_configs if config.get('dy', 0) == 1)
        
        if fixed_supports == 0:
            errors.append("至少需要一个固定支座以防止结构水平滑移")
        
        if vertical_supports < 2:
            errors.append("至少需要两个竖向支座以保证结构稳定")
        
        # Check for over-constraint
        total_constraints = sum(
            config.get('dx', 0) + config.get('dy', 0) + config.get('rz', 0) 
            for config in support_configs
        )
        
        if total_constraints > 3:
            warnings.append("支座约束可能过多，建议检查是否存在多余约束")
        
        return {
            'valid': len(errors) == 0,
            'warnings': warnings,
            'errors': errors
        }
    
    def get_reaction_summary(self):
        """
        Get summary of support reactions
        
        Returns:
            dict: Summary of reaction forces and moments
        """
        if not self.reactions:
            return {'total_vertical': 0, 'total_horizontal': 0, 'total_moment': 0}
        
        total_vertical = sum(r['Fy'] for r in self.reactions)
        total_horizontal = sum(r['Fx'] for r in self.reactions)
        total_moment = sum(r['Mz'] for r in self.reactions)
        
        return {
            'total_vertical': total_vertical,
            'total_horizontal': total_horizontal,
            'total_moment': total_moment,
            'reactions_count': len(self.reactions),
            'max_vertical': max(abs(r['Fy']) for r in self.reactions),
            'max_horizontal': max(abs(r['Fx']) for r in self.reactions),
            'reactions_by_pier': self.reactions
        } 