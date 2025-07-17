import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np

class BridgeVisualizer:
    """
    Enhanced Visualization module for configurable continuous beam bridge digital twin
    Supports 2/3 spans, custom pier positions, and variable bearing configurations
    """
    
    def __init__(self, bridge_model, results):
        """
        Initialize enhanced visualizer
        
        Args:
            bridge_model: Enhanced BridgeModel instance with configurable spans
            results: Analysis results dictionary
        """
        self.bridge = bridge_model
        self.results = results
        
        # Style settings
        plt.style.use('default')
        self.colors = {
            'structure': '#2E86AB',
            'deformed': '#A23B72',
            'moment': '#F18F01',
            'shear': '#C73E1D',
            'supports': '#000000',
            'pier': '#8B4513',
            'bearing': '#FFD700',
            'deck': '#4682B4'
        }
    
    def create_3d_model(self):
        """Create enhanced 3D visualization with configurable spans and bearings"""
        fig = go.Figure()
        
        # Get coordinates
        x_coords, y_coords = self.bridge.get_node_coordinates()
        
        # Bridge deck - use actual bridge width from configuration
        deck_width = self.bridge.bridge_width  # Use configured bridge width, not section_width * 8
        deck_height = self.bridge.section_height
        
        # Create bridge deck surface
        x_surf = np.array([x_coords, x_coords])
        y_surf = np.array([[-deck_width/2]*len(x_coords), [deck_width/2]*len(x_coords)])
        z_surf = np.array([[deck_height]*len(x_coords), [deck_height]*len(x_coords)])
        
        # Add deck surface
        fig.add_trace(go.Surface(
            x=x_surf,
            y=y_surf,
            z=z_surf,
            colorscale='Blues',
            opacity=0.7,
            name='Bridge Deck',
            showscale=False
        ))
        
        # Add deck edges for better definition
        fig.add_trace(go.Scatter3d(
            x=x_coords + x_coords[::-1] + [x_coords[0]],
            y=[-deck_width/2]*len(x_coords) + [deck_width/2]*len(x_coords) + [-deck_width/2],
            z=[deck_height]*(2*len(x_coords)+1),
            mode='lines',
            line=dict(color=self.colors['deck'], width=4),
            name='Deck Outline'
        ))
        
        # Add enhanced piers and bearings
        self._add_enhanced_piers_and_bearings(fig, deck_width, deck_height)
        
        # Add loads visualization
        self._add_loads_visualization(fig, deck_height, deck_width)
        
        # Configure layout
        fig.update_layout(
            title=f"Enhanced {self.bridge.num_spans}-Span Bridge Digital Twin",
            scene=dict(
                xaxis_title="Length (m)",
                yaxis_title="Width (m)", 
                zaxis_title="Height (m)",
                camera=dict(eye=dict(x=1.5, y=1.5, z=1.2)),
                aspectratio=dict(x=4, y=1, z=1.5)
            ),
            showlegend=True,
            height=400
        )
        
        return fig
    
    def _add_enhanced_piers_and_bearings(self, fig, deck_width, deck_height):
        """Add configurable piers and bearings based on bridge configuration"""
        pier_height = deck_height * 3  # Pier extends below deck
        bearing_size = 0.5  # Size of bearing blocks
        
        for pier in self.bridge.piers:
            x_pos = pier['x_coord']
            pier_type = pier['type']
            bearings_count = pier.get('bearings_count', 2)  # Get actual bearing count
            
            # Pier column (rectangular) - size based on bearing count
            pier_width = 1.0 + (bearings_count - 2) * 0.3  # Wider pier for more bearings
            pier_depth = 1.5
            
            # Pier column corners
            pier_x = [x_pos-pier_width/2, x_pos+pier_width/2, x_pos+pier_width/2, x_pos-pier_width/2, 
                     x_pos-pier_width/2, x_pos+pier_width/2, x_pos+pier_width/2, x_pos-pier_width/2]
            pier_y = [-pier_depth/2, -pier_depth/2, pier_depth/2, pier_depth/2,
                     -pier_depth/2, -pier_depth/2, pier_depth/2, pier_depth/2]
            pier_z = [0, 0, 0, 0, deck_height, deck_height, deck_height, deck_height]
            
            # Define pier faces
            i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
            j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
            k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
            
            # Color based on pier type
            pier_color = {
                'abutment_left': '#8B4513',
                'abutment_right': '#8B4513', 
                'pier_intermediate': '#A0522D'
            }.get(pier_type, self.colors['pier'])
            
            # Add pier column
            fig.add_trace(go.Mesh3d(
                x=pier_x, y=pier_y, z=pier_z,
                i=i, j=j, k=k,
                color=pier_color,
                opacity=0.7,
                name=f'Pier {pier["id"]+1} ({pier_type})'
            ))
            
            # Add configurable bearings
            self._add_configurable_bearings(fig, pier, bearing_size, deck_height)
    
    def _add_configurable_bearings(self, fig, pier, bearing_size, deck_height):
        """Add bearings based on configurable count"""
        x_pos = pier['x_coord']
        pier_type = pier['type']
        bearings_count = pier.get('bearings_count', 2)
        
        # Calculate bearing positions based on count
        if bearings_count == 1:
            bearing_positions = [0.0]  # Single bearing at center
        elif bearings_count == 2:
            spacing = self.bridge.bearing_spacing
            bearing_positions = [-spacing/2, spacing/2]  # Standard dual bearings
        elif bearings_count == 3:
            spacing = self.bridge.bearing_spacing
            bearing_positions = [-spacing, 0.0, spacing]  # Triple bearings
        elif bearings_count == 4:
            spacing = self.bridge.bearing_spacing
            bearing_positions = [-spacing*1.5, -spacing/2, spacing/2, spacing*1.5]  # Quad bearings
        else:
            # For any other count, distribute evenly
            spacing = self.bridge.bearing_spacing
            half_span = spacing * (bearings_count - 1) / 2
            bearing_positions = [i * spacing - half_span for i in range(bearings_count)]
        
        for j, bearing_y in enumerate(bearing_positions):
            # Bearing block
            bearing_x = [x_pos-bearing_size/2, x_pos+bearing_size/2]
            bearing_y_pos = [bearing_y-bearing_size/2, bearing_y+bearing_size/2]
            bearing_z = [deck_height, deck_height+bearing_size/2]
            
            # Create bearing as a small box
            bearing_x_mesh = [bearing_x[0], bearing_x[1], bearing_x[1], bearing_x[0],
                            bearing_x[0], bearing_x[1], bearing_x[1], bearing_x[0]]
            bearing_y_mesh = [bearing_y_pos[0], bearing_y_pos[0], bearing_y_pos[1], bearing_y_pos[1],
                            bearing_y_pos[0], bearing_y_pos[0], bearing_y_pos[1], bearing_y_pos[1]]
            bearing_z_mesh = [bearing_z[0], bearing_z[0], bearing_z[0], bearing_z[0],
                            bearing_z[1], bearing_z[1], bearing_z[1], bearing_z[1]]
            
            # Bearing color based on type
            bearing_color = {
                'abutment_left': '#FFD700',
                'abutment_right': '#FFD700',
                'pier_intermediate': '#FFA500'
            }.get(pier_type, self.colors['bearing'])
            
            fig.add_trace(go.Mesh3d(
                x=bearing_x_mesh, y=bearing_y_mesh, z=bearing_z_mesh,
                i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
                j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
                k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                color=bearing_color,
                opacity=0.9,
                name=f'Bearing {pier["id"]+1}-{j+1}'
            ))
            
            # Support symbol - use valid plotly symbols only
            valid_symbols = ['circle', 'circle-open', 'cross', 'diamond', 
                           'diamond-open', 'square', 'square-open', 'x']
            symbol_type = 'diamond' if pier_type in ['abutment_left', 'abutment_right'] else 'square'
            
            fig.add_trace(go.Scatter3d(
                x=[x_pos],
                y=[bearing_y],
                z=[bearing_z[1] + 0.2],
                mode='markers',
                marker=dict(size=8, color=self.colors['supports'], symbol=symbol_type),
                name=f'Support {pier["id"]+1}-{j+1}',
                showlegend=False
            ))
    
    def _add_loads_visualization(self, fig, deck_height, deck_width):
        """Add load visualization to 3D model"""
        for load in self.bridge.loads:
            if load[0] == 'point_load':
                load_pos = load[2] * self.bridge.length
                load_magnitude = load[1] / 1000  # Convert to kN
                
                # Load arrow - use simple line instead of invalid symbols
                arrow_height = 2.0
                fig.add_trace(go.Scatter3d(
                    x=[load_pos, load_pos],
                    y=[0, 0],
                    z=[deck_height + arrow_height, deck_height],
                    mode='lines+markers',
                    line=dict(color='red', width=6),
                    marker=dict(size=8, color='red', symbol='x'),  # Use valid symbol
                    name=f'Point Load: {abs(load_magnitude):.1f} kN'
                ))
                
                # Load text annotation
                fig.add_trace(go.Scatter3d(
                    x=[load_pos],
                    y=[0],
                    z=[deck_height + arrow_height + 0.5],
                    mode='text',
                    text=[f'{abs(load_magnitude):.1f} kN'],
                    textfont=dict(size=12, color='red'),
                    showlegend=False
                ))
    
    def create_deformation_plot(self, scale_factor=100):
        """Create enhanced Plotly deformation plot for configurable bridges"""
        import plotly.graph_objects as go
        
        # Get coordinates
        x_coords, y_coords = self.bridge.get_node_coordinates()
        x_def, y_def = self.bridge.get_deformed_coordinates(scale_factor)
        
        fig = go.Figure()
        
        # Original shape
        fig.add_trace(go.Scatter(
            x=x_coords, y=y_coords,
            mode='lines+markers',
            name='Original Shape',
            line=dict(color='blue', width=3),
            marker=dict(size=6)
        ))
        
        # Deformed shape
        fig.add_trace(go.Scatter(
            x=x_def, y=y_def,
            mode='lines+markers',
            name=f'Deformed Shape (×{scale_factor})',
            line=dict(color='red', width=3, dash='dash'),
            marker=dict(size=6)
        ))
        
        # Add enhanced pier markers with labels
        pier_x = []
        pier_y = []
        pier_text = []
        pier_colors = []
        
        for pier in self.bridge.piers:
            pier_x.append(pier['x_coord'])
            pier_y.append(0)
            
            # Enhanced pier labeling
            pier_type = pier['type']
            pier_id = pier.get('id', pier.get('pier_id', 0))  # 使用id或pier_id，默认为0
            bearings_count = pier.get('bearings_count', 2)
            
            if pier_type == 'abutment_left':
                pier_text.append(f"左桥台 (支座×{bearings_count})")
                pier_colors.append('darkgreen')
            elif pier_type == 'abutment_right':
                pier_text.append(f"右桥台 (支座×{bearings_count})")
                pier_colors.append('darkgreen')
            else:
                pier_text.append(f"中墩{pier_id} (支座×{bearings_count})")
                pier_colors.append('darkorange')
        
        fig.add_trace(go.Scatter(
            x=pier_x, y=pier_y,
            mode='markers+text',
            name='支座布置',
            marker=dict(color=pier_colors, size=12, symbol='square'),
            text=pier_text,
            textposition='bottom center',
            textfont=dict(size=10)
        ))
        
        fig.update_layout(
            title=f"{self.bridge.num_spans}跨连续梁桥变形分析",
            xaxis_title="距离 (m)",
            yaxis_title="挠度 (m)",
            showlegend=True,
            height=400,
            hovermode='x unified'
        )
        
        return fig

    def create_moment_diagram(self):
        """Create enhanced Plotly moment diagram with accurate moment values"""
        import plotly.graph_objects as go
        
        # Check if detailed moment data is available
        if 'moments_i' in self.results and 'moments_j' in self.results:
            # Use detailed moment data for accurate plotting
            x_coords, _ = self.bridge.get_node_coordinates()
            moments_i = np.array(self.results['moments_i']) / 1000  # Convert to kN⋅m
            moments_j = np.array(self.results['moments_j']) / 1000  # Convert to kN⋅m
            
            # Create detailed moment diagram with node-by-node values
            x_detailed = []
            moment_detailed = []
            
            # First node (start of first element)
            x_detailed.append(x_coords[0])
            moment_detailed.append(moments_i[0])
            
            # Add intermediate points and element ends
            for i in range(len(moments_i)):
                # Add end of current element
                if i + 1 < len(x_coords):
                    x_detailed.append(x_coords[i + 1])
                    moment_detailed.append(moments_j[i])
            
            x_plot = np.array(x_detailed)
            moments_plot = np.array(moment_detailed)
        else:
            # Fallback to element centers if detailed data not available
            x_plot = np.array(self.bridge.get_element_centers())
            moments_plot = np.array(self.results['moments']) / 1000  # Convert to kN⋅m
        
        fig = go.Figure()
        
        # Add moment diagram with improved accuracy
        fig.add_trace(go.Scatter(
            x=x_plot, y=moments_plot,
            fill='tonext',
            mode='lines+markers',
            name='弯矩 (kN⋅m)',
            line=dict(color='orange', width=3),
            marker=dict(size=4),
            fillcolor='rgba(255, 165, 0, 0.3)',
            hovertemplate='位置: %{x:.1f}m<br>弯矩: %{y:.1f} kN⋅m<extra></extra>'
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)
        
        # Add enhanced pier lines with constraint information
        for i, pier in enumerate(self.bridge.piers):
            constraint_info = pier.get('constraint_type', 'Unknown')
            fig.add_vline(
                x=pier['x_coord'], 
                line_dash="dash", 
                line_color="red", 
                line_width=2,
                opacity=0.7,
                annotation_text=f"支座{i+1}<br>{constraint_info}",
                annotation_position="top"
            )
        
        # Add span labels
        for i in range(self.bridge.num_spans):
            if i == 0:
                span_start = 0
            else:
                span_start = self.bridge.piers[i]['x_coord']
            
            span_end = self.bridge.piers[i+1]['x_coord']
            span_center = (span_start + span_end) / 2
            span_length = span_end - span_start
            
            fig.add_annotation(
                x=span_center,
                y=max(moments_plot) * 0.8,
                text=f"第{i+1}跨<br>{span_length:.1f}m",
                showarrow=False,
                bgcolor="lightblue",
                bordercolor="blue",
                font=dict(size=10)
            )
        
        # Find max moment for annotation
        max_moment_idx = np.argmax(np.abs(moments_plot))
        max_moment = moments_plot[max_moment_idx]
        max_x = x_plot[max_moment_idx]
        
        fig.add_annotation(
            x=max_x, y=max_moment,
            text=f"最大弯矩: {max_moment:.1f} kN⋅m",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            bgcolor="white",
            bordercolor="red"
        )
        
        fig.update_layout(
            title=f"{self.bridge.num_spans}跨连续梁桥弯矩图",
            xaxis_title="距离 (m)",
            yaxis_title="弯矩 (kN⋅m)",
            showlegend=True,
            height=400,
            hovermode='x unified'
        )
        
        return fig

    def create_shear_diagram(self):
        """Create enhanced Plotly shear diagram"""
        import plotly.graph_objects as go
        
        # Get element centers and shear forces
        x_centers = self.bridge.get_element_centers()
        shears = np.array(self.results['shears']) / 1000  # Convert to kN
        
        fig = go.Figure()
        
        # Add shear diagram
        fig.add_trace(go.Scatter(
            x=x_centers, y=shears,
            fill='tonext',
            mode='lines+markers',
            name='剪力',
            line=dict(color='red', width=2),
            marker=dict(size=4),
            fillcolor='rgba(255, 0, 0, 0.3)'
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="solid", line_color="black", line_width=1)
        
        # Add enhanced pier lines
        for i, pier in enumerate(self.bridge.piers):
            fig.add_vline(
                x=pier['x_coord'], 
                line_dash="dash", 
                line_color="gray", 
                line_width=2,
                opacity=0.5,
                annotation_text=f"支座{i+1}",
                annotation_position="top"
            )
        
        # Find max shear for annotation
        max_shear_idx = np.argmax(np.abs(shears))
        max_shear = shears[max_shear_idx]
        max_x = x_centers[max_shear_idx]
        
        fig.add_annotation(
            x=max_x, y=max_shear,
            text=f"最大剪力: {max_shear:.1f} kN",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            bgcolor="white",
            bordercolor="red"
        )
        
        fig.update_layout(
            title=f"{self.bridge.num_spans}跨连续梁桥剪力图",
            xaxis_title="距离 (m)",
            yaxis_title="剪力 (kN)",
            showlegend=True,
            height=400,
            hovermode='x unified'
        )
        
        return fig

    # Legacy matplotlib methods for compatibility
    def plot_deformation(self, scale_factor=100):
        """Plot deformation diagram using matplotlib"""
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Original shape
        x_coords, y_coords = self.bridge.get_node_coordinates()
        ax.plot(x_coords, y_coords, '-', linewidth=3, label='Original Shape', color=self.colors['structure'])
        
        # Deformed shape
        x_def, y_def = self.bridge.get_deformed_coordinates(scale_factor)
        ax.plot(x_def, y_def, '--', linewidth=3, label=f'Deformed Shape (×{scale_factor})', color=self.colors['deformed'])
        
        # Add piers and supports with enhanced labeling
        for pier in self.bridge.piers:
            x_pos = pier['x_coord']
            pier_type = pier['type']
            bearings_count = pier.get('bearings_count', 2)
            
            if pier_type in ['abutment_left', 'abutment_right']:
                # Abutments (fixed supports)
                ax.plot(x_pos, 0, 'ks', markersize=12, label='桥台' if pier['id'] == 0 else '')
                ax.annotate(f'固定支座\n(支座×{bearings_count})', xy=(x_pos, 0), xytext=(0, -30), 
                           textcoords='offset points', ha='center', fontsize=8)
            else:
                # Intermediate piers (roller supports)
                ax.plot(x_pos, 0, '^', markersize=12, color='orange', label='中墩' if pier['id'] == 1 else '')
                ax.annotate(f'滑动支座\n(支座×{bearings_count})', xy=(x_pos, 0), xytext=(0, -30), 
                           textcoords='offset points', ha='center', fontsize=8)
        
        ax.set_xlabel('距离 (m)')
        ax.set_ylabel('挠度 (m)')
        ax.set_title(f'{self.bridge.num_spans}跨连续梁桥变形分析')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        return fig

    def plot_moment_diagram(self):
        """Plot bending moment diagram using matplotlib"""
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Get data for plotting - use accurate moment values if available
        if 'moments_i' in self.results and 'moments_j' in self.results:
            # Use detailed moment data for accurate plotting
            x_coords, _ = self.bridge.get_node_coordinates()
            moments_i = np.array(self.results['moments_i']) / 1000  # Convert to kN⋅m
            moments_j = np.array(self.results['moments_j']) / 1000  # Convert to kN⋅m
            
            # Create detailed moment diagram
            x_plot = []
            moment_plot = []
            
            # First node (start of first element)
            x_plot.append(x_coords[0])
            moment_plot.append(moments_i[0])
            
            # Add all element end points
            for i in range(len(moments_i)):
                if i + 1 < len(x_coords):
                    x_plot.append(x_coords[i + 1])
                    moment_plot.append(moments_j[i])
            
            x_centers = np.array(x_plot)
            moments = np.array(moment_plot)
        else:
            # Fallback to element centers
            x_centers = self.bridge.get_element_centers()
            moments = np.array(self.results['moments']) / 1000  # Convert to kN⋅m
        
        # Plot moment diagram
        ax.fill_between(x_centers, 0, moments, alpha=0.7, color=self.colors['moment'], label='弯矩')
        ax.plot(x_centers, moments, 'o-', color=self.colors['moment'], linewidth=2, markersize=3)
        
        # Add zero line
        ax.axhline(y=0, color='black', linewidth=1, linestyle='-')
        
        # Add pier locations with enhanced labels
        for i, pier in enumerate(self.bridge.piers):
            ax.axvline(x=pier['x_coord'], color='gray', linewidth=2, linestyle='--', alpha=0.5)
            ax.text(pier['x_coord'], ax.get_ylim()[1]*0.9, f"支座{i+1}", 
                   rotation=90, ha='right', va='top', fontsize=8)
        
        # Add span information
        for i in range(self.bridge.num_spans):
            if i == 0:
                span_start = 0
            else:
                span_start = self.bridge.piers[i]['x_coord']
            span_end = self.bridge.piers[i+1]['x_coord']
            span_center = (span_start + span_end) / 2
            span_length = span_end - span_start
            
            ax.text(span_center, ax.get_ylim()[1]*0.8, f'第{i+1}跨\n{span_length:.1f}m', 
                   ha='center', va='center', fontsize=9, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7))
        
        ax.set_xlabel('距离 (m)')
        ax.set_ylabel('弯矩 (kN⋅m)')
        ax.set_title(f'{self.bridge.num_spans}跨连续梁桥弯矩图')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        return fig

    def plot_shear_diagram(self):
        """Plot shear force diagram using matplotlib"""
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Get element centers for plotting
        x_centers = self.bridge.get_element_centers()
        shears = np.array(self.results['shears']) / 1000  # Convert to kN
        
        # Plot shear diagram
        ax.fill_between(x_centers, 0, shears, alpha=0.7, color=self.colors['shear'], label='剪力')
        ax.plot(x_centers, shears, 'o-', color=self.colors['shear'], linewidth=2, markersize=3)
        
        # Add zero line
        ax.axhline(y=0, color='black', linewidth=1, linestyle='-')
        
        # Add pier locations
        for i, pier in enumerate(self.bridge.piers):
            ax.axvline(x=pier['x_coord'], color='gray', linewidth=2, linestyle='--', alpha=0.5)
            ax.text(pier['x_coord'], ax.get_ylim()[1]*0.9, f"支座{i+1}", 
                   rotation=90, ha='right', va='top', fontsize=8)
        
        ax.set_xlabel('距离 (m)')
        ax.set_ylabel('剪力 (kN)')
        ax.set_title(f'{self.bridge.num_spans}跨连续梁桥剪力图')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        return fig 