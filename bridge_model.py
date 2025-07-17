import numpy as np
import pandas as pd
from simple_fea import SimplifiedFEA

class BridgeModel:
    """
    Bridge Digital Twin Model using Simplified FEA
    Continuous beam bridge with 3 piers and dual bearings per pier
    Compatible with Mac systems - no OpenSees dependency
    """
    
    def __init__(self, length=60.0, num_elements=30, E=30e9, section_height=1.5, 
                 section_width=1.0, density=2400):
        """
        Initialize continuous beam bridge model
        
        Args:
            length: Bridge length in meters (total span)
            num_elements: Number of finite elements
            E: Elastic modulus in Pa
            section_height: Cross-section height in meters
            section_width: Cross-section width in meters
            density: Material density in kg/m³
        """
        self.length = length
        self.num_elements = num_elements
        self.E = E
        self.section_height = section_height
        self.section_width = section_width
        self.density = density
        
        # Calculate section properties
        self.A = section_height * section_width  # Cross-sectional area
        self.I = (section_width * section_height**3) / 12  # Moment of inertia
        
        # Pier configurations for 3-pier continuous bridge
        self.num_piers = 3
        self.pier_positions = [0.25, 0.5, 0.75]  # Relative positions along span
        self.bearing_spacing = 2.0  # Transverse spacing between bearings (m)
        
        # Initialize FEA solver
        self.fea = SimplifiedFEA()
        
        # Node and element arrays
        self.nodes = []
        self.elements = []
        self.loads = []
        self.piers = []  # Store pier information
        
        # Analysis results
        self.displacements = []
        self.moments = []
        self.shears = []
        
        self._create_model()
    
    def _create_model(self):
        """Create the continuous beam bridge FEA model"""
        # Create nodes along the bridge deck
        num_nodes = self.num_elements + 1
        dx = self.length / self.num_elements
        
        for i in range(num_nodes):
            x = i * dx
            node_id = self.fea.add_node(x, 0.0)
            self.nodes.append((node_id, x, 0.0))
        
        # Create beam elements
        for i in range(self.num_elements):
            element_id = self.fea.add_element(i, i+1, self.E, self.A, self.I)
            self.elements.append((element_id, i, i+1))
        
        # Define pier supports - each pier has constraints
        self._create_pier_supports()
        
        # Add self-weight
        self._add_self_weight()
    
    def _create_pier_supports(self):
        """Create pier supports with dual bearings"""
        for i, pier_pos in enumerate(self.pier_positions):
            # Find the closest node to pier position
            pier_x = pier_pos * self.length
            node_spacing = self.length / self.num_elements
            pier_node = int(round(pier_x / node_spacing))
            pier_node = max(0, min(pier_node, len(self.nodes)-1))
            
            # Store pier information
            pier_info = {
                'id': i,
                'position': pier_pos,
                'x_coord': pier_x,
                'node': pier_node,
                'type': self._get_pier_type(i)
            }
            
            # Add support constraints based on pier type for continuous beam
            if i == 0:
                # Left abutment: Fixed pin support - prevent horizontal and vertical movement, allow rotation
                self.fea.add_support(pier_node, [1, 1, 0])  # Fixed pin support
                pier_info['constraint_type'] = 'Fixed Pin (dx=0, dy=0, rz=free)'
            elif i == len(self.pier_positions) - 1:
                # Right abutment: Roller support - prevent only vertical movement
                self.fea.add_support(pier_node, [0, 1, 0])  # Roller support
                pier_info['constraint_type'] = 'Roller (dx=free, dy=0, rz=free)'
            else:
                # Middle piers: Roller support - prevent only vertical movement
                self.fea.add_support(pier_node, [0, 1, 0])  # Roller support
                pier_info['constraint_type'] = 'Intermediate Roller (dx=free, dy=0, rz=free)'
            
            # Store the updated pier info
            self.piers.append(pier_info)
    
    def _get_pier_type(self, pier_index):
        """Determine pier type based on position"""
        if pier_index == 0:
            return "abutment_left"
        elif pier_index == len(self.pier_positions) - 1:
            return "abutment_right" 
        else:
            return "pier"
    
    def _add_self_weight(self):
        """Add self-weight to the model"""
        weight_per_length = self.density * 9.81 * self.A  # N/m
        
        # Add distributed load to each element
        for i in range(self.num_elements):
            self.fea.add_distributed_load(i, -weight_per_length)
    
    def add_point_load(self, magnitude, position_ratio):
        """
        Add a point load to the bridge
        
        Args:
            magnitude: Load magnitude in N (negative for downward)
            position_ratio: Load position as ratio of span (0.0 to 1.0)
        """
        # Find the closest node
        load_position = position_ratio * self.length
        node_spacing = self.length / self.num_elements
        node_index = int(round(load_position / node_spacing))
        
        # Ensure node is within valid range
        node_index = max(0, min(node_index, len(self.nodes)-1))
        
        self.fea.add_point_load(node_index, 0, -abs(magnitude), 0)
        self.loads.append(('point', magnitude, position_ratio, node_index))
    
    def add_distributed_load(self, magnitude):
        """
        Add distributed load to all elements
        
        Args:
            magnitude: Load magnitude in N/m (negative for downward)
        """
        for i in range(self.num_elements):
            self.fea.add_distributed_load(i, -abs(magnitude))
        
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
        Run static analysis and extract results
        
        Returns:
            dict: Analysis results including displacements, moments, and shears
        """
        # Solve the FEA system
        displacements = self.fea.solve()
        
        # Extract nodal displacements (vertical only)
        node_displacements = []
        for i in range(len(self.nodes)):
            # Extract vertical displacement (DOF 1 of each node)
            disp = displacements[i*3 + 1]
            node_displacements.append(disp)
        
        # Get element forces
        element_forces = self.fea.get_element_forces()
        
        # Extract moments and shears
        moments = []
        shears = []
        
        for force in element_forces:
            moments.append(force['moment'])
            shears.append(force['shear'])
        
        # Store results
        self.displacements = node_displacements
        self.moments = moments
        self.shears = shears
        
        # Calculate summary statistics for compatibility
        max_displacement = max(abs(d) for d in node_displacements) if node_displacements else 0
        max_moment = max(abs(m) for m in moments) if moments else 0
        max_shear = max(abs(s) for s in shears) if shears else 0
        
        return {
            'displacements': node_displacements,
            'moments': moments,
            'shears': shears,
            'max_displacement': max_displacement,  # 添加兼容字段
            'max_moment': max_moment,              # 添加兼容字段
            'max_shear': max_shear,                # 添加兼容字段
            'nodes': self.nodes,
            'elements': self.elements,
            'loads': self.loads,
            'piers': self.piers
        }
    
    def get_node_coordinates(self):
        """Get node coordinates for visualization"""
        x_coords = [node[1] for node in self.nodes]
        y_coords = [node[2] for node in self.nodes]
        return x_coords, y_coords
    
    def get_deformed_coordinates(self, scale_factor=100):
        """
        Get deformed coordinates for visualization
        
        Args:
            scale_factor: Amplification factor for displacements
            
        Returns:
            tuple: (x_coords, y_deformed)
        """
        x_coords, y_coords = self.get_node_coordinates()
        y_deformed = [y + scale_factor * disp for y, disp in zip(y_coords, self.displacements)]
        return x_coords, y_deformed
    
    def get_element_centers(self):
        """Get element center coordinates for force diagrams"""
        x_centers = []
        for i in range(self.num_elements):
            x1 = self.nodes[i][1]
            x2 = self.nodes[i+1][1]
            x_centers.append((x1 + x2) / 2)
        return x_centers 