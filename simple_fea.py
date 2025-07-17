import numpy as np
from scipy.linalg import solve
import warnings

class SimplifiedFEA:
    """
    Simplified Finite Element Analysis for beam structures
    Alternative to OpenSees for Mac compatibility
    """
    
    def __init__(self):
        self.nodes = []
        self.elements = []
        self.loads = []
        self.supports = []
        self.K_global = None
        self.F_global = None
        self.displacements = None
        
    def add_node(self, x, y=0.0):
        """Add a node to the model"""
        node_id = len(self.nodes)
        self.nodes.append({'id': node_id, 'x': x, 'y': y})
        return node_id
    
    def add_element(self, node1, node2, E, A, I):
        """Add a beam element between two nodes"""
        element_id = len(self.elements)
        
        # Calculate element properties
        dx = self.nodes[node2]['x'] - self.nodes[node1]['x']
        dy = self.nodes[node2]['y'] - self.nodes[node1]['y']
        length = np.sqrt(dx**2 + dy**2)
        angle = np.arctan2(dy, dx)
        
        element = {
            'id': element_id,
            'nodes': [node1, node2],
            'E': E,
            'A': A,
            'I': I,
            'length': length,
            'angle': angle
        }
        
        self.elements.append(element)
        return element_id
    
    def add_support(self, node_id, restraints):
        """
        Add support constraints
        restraints: [ux, uy, rz] where 1=restrained, 0=free
        """
        self.supports.append({'node': node_id, 'restraints': restraints})
    
    def add_point_load(self, node_id, fx=0, fy=0, mz=0):
        """Add point load to a node"""
        self.loads.append({
            'type': 'point',
            'node': node_id,
            'fx': fx,
            'fy': fy,
            'mz': mz
        })
    
    def add_distributed_load(self, element_id, wy):
        """Add distributed load to an element"""
        self.loads.append({
            'type': 'distributed',
            'element': element_id,
            'wy': wy
        })
    
    def _beam_stiffness_matrix(self, element):
        """Calculate local stiffness matrix for beam element"""
        E = element['E']
        A = element['A']
        I = element['I']
        L = element['length']
        
        # Local stiffness matrix (6x6 for 2D beam with 3 DOF per node)
        k_local = np.zeros((6, 6))
        
        # Axial terms
        k_local[0, 0] = k_local[3, 3] = E * A / L
        k_local[0, 3] = k_local[3, 0] = -E * A / L
        
        # Bending terms
        k_local[1, 1] = k_local[4, 4] = 12 * E * I / (L**3)
        k_local[1, 4] = k_local[4, 1] = -12 * E * I / (L**3)
        k_local[1, 2] = k_local[2, 1] = 6 * E * I / (L**2)
        k_local[1, 5] = k_local[5, 1] = 6 * E * I / (L**2)
        k_local[4, 2] = k_local[2, 4] = -6 * E * I / (L**2)
        k_local[4, 5] = k_local[5, 4] = -6 * E * I / (L**2)
        
        k_local[2, 2] = k_local[5, 5] = 4 * E * I / L
        k_local[2, 5] = k_local[5, 2] = 2 * E * I / L
        
        return k_local
    
    def _transformation_matrix(self, angle):
        """Calculate transformation matrix from local to global coordinates"""
        c = np.cos(angle)
        s = np.sin(angle)
        
        T = np.zeros((6, 6))
        T[0, 0] = T[1, 1] = T[3, 3] = T[4, 4] = c
        T[0, 1] = T[3, 4] = s
        T[1, 0] = T[4, 3] = -s
        T[2, 2] = T[5, 5] = 1
        
        return T
    
    def _assemble_global_stiffness(self):
        """Assemble global stiffness matrix"""
        ndof = len(self.nodes) * 3  # 3 DOF per node
        self.K_global = np.zeros((ndof, ndof))
        
        for element in self.elements:
            # Local stiffness matrix
            k_local = self._beam_stiffness_matrix(element)
            
            # Transformation matrix
            T = self._transformation_matrix(element['angle'])
            
            # Global stiffness matrix
            k_global = T.T @ k_local @ T
            
            # Assembly
            node1, node2 = element['nodes']
            dofs = [node1*3, node1*3+1, node1*3+2, node2*3, node2*3+1, node2*3+2]
            
            for i in range(6):
                for j in range(6):
                    self.K_global[dofs[i], dofs[j]] += k_global[i, j]
    
    def _assemble_load_vector(self):
        """Assemble global load vector"""
        ndof = len(self.nodes) * 3
        self.F_global = np.zeros(ndof)
        
        for load in self.loads:
            if load['type'] == 'point':
                node = load['node']
                self.F_global[node*3] += load['fx']
                self.F_global[node*3+1] += load['fy']
                self.F_global[node*3+2] += load['mz']
            
            elif load['type'] == 'distributed':
                # Convert distributed load to equivalent nodal loads
                element = self.elements[load['element']]
                L = element['length']
                wy = load['wy']
                
                # Equivalent loads for uniform distributed load
                node1, node2 = element['nodes']
                self.F_global[node1*3+1] += wy * L / 2
                self.F_global[node2*3+1] += wy * L / 2
                self.F_global[node1*3+2] += wy * L**2 / 12
                self.F_global[node2*3+2] += -wy * L**2 / 12
    
    def _apply_boundary_conditions(self):
        """Apply support boundary conditions"""
        # Create lists of free and constrained DOFs
        free_dofs = list(range(len(self.nodes) * 3))
        
        for support in self.supports:
            node = support['node']
            restraints = support['restraints']
            
            for i, restrained in enumerate(restraints):
                if restrained:
                    dof = node * 3 + i
                    if dof in free_dofs:
                        free_dofs.remove(dof)
        
        return free_dofs
    
    def solve(self):
        """Solve the FEA system"""
        # Assemble matrices
        self._assemble_global_stiffness()
        self._assemble_load_vector()
        
        # Apply boundary conditions
        free_dofs = self._apply_boundary_conditions()
        
        # Extract reduced system
        K_reduced = self.K_global[np.ix_(free_dofs, free_dofs)]
        F_reduced = self.F_global[free_dofs]
        
        # Solve for displacements
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                u_reduced = solve(K_reduced, F_reduced)
            except np.linalg.LinAlgError:
                # Fallback for singular matrix
                u_reduced = np.linalg.pinv(K_reduced) @ F_reduced
        
        # Reconstruct full displacement vector
        self.displacements = np.zeros(len(self.nodes) * 3)
        for i, dof in enumerate(free_dofs):
            self.displacements[dof] = u_reduced[i]
        
        return self.displacements
    
    def get_element_forces(self):
        """Calculate internal forces in elements"""
        element_forces = []
        
        for element in self.elements:
            node1, node2 = element['nodes']
            
            # Get nodal displacements
            u1 = self.displacements[node1*3:node1*3+3]
            u2 = self.displacements[node2*3:node2*3+3]
            u_element = np.concatenate([u1, u2])
            
            # Transform to local coordinates
            T = self._transformation_matrix(element['angle'])
            u_local = T @ u_element
            
            # Calculate local forces
            k_local = self._beam_stiffness_matrix(element)
            f_local = k_local @ u_local
            
            # Extract forces (node 1: axial, shear, moment)
            axial = f_local[0]
            shear = f_local[1]
            moment = f_local[2]
            
            element_forces.append({
                'element_id': element['id'],
                'axial': axial,
                'shear': shear,
                'moment': moment
            })
        
        return element_forces 