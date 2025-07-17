# Bridge Digital Twin - Enhanced Continuous Beam Analysis

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

一个专业的连续梁桥数字孪生系统，支持可配置跨数、支座布置和详细工程表格分析。

## 🌟 特性

- **双引擎分析**: 支持 xara/OpenSees 专业分析和简化 FEA 快速分析
- **可配置桥梁**: 支持 2跨/3跨连续梁，自定义支座位置和类型
- **3D 可视化**: 交互式 3D 桥梁模型，自动反映配置参数
- **多种荷载**: 点荷载、分布荷载、车辆荷载模拟
- **实时结果**: 位移、弯矩、剪力图表和支座反力分析
- **工程表格**: 完整的计算表格和数据导出功能

## 🚀 快速开始

### 在线体验
访问我们的在线演示：[Bridge Digital Twin App](https://share.streamlit.io) (部署后替换链接)

### 本地运行
```bash
# 克隆仓库
git clone https://github.com/yourusername/bridge-digital-twin.git
cd bridge-digital-twin

# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run main_enhanced_fixed.py
```

## 📋 系统要求

- Python 3.8+
- 主要依赖：Streamlit, NumPy, Pandas, Plotly, Matplotlib

## 🏗️ 项目结构

```
├── main_enhanced_fixed.py      # 主程序入口
├── bridge_model.py            # 简化 FEA 桥梁模型
├── bridge_model_enhanced.py   # 增强版桥梁模型 (xara/OpenSees)
├── simple_fea.py             # 自制有限元分析引擎
├── visualization_enhanced.py  # 3D 可视化模块
├── requirements.txt           # 项目依赖
└── .github/
    └── copilot-instructions.md # AI 开发指南
```
- **Frontend**: Streamlit
- **3D Visualization**: Plotly with mesh3d for pier columns
- **2D Plots**: Matplotlib with pier location indicators
- **Computing**: NumPy, Pandas, SciPy

## Quick Start

### 1. Environment Setup

Create a conda environment (recommended):

```bash
conda create -n bridge-twin python=3.9
conda activate bridge-twin
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

**Option A: Quick start script**
```bash
python run_demo.py
```

**Option B: Direct streamlit**
```bash
streamlit run main.py
```

The application will open in your web browser at `http://localhost:8501`

## How to Use

### Bridge Configuration
1. **Adjust Bridge Geometry**:
   - Total bridge length (40-120m)
   - Number of finite elements (20-60)
   - Section properties (height: 1.0-3.0m, width: 0.5-2.0m)

2. **Set Material Properties**:
   - Elastic modulus (20-50 GPa)
   - Concrete density (2000-3000 kg/m³)

### Loading Options
3. **Choose Load Type**:
   - **Point Load**: Single concentrated load at specified location
   - **Distributed Load**: Uniform load across entire bridge
   - **Vehicle Load**: Truck with front and rear axles (4m spacing)

4. **Run Analysis**:
   - Click "Run Analysis" button
   - Wait for FEA computation to complete

### Results Visualization
5. **View Results** in 4 tabs:
   - **3D Model**: Interactive 3D bridge with pier columns and bearings
   - **Deformation**: Displacement profile with pier locations marked
   - **Moment Diagram**: Bending moment distribution with pier indicators
   - **Shear Diagram**: Shear force distribution with pier indicators

## Model Details

- **Element Type**: Elastic beam-column elements (Euler-Bernoulli beam theory)
- **Support Conditions**: 
  - Pier 1 (Abutment): Fixed (prevents translation and rotation)
  - Pier 2 (Main): Roller (prevents vertical translation only)
  - Pier 3 (Abutment): Fixed (prevents translation and rotation)
- **Analysis Type**: Static linear analysis
- **Units**: SI units (meters, Newtons, Pascals)
- **Degrees of Freedom**: 3 DOF per node (ux, uy, rz)

## Architecture

```
├── main.py              # Streamlit main application
├── bridge_model.py      # Continuous bridge model using simplified FEA
├── simple_fea.py        # Custom FEA engine (beam elements)
├── visualization.py     # Advanced plotting and 3D visualization
├── test_functionality.py # Comprehensive functionality tests
├── run_demo.py         # Quick start script
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## FEA Implementation

Our custom FEA engine implements:

- **Beam Elements**: 2D Euler-Bernoulli beam elements with 3 DOF per node
- **Stiffness Matrix**: Standard beam stiffness formulation
- **Coordinate Transformation**: Local to global coordinate transformation
- **Boundary Conditions**: Multiple support types and loading
- **Solution**: Direct sparse matrix solution using SciPy

### Pier Support Modeling
- **Abutments**: Fixed supports (constrain x, y translations)
- **Main Pier**: Roller support (constrain y translation only)
- **Bearing Details**: Dual bearings per pier for realistic load transfer

## Extending the Demo

To add more features:

1. **More Bridge Types**: Add cable-stayed, arch, or truss bridges
2. **Dynamic Analysis**: Include time-history or modal analysis
3. **Material Models**: Add nonlinear material behavior
4. **Advanced Loading**: Implement moving loads or wind loads
5. **Optimization**: Add design optimization capabilities
6. **3D Elements**: Extend to 3D frame elements
7. **Temperature Effects**: Add thermal loading
8. **Construction Sequence**: Model staged construction

## Validation

The simplified FEA results have been validated against analytical solutions for:
- Simply supported beam under point load
- Simply supported beam under distributed load
- Continuous beam configurations
- Multiple support conditions

## Advantages over OpenSees

- **No installation issues**: Pure Python implementation
- **Mac compatibility**: Works on all Mac systems including M1/M2
- **Lightweight**: Minimal dependencies
- **Transparent**: Full source code available and readable
- **Fast**: Quick startup and execution for continuous bridge models
- **Visual**: Rich 3D visualization with detailed pier modeling

## Performance Notes

- Analysis time scales with O(n³) where n is number of nodes
- For real-time interaction, keep elements < 60
- 3D visualization includes detailed pier columns and bearings
- Memory usage is minimal for typical continuous bridge models
- Typical analysis time: < 1 second for 30-element model

## Troubleshooting

### Import Issues

All dependencies are standard Python scientific packages available via pip/conda.

### Plotting Issues

If matplotlib plots don't display properly:

```bash
pip install matplotlib --upgrade
```

### Performance Issues

For large models (>50 elements):
- Reduce number of elements for real-time interaction
- Use coarser mesh for preliminary analysis

### 3D Visualization Issues

If 3D visualization is slow:
- Reduce number of elements
- Close other browser tabs
- Ensure WebGL is enabled in browser

## Example Use Cases

1. **Design Studies**: Compare different pier arrangements
2. **Load Testing**: Analyze response to various loading conditions
3. **Educational**: Learn about continuous bridge behavior
4. **Prototype Development**: Quick structural analysis for preliminary design

## License

Open source - feel free to modify and extend for your needs. 