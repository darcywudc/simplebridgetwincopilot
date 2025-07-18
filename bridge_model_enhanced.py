import numpy as np
import pandas as pd
import xara
import logging

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
                 beam_segments=None, custom_materials=None, pier_heights=None,
                 individual_bearing_config=None):
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
            pier_heights: List of pier heights in meters (default: None for automatic calculation)
            individual_bearing_config: Dictionary for individual bearing configuration
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
        
        # NEW: Pier heights configuration
        self.pier_heights = pier_heights or self._default_pier_heights()
        
        # NEW: Individual bearing configuration for precise control
        self.individual_bearing_config = individual_bearing_config or {}
        
        # Individual bearings list - each bearing is a separate entity
        self.individual_bearings = []
        
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
        
        # Generate individual bearings configuration
        self.individual_bearings = self._generate_individual_bearings()
    
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
    
    def _default_pier_heights(self):
        """Generate default pier heights based on bridge configuration"""
        # Default pier heights in meters - 产生毫米到厘米级别的高度差
        base_height = 8.0  # Base pier height
        
        if self.num_spans == 2:
            # 2-span bridge: 产生合理的毫米级高度差
            return [
                base_height,           # 8.000m
                base_height + 0.005,   # 8.005m (高5mm)
                base_height + 0.002    # 8.002m (高2mm)
            ]
        else:  # 3 spans
            # 3-span bridge: 产生合理的毫米级高度差
            return [
                base_height,           # 8.000m
                base_height + 0.008,   # 8.008m (高8mm)
                base_height + 0.015,   # 8.015m (高15mm = 1.5cm)
                base_height + 0.003    # 8.003m (高3mm)
            ]
    
    def _generate_individual_bearings(self):
        """Generate individual bearing configurations for each pier"""
        bearings = []
        
        for pier_idx, pier_pos in enumerate(self.pier_positions):
            pier_x = pier_pos * self.length
            pier_height = self.pier_heights[pier_idx] if pier_idx < len(self.pier_heights) else 8.0
            
            # Generate individual bearings for this pier
            for bearing_idx in range(self.bearings_per_pier):
                # Calculate transverse position of bearing
                if self.bearings_per_pier == 1:
                    y_offset = 0.0  # Single bearing at centerline
                else:
                    # Multiple bearings distributed across bridge width
                    spacing = self.bearing_spacing
                    total_width = (self.bearings_per_pier - 1) * spacing
                    y_offset = -total_width/2 + bearing_idx * spacing
                
                # Check for individual bearing configuration
                bearing_key = f"pier_{pier_idx}_bearing_{bearing_idx}"
                individual_config = self.individual_bearing_config.get(bearing_key, {})
                
                # Individual bearing height (default to pier height + small variation)
                bearing_height = individual_config.get('height', pier_height + np.random.normal(0, 0.002))
                
                bearing_info = {
                    'pier_index': pier_idx,
                    'bearing_index': bearing_idx,
                    'global_id': len(bearings),
                    'pier_x': pier_x,
                    'pier_y': y_offset,
                    'height': bearing_height,
                    'support_type': individual_config.get('support_type', self.support_types[pier_idx]),
                    'stiffness': individual_config.get('stiffness', None),
                    'damping': individual_config.get('damping', 0.0),
                    'bearing_key': bearing_key
                }
                
                bearings.append(bearing_info)
        
        return bearings
    
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
            pier_height = self.pier_heights[i] if i < len(self.pier_heights) else 8.0
            pier_info = {
                'id': i,
                'x_coord': pier_x,
                'position': pier_pos,
                'height': pier_height,  # NEW: Add pier height
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
        """Create pier supports using individual bearing configuration"""
        print(f"DEBUG: Creating individual bearing supports for {len(self.individual_bearings)} bearings")
        
        # 清除现有的pier支座数据，避免重复
        self.piers = []
        
        # 获取所有支座的基准高度（最低的支座高度）
        all_bearing_heights = [bearing['height'] for bearing in self.individual_bearings]
        reference_height = min(all_bearing_heights) if all_bearing_heights else 8.0
        
        # 按墩台分组处理支座
        piers_bearings = {}
        for bearing in self.individual_bearings:
            pier_idx = bearing['pier_index']
            if pier_idx not in piers_bearings:
                piers_bearings[pier_idx] = []
            piers_bearings[pier_idx].append(bearing)
        
        # 为每个墩台创建支座
        for pier_idx, bearings in piers_bearings.items():
            pier_pos = self.pier_positions[pier_idx]
            pier_x = pier_pos * self.length
            
            # 找到最接近的主梁节点
            node_spacing = self.length / self.num_elements
            main_node_id = int(round(pier_x / node_spacing)) + 1
            main_node_id = max(1, min(main_node_id, len(self.nodes)))
            
            # 计算墩台的平均高度和位移
            avg_height = np.mean([b['height'] for b in bearings])
            avg_displacement = avg_height - reference_height
            
            print(f"DEBUG: Pier {pier_idx+1} has {len(bearings)} bearings")
            print(f"DEBUG: Average height: {avg_height:.4f}m, displacement: {avg_displacement:.4f}m")
            
            # 获取支座配置（使用第一个支座的配置作为墩台配置）
            support_config = bearings[0]['support_type']
            
            # 对于主梁节点，施加约束（代表整个墩台的约束）
            if support_config['type'] == 'fixed_pin':
                self.model.fix(main_node_id, 1, 1, 0)
                constraint_type = 'Fixed Pin'
            elif support_config['type'] == 'roller':
                self.model.fix(main_node_id, 0, 1, 0)
                constraint_type = 'Roller'
            elif support_config['type'] == 'fixed':
                self.model.fix(main_node_id, 1, 1, 1)
                constraint_type = 'Fixed'
            else:
                dx = support_config['dx']
                dy = support_config['dy']
                rz = support_config['rz']
                self.model.fix(main_node_id, dx, dy, rz)
                constraint_type = f'Custom (dx={dx}, dy={dy}, rz={rz})'
            
            print(f"DEBUG: Applied {constraint_type} to main node {main_node_id}")
            
            # 创建墩台信息（包含所有支座的信息）
            pier_info = {
                'id': pier_idx,
                'pier_id': pier_idx,
                'node': main_node_id,
                'position': pier_pos,
                'x_coord': pier_x,
                'height': avg_height,
                'imposed_displacement': avg_displacement,
                'support_config': support_config,
                'constraint_type': constraint_type,
                'type': self._get_pier_type(pier_idx),
                'bearings_count': len(bearings),
                'individual_bearings': bearings  # 新增：包含所有独立支座信息
            }
            self.piers.append(pier_info)
        
        print(f"DEBUG: Created {len(self.piers)} pier supports with {len(self.individual_bearings)} individual bearings")
        print(f"DEBUG: Individual bearing configuration enabled")
    
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
        
        # Apply settlements based on pier heights
        self._apply_settlements()
        
        # Apply imposed displacements for pier height effects
        self._apply_imposed_displacements()
    
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
                print("DEBUG: reactions() command executed successfully")
            except Exception as e:
                print(f"Warning: reactions() command failed: {e}")
            
            for i, pier in enumerate(self.piers):
                if 'node' in pier:
                    node_id = pier['node']
                    try:
                        # Get reaction forces at support nodes: [Fx, Fy, Mz]
                        reaction = self.model.nodeReaction(node_id)
                        print(f"DEBUG: Pier {i+1} node {node_id} reaction: {reaction}")
                        
                        if len(reaction) >= 3:
                            # 支座反力处理：只显示正值（受压状态）
                            # 竖向反力取绝对值，水平反力根据实际情况处理
                            vertical_reaction = abs(reaction[1])  # 竖向反力始终为正（受压）
                            horizontal_reaction = reaction[0]     # 水平反力保持原符号（可能有拉压）
                            moment_reaction = reaction[2]         # 弯矩反力保持原符号
                            
                            reaction_data = {
                                'pier_id': i,
                                'pier_type': pier['type'],
                                'node_id': node_id,
                                'x_coord': pier['x_coord'],
                                'Fx': horizontal_reaction,        # 水平反力 (N)
                                'Fy': vertical_reaction,         # 竖向反力 (N) - 始终为正
                                'Mz': moment_reaction,           # 弯矩反力 (N⋅m)
                                'support_type': pier['support_config']['type'],
                                'constraint_type': pier.get('constraint_type', 'Unknown')
                            }
                            support_reactions.append(reaction_data)
                        else:
                            print(f"DEBUG: Reaction length insufficient for pier {i+1}: {len(reaction)}")
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
            
            # 计算总反力以验证平衡
            total_vertical_reaction = sum(r['Fy'] for r in support_reactions)
            total_horizontal_reaction = sum(r['Fx'] for r in support_reactions)
            print(f"DEBUG: Total vertical reaction: {total_vertical_reaction/1000:.2f} kN")
            print(f"DEBUG: Total horizontal reaction: {total_horizontal_reaction/1000:.2f} kN")
            
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
    
    def update_pier_height(self, pier_index, new_height):
        """
        Update pier height and recalculate structural response
        
        Args:
            pier_index: Index of the pier to update (0-based)
            new_height: New height in meters
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        if pier_index < 0 or pier_index >= len(self.piers):
            return False
            
        # Update pier height
        old_height = self.piers[pier_index]['height']
        self.piers[pier_index]['height'] = new_height
        self.pier_heights[pier_index] = new_height
        
        # Log the change
        logging.info(f"Updated pier {pier_index + 1} height from {old_height:.2f}m to {new_height:.2f}m")
        
        return True
    
    def get_pier_height_effects(self, pier_index, height_change):
        """
        Calculate the effects of pier height change on structural response
        
        Args:
            pier_index: Index of the pier (0-based)
            height_change: Change in height (positive = increase, negative = decrease)
            
        Returns:
            dict: Effects on moments, shears, and reactions
        """
        if pier_index < 0 or pier_index >= len(self.piers):
            return {}
            
        # The height change affects the pier's flexibility and thus the force distribution
        # Higher piers are more flexible, leading to reduced load sharing
        # This is a simplified approach - in reality, pier flexibility depends on:
        # - Pier height (h³ effect for cantilever deflection)
        # - Cross-section properties
        # - Material properties
        
        pier_info = self.piers[pier_index]
        original_height = pier_info['height']
        new_height = original_height + height_change
        
        # Calculate flexibility ratio (simplified)
        # Pier flexibility is proportional to h³ for cantilever-like behavior
        flexibility_ratio = (new_height / original_height) ** 3
        
        effects = {
            'pier_index': pier_index,
            'height_change': height_change,
            'new_height': new_height,
            'flexibility_ratio': flexibility_ratio,
            'load_redistribution_factor': 1.0 / flexibility_ratio,
            'estimated_reaction_change': f"{((1 - flexibility_ratio) * 100):.1f}%"
        }
        
        return effects
    
    def update_multiple_pier_heights(self, height_updates):
        """
        Update multiple pier heights simultaneously
        
        Args:
            height_updates: Dictionary {pier_index: new_height, ...}
            
        Returns:
            bool: True if all updates were successful
        """
        success = True
        for pier_index, new_height in height_updates.items():
            if not self.update_pier_height(pier_index, new_height):
                success = False
                logging.error(f"Failed to update pier {pier_index + 1} height to {new_height}m")
        
        return success
    
    def get_pier_height_summary(self):
        """
        Generate a summary table of pier heights and their effects
        
        Returns:
            pandas.DataFrame: Summary of pier heights and calculated effects
        """
        summary_data = []
        
        E_pier = 30e9  # Pa
        A_pier = 4.0   # m²
        
        for i, (pier, height) in enumerate(zip(self.piers, self.pier_heights)):
            # Calculate spring stiffness
            k_vertical = (E_pier * A_pier) / height
            
            # Calculate relative flexibility (higher = more flexible)
            base_height = 8.0
            flexibility_ratio = (height / base_height) ** 3
            
            # Determine pier type
            pier_type = pier.get('type', 'unknown')
            pier_name = {
                'abutment_left': '左桥台',
                'abutment_right': '右桥台', 
                'pier_intermediate': '中间墩'
            }.get(pier_type, pier_type)
            
            summary_data.append({
                '支座编号': f'墩台 {i+1}',
                '支座类型': pier_name,
                '位置 (m)': f"{pier.get('x_coord', 0):.1f}",
                '高度 (m)': f"{height:.1f}",
                '竖向刚度 (MN/m)': f"{k_vertical/1e6:.1f}",
                '柔性比': f"{flexibility_ratio:.2f}",
                '相对刚度': f"{1/flexibility_ratio:.2f}"
            })
        
        return pd.DataFrame(summary_data)
    
    def get_height_effect_analysis(self):
        """
        Analyze the structural effects of current pier height configuration
        
        Returns:
            dict: Analysis of height effects on structural behavior
        """
        if not self.pier_heights:
            return {'error': 'No pier heights defined'}
        
        analysis = {
            'height_statistics': {
                'max_height': max(self.pier_heights),
                'min_height': min(self.pier_heights),
                'avg_height': np.mean(self.pier_heights),
                'std_height': np.std(self.pier_heights),
                'height_range': max(self.pier_heights) - min(self.pier_heights)
            },
            'stiffness_analysis': [],
            'load_distribution_prediction': [],
            'structural_effects': []
        }
        
        E_pier = 30e9
        A_pier = 4.0
        
        # Calculate stiffness for each pier
        stiffness_values = []
        for i, height in enumerate(self.pier_heights):
            k_vertical = (E_pier * A_pier) / height
            stiffness_values.append(k_vertical)
            
            analysis['stiffness_analysis'].append({
                'pier_id': i,
                'height': height,
                'stiffness': k_vertical,
                'stiffness_mn': k_vertical / 1e6,
                'relative_stiffness': k_vertical / min(stiffness_values) if min(stiffness_values) > 0 else 1.0
            })
        
        # Predict load distribution based on stiffness
        total_stiffness = sum(stiffness_values)
        for i, k in enumerate(stiffness_values):
            load_share = k / total_stiffness if total_stiffness > 0 else 0
            analysis['load_distribution_prediction'].append({
                'pier_id': i,
                'expected_load_share': load_share,
                'expected_load_percentage': load_share * 100
            })
        
        # Structural effects analysis
        if len(set(self.pier_heights)) > 1:  # If heights are different
            analysis['structural_effects'].append({
                'effect': 'Uneven Load Distribution',
                'description': 'Different pier heights will cause uneven load distribution',
                'severity': 'High' if max(self.pier_heights) - min(self.pier_heights) > 2.0 else 'Medium'
            })
            
            analysis['structural_effects'].append({
                'effect': 'Differential Settlement',
                'description': 'Height differences may cause differential settlement patterns',
                'severity': 'Medium'
            })
        
        return analysis
    
    def _apply_settlements(self):
        """Height effects are now handled by imposed displacements, not settlements"""
        print("DEBUG: Height effects handled by imposed displacement boundary conditions")
        # No settlements needed - displacements are handled by sp() commands
        return
    
    def _apply_imposed_displacements(self):
        """Apply imposed displacements to simulate pier height effects"""
        # Create a separate load pattern for imposed displacements
        ts_id = self.time_series_id
        pattern_id = self.load_pattern_id
        
        self.model.timeSeries('Linear', ts_id)
        self.model.pattern('Plain', pattern_id, ts_id)
        
        # Apply imposed displacements to each pier
        for pier in self.piers:
            imposed_displacement = pier.get('imposed_displacement', 0.0)
            if abs(imposed_displacement) > 1e-6:  # 只有当位移不为零时才施加
                node_id = pier['node']
                print(f"DEBUG: Applying imposed displacement {imposed_displacement:.4f}m to node {node_id}")
                # Use sp() command within load pattern
                self.model.sp(node_id, 2, imposed_displacement)  # 在y方向施加强制位移
        
        self.time_series_id += 1
        self.load_pattern_id += 1
    
    def configure_individual_bearing(self, pier_index, bearing_index, **kwargs):
        """
        Configure individual bearing properties
        
        Args:
            pier_index: Index of the pier (0-based)
            bearing_index: Index of the bearing within the pier (0-based)
            **kwargs: Bearing properties (height, support_type, stiffness, damping, etc.)
        """
        bearing_key = f"pier_{pier_index}_bearing_{bearing_index}"
        if bearing_key not in self.individual_bearing_config:
            self.individual_bearing_config[bearing_key] = {}
        
        self.individual_bearing_config[bearing_key].update(kwargs)
        
        # Update existing bearing if already generated
        for bearing in self.individual_bearings:
            if bearing['bearing_key'] == bearing_key:
                bearing.update(kwargs)
                break
        
        print(f"DEBUG: Configured bearing {bearing_key} with properties: {kwargs}")
        return True
    
    def get_individual_bearing_info(self, pier_index=None, bearing_index=None):
        """
        Get information about individual bearings
        
        Args:
            pier_index: Optional pier index to filter
            bearing_index: Optional bearing index to filter
            
        Returns:
            List of bearing information dictionaries
        """
        if pier_index is not None and bearing_index is not None:
            # Get specific bearing
            bearing_key = f"pier_{pier_index}_bearing_{bearing_index}"
            return [b for b in self.individual_bearings if b['bearing_key'] == bearing_key]
        elif pier_index is not None:
            # Get all bearings for a pier
            return [b for b in self.individual_bearings if b['pier_index'] == pier_index]
        else:
            # Get all bearings
            return self.individual_bearings
    
    def get_individual_bearing_summary(self):
        """
        Generate a summary table of individual bearing configurations
        
        Returns:
            pandas.DataFrame: Summary of all individual bearings
        """
        summary_data = []
        
        for bearing in self.individual_bearings:
            summary_data.append({
                '墩台编号': bearing['pier_index'] + 1,
                '支座编号': bearing['bearing_index'] + 1,
                '全局ID': bearing['global_id'],
                '纵向位置 (m)': f"{bearing['pier_x']:.2f}",
                '横向位置 (m)': f"{bearing['pier_y']:.2f}",
                '支座高度 (m)': f"{bearing['height']:.4f}",
                '支座类型': bearing['support_type']['type'],
                '刚度 (kN/m)': f"{bearing.get('stiffness', 'Default'):.0f}" if bearing.get('stiffness') else 'Default',
                '阻尼 (%)': f"{bearing.get('damping', 0.0):.1f}"
            })
        
        return pd.DataFrame(summary_data)
    
    def set_bearing_heights_with_variation(self, pier_index, base_height, variation_std=0.002):
        """
        Set bearing heights for a pier with random variation
        
        Args:
            pier_index: Index of the pier
            base_height: Base height for all bearings
            variation_std: Standard deviation of height variation in meters
        """
        pier_bearings = self.get_individual_bearing_info(pier_index=pier_index)
        
        for bearing in pier_bearings:
            bearing_idx = bearing['bearing_index']
            height_variation = np.random.normal(0, variation_std)
            new_height = base_height + height_variation
            
            self.configure_individual_bearing(
                pier_index, bearing_idx, 
                height=new_height
            )
        
        print(f"DEBUG: Set heights for pier {pier_index+1} bearings with base={base_height:.4f}m, std={variation_std:.4f}m")
        return True