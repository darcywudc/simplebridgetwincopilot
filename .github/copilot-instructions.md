# Copilot Instructions for Bridge Digital Twin

## Architecture Overview

This is a **continuous beam bridge finite element analysis (FEA) system** with dual analysis engines and interactive Streamlit UI. The architecture follows a modular design:

- **`main_enhanced_fixed.py`**: Streamlit UI entry point with sidebar configuration and result visualization
- **Bridge Models**: Two analysis engines with different capabilities
  - `BridgeModel` (simple_fea.py): Pure Python FEA engine for Mac compatibility
  - `BridgeModelXara` (bridge_model_enhanced.py): Advanced analysis using xara/OpenSees
- **`BridgeVisualizer`** (visualization_enhanced.py): 3D Plotly and 2D matplotlib visualization

## Key Development Patterns

### Bridge Model Creation Pattern
Always use the dual-engine pattern in `main_enhanced_fixed.py`:
```python
if use_xara:
    bridge = BridgeModelXara(length=60, num_spans=3, pier_start_position=0.0, ...)
else:
    bridge = BridgeModel(length=60, ...)
    # Add compatibility attributes for simple engine
    bridge.piers = [...] 
```

### Configuration Management
Bridge parameters are managed through Streamlit session state with cache invalidation:
```python
bridge_key = f"bridge_{use_xara}_{length}_{num_elements}_{E}_{section_height}..."
if 'bridge_params' not in st.session_state or st.session_state.bridge_params != bridge_key:
    # Recreate bridge model
```

### Pier Configuration System
Piers are configured with position ratios (0.0-1.0) and support types:
- `pier_start_position`: First pier relative position
- `support_configs`: List of dicts with `{'type': 'fixed_pin', 'dx': 1, 'dy': 1, 'rz': 0}`
- `bearings_per_pier`: Transverse bearing count per pier

## Critical Workflows

### Running the Application
```bash
streamlit run main_enhanced_fixed.py
```

### Engine Selection Logic
- **xara/OpenSees**: Professional analysis with reaction calculations, configurable supports
- **Simple FEA**: Mac-compatible fallback with basic beam analysis

### Load Application Workflow
1. Configure bridge parameters in sidebar
2. Apply loads via tabs (point, distributed, vehicle)
3. Click "🚀 Run Analysis" 
4. Results stored in `st.session_state` for persistence

## Project-Specific Conventions

### Unit System
- **Length**: meters (m)
- **Force**: Newtons (N) internally, displayed as kN
- **Stress**: Pascals (Pa), input as GPa
- **Density**: kg/m³

### Support Type Mapping
```python
support_options = {
    'fixed_pin': '固定铰接 (水平+竖向固定, 转动自由)',
    'roller': '滑动支座 (仅竖向固定)', 
    'fixed': '固定支座 (全固定)'
}
```

### Logging Pattern
All operations log to both file and terminal:
```python
logging.info(f"Applied point load: {point_load} kN at position {point_position:.1%}")
```

## Critical Dependencies

- **Streamlit**: UI framework - all interactions through `st.*` components
- **xara**: Professional FEA engine (may not be available on all systems)
- **simple_fea.py**: Fallback FEA implementation using NumPy/SciPy
- **Plotly**: 3D visualization with `mesh3d` for pier columns
- **Pandas**: Result tabulation and export

## Error Handling Patterns

Always check for analysis engine availability:
```python
analysis_ok = results.get('analysis_ok', True)  # Simple FEA defaults to True
if not analysis_ok:
    st.error("❌ Analysis failed!")
```

Use safe attribute access for cross-engine compatibility:
```python
max_disp = results.get('max_displacement', 0)
if max_disp == 0 and 'displacements' in results:
    max_disp = max(abs(d) for d in results['displacements'])
```
