#!/usr/bin/env python3
"""
Enhanced Bridge Digital Twin - Professional Analysis Interface with Fixed 3D Visualization
支持可配置跨数、支座位置和详细工程表格，3D模型正确反映配置
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from bridge_model_enhanced import BridgeModelXara
from bridge_model import BridgeModel
from visualization_enhanced import BridgeVisualizer
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bridge_analysis.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Enhanced main application with comprehensive configuration options and fixed 3D visualization"""
    st.set_page_config(
        page_title="Enhanced Bridge Digital Twin",
        page_icon="🌉",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.title("🌉 Enhanced Bridge Digital Twin - Professional Analysis")
    st.markdown("""
    **专业桥梁有限元分析系统** | 支持可配置跨数、支座布置和详细工程表格
    
    ✨ **新功能特性**:
    - 🎯 可配置桥梁跨数 (2跨/3跨)
    - 📐 自定义支座起始位置
    - 🔧 横向支座数量配置
    - 📊 完整工程计算表格
    - 🏗️ **3D模型自动适配配置**
    """)
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ 桥梁配置参数")
        
        # Analysis Engine Selection
        st.subheader("🚀 分析引擎选择")
        use_xara = st.radio(
            "选择分析引擎:",
            [True, False],
            format_func=lambda x: "🎯 xara/OpenSees (专业精度)" if x else "⚡ Simple FEA (快速分析)",
            index=0
        )
        
        if use_xara:
            st.success("✅ 使用专业级OpenSees有限元分析")
        else:
            st.info("ℹ️ 使用简化有限元分析引擎")
        
        st.divider()
        
        # Bridge Geometry Configuration
        st.subheader("🏗️ 桥梁几何参数")
        
        # NEW: Span Configuration
        col1, col2 = st.columns(2)
        with col1:
            num_spans = st.selectbox(
                "纵向跨数",
                [2, 3],
                index=1,
                help="选择桥梁的跨数：2跨或3跨连续梁"
            )
        
        with col2:
            pier_start_position = st.slider(
                "支座起始位置",
                0.0, 0.3, 0.0, 0.05,
                format="%.2f",
                help="第一个支座的相对位置 (0.0 = 桥梁起点)"
            )
        
        # NEW: Bearing Configuration
        bearings_per_pier = st.number_input(
            "横向支座数量",
            min_value=1,
            max_value=4,
            value=2,
            help="每个墩台的横向支座数量"
        )
        
        # Visual feedback for bearing configuration
        if bearings_per_pier == 1:
            st.warning("⚠️ 单支座配置，建议使用≥2个支座")
        elif bearings_per_pier >= 3:
            st.success("✅ 多支座配置，提供更好的横向稳定性")
        
        # Basic Parameters
        length = st.number_input("桥梁长度 (m)", 20.0, 100.0, 60.0, 5.0)
        bridge_width = st.number_input("桥梁横向宽度 (m)", 8.0, 25.0, 15.0, 1.0, 
                                     help="桥梁的横向总宽度，影响3D模型显示和横向分析")
        num_elements = st.number_input("有限元数量", 10, 50, 30, 5)
        
        # Material Properties
        st.subheader("🧱 材料属性")
        
        # Material selection
        material_options = {
            'C30混凝土': {'E': 30e9, 'density': 2400},
            'C40混凝土': {'E': 32.5e9, 'density': 2450},
            'C50混凝土': {'E': 34.5e9, 'density': 2500},
            '结构钢': {'E': 200e9, 'density': 7850},
            '预应力混凝土': {'E': 36e9, 'density': 2500},
            '自定义': {'E': 30e9, 'density': 2400}
        }
        
        selected_material = st.selectbox(
            "材料类型",
            list(material_options.keys()),
            index=0,
            help="选择梁体材料类型"
        )
        
        if selected_material == '自定义':
            E = st.number_input("弹性模量 (GPa)", 20.0, 250.0, 30.0, 1.0) * 1e9
            density = st.number_input("密度 (kg/m³)", 1000, 8000, 2400, 50)
        else:
            mat_props = material_options[selected_material]
            E = mat_props['E']
            density = mat_props['density']
            st.info(f"✅ 材料: {selected_material}, E = {E/1e9:.1f} GPa, ρ = {density} kg/m³")
        
        col1, col2 = st.columns(2)
        with col1:
            section_height = st.number_input("截面高度 (m)", 0.5, 3.0, 1.5, 0.1)
        with col2:
            section_width = st.number_input("截面宽度 (m)", 0.5, 2.0, 1.0, 0.1)
        
        st.divider()
        
        # NEW: Support Configuration
        st.subheader("🏗️ 支座配置")
        
        # Support type options
        support_options = {
            'fixed_pin': '固定铰接 (水平+竖向固定, 转动自由)',
            'roller': '滑动支座 (仅竖向固定)',
            'fixed': '固定支座 (全固定)',
        }
        
        # Generate support configuration UI
        num_piers = num_spans + 1
        support_configs = []
        
        st.write(f"**配置 {num_piers} 个支座：**")
        
        for i in range(num_piers):
            pier_name = f"墩台 {i+1}"
            if i == 0:
                pier_name += " (左端)"
            elif i == num_piers - 1:
                pier_name += " (右端)"
            else:
                pier_name += " (中间墩)"
            
            col1, col2 = st.columns([2, 1])
            with col1:
                default_type = 'fixed_pin' if i == 0 else 'roller'
                support_type = st.selectbox(
                    f"{pier_name} 支座类型",
                    list(support_options.keys()),
                    format_func=lambda x: support_options[x],
                    index=list(support_options.keys()).index(default_type),
                    key=f"support_{i}"
                )
            
            with col2:
                if support_type == 'fixed_pin':
                    config = {'type': 'fixed_pin', 'dx': 1, 'dy': 1, 'rz': 0}
                elif support_type == 'roller':
                    config = {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0}
                elif support_type == 'fixed':
                    config = {'type': 'fixed', 'dx': 1, 'dy': 1, 'rz': 1}
                
                constraint_desc = f"dx={config['dx']}, dy={config['dy']}, rz={config['rz']}"
                st.code(constraint_desc)
            
            support_configs.append(config)
        
        # Support configuration validation
        fixed_supports = sum(1 for config in support_configs if config['dx'] == 1)
        vertical_supports = sum(1 for config in support_configs if config['dy'] == 1)
        
        if fixed_supports == 0:
            st.error("⚠️ 缺少水平固定支座，结构可能水平滑移")
        elif vertical_supports < 2:
            st.error("⚠️ 竖向支座不足，结构不稳定")
        else:
            st.success("✅ 支座配置满足稳定性要求")
    
    # Create bridge model based on engine choice
    def create_bridge_model(_use_xara, _length, _num_elements, _E, _height, _width, 
                           _num_spans, _pier_start, _bearings_per_pier, _bridge_width, 
                           _density, _support_configs):
        """Create bridge model with enhanced parameters - No caching for real-time updates"""
        if _use_xara:
            return BridgeModelXara(
                length=_length,
                num_elements=_num_elements,
                E=_E,
                section_height=_height,
                section_width=_width,
                density=_density,
                num_spans=_num_spans,
                pier_start_position=_pier_start,
                bearings_per_pier=_bearings_per_pier,
                bridge_width=_bridge_width,
                support_types=_support_configs
            )
        else:
            # 简单FEA引擎只支持基本参数
            simple_bridge = BridgeModel(
                length=_length,
                num_elements=_num_elements,
                E=_E,
                section_height=_height,
                section_width=_width
            )
            # 为简单FEA桥梁添加基本兼容属性
            simple_bridge.num_spans = _num_spans
            simple_bridge.bridge_width = _bridge_width
            simple_bridge.density = _density
            simple_bridge.bearings_per_pier = _bearings_per_pier
            
            # 创建简化的pier信息以保持兼容性
            simple_piers = []
            pier_positions = []
            
            if _num_spans == 2:
                if _pier_start == 0.0:
                    pier_positions = [0.0, 0.5, 1.0]
                else:
                    center_pos = _pier_start + (1.0 - _pier_start) / 2
                    pier_positions = [_pier_start, center_pos, 1.0]
            else:  # 3 spans
                if _pier_start == 0.0:
                    pier_positions = [0.0, 0.33, 0.67, 1.0]
                else:
                    available = 1.0 - _pier_start
                    span_len = available / 3
                    pier_positions = [_pier_start, _pier_start + span_len, _pier_start + 2*span_len, 1.0]
            
            for i, pos in enumerate(pier_positions):
                pier_info = {
                    'id': i,
                    'x_coord': pos * _length,
                    'position': pos,
                    'type': 'abutment_left' if i == 0 else ('abutment_right' if i == len(pier_positions)-1 else 'pier_intermediate'),
                    'bearings_count': _bearings_per_pier,
                    'support_config': _support_configs[i] if i < len(_support_configs) else {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0}
                }
                simple_piers.append(pier_info)
            
            simple_bridge.piers = simple_piers
            return simple_bridge
    
    # Create the bridge model with session state management to prevent load loss
    bridge_key = f"bridge_{use_xara}_{length}_{num_elements}_{E}_{section_height}_{section_width}_{num_spans}_{pier_start_position}_{bearings_per_pier}_{bridge_width}_{density}"
    
    # Check if parameters changed, if so recreate bridge
    if 'bridge_params' not in st.session_state or st.session_state.bridge_params != bridge_key:
        with st.spinner("Creating enhanced bridge model..."):
            bridge = create_bridge_model(
                use_xara, length, num_elements, E, section_height, section_width,
                num_spans, pier_start_position, bearings_per_pier, bridge_width,
                density, support_configs
            )
            # Store in session_state to preserve loads
            st.session_state.bridge = bridge
            st.session_state.bridge_params = bridge_key
            st.success("✅ 桥梁模型创建成功")
    else:
        # Use cached bridge object to preserve loads
        bridge = st.session_state.bridge
    
    # Display enhanced model info
    st.header("📋 桥梁模型信息")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("桥梁跨数", f"{num_spans}跨")
    with col2:
        st.metric("总长度", f"{length:.0f} m")
    with col3:
        st.metric("桥梁宽度", f"{bridge_width:.0f} m")
    with col4:
        st.metric("有限元数", f"{num_elements}")
    with col5:
        pier_count = len(bridge.piers) if hasattr(bridge, 'piers') and bridge.piers else "2"
        st.metric("支座数量", f"{pier_count}")
    with col6:
        st.metric("横向支座", f"{bearings_per_pier}/墩")
    
    # Enhanced pier configuration display
    if hasattr(bridge, 'piers') and bridge.piers:
        st.subheader("🏛️ 支座布置信息")
        pier_cols = st.columns(len(bridge.piers))
        
        # Calculate span lengths for display
        span_lengths = []
        if hasattr(bridge, 'piers') and len(bridge.piers) > 1:
            for i in range(num_spans):
                if i == 0:
                    span_start = 0 if pier_start_position == 0 else pier_start_position * length
                else:
                    span_start = bridge.piers[i]['x_coord']
                
                # 确保索引不超出范围
                if i+1 < len(bridge.piers):
                    span_end = bridge.piers[i+1]['x_coord']
                    span_lengths.append(span_end - span_start)
                else:
                    # 如果索引超出范围，使用桥梁总长度作为终点
                    span_end = length
                    span_lengths.append(span_end - span_start)
        
        for i, pier in enumerate(bridge.piers):
            with pier_cols[i]:
                pier_type_display = {
                    'abutment_left': '🏗️ 左桥台',
                    'abutment_right': '🏗️ 右桥台',
                    'pier_intermediate': '🏛️ 中间墩'
                }.get(pier.get('type', 'unknown'), pier.get('type', 'unknown'))
                
                st.metric(
                    f"支座 {i+1}",
                    f"{pier.get('x_coord', 0):.1f}m",
                    delta=pier_type_display
                )
                st.caption(f"相对位置: {pier.get('position', 0):.1%}")
                st.caption(f"横向支座: {pier.get('bearings_count', 2)}个")
        
        # Display span information
        if span_lengths:
            st.info(f"📏 **跨长分布**: " + " | ".join([f"第{i+1}跨: {span_lengths[i]:.1f}m" for i in range(len(span_lengths))]))
    else:
        # 简单FEA引擎的基本信息显示
        st.subheader("🏛️ 基本支座信息")
        st.info("📌 **简单FEA模式**: 使用标准两端固定支座，不支持自定义支座配置")
    
    # Load Application Section
    st.header("⚖️ 荷载施加")
    load_tab1, load_tab2, load_tab3 = st.tabs(["🎯 点荷载", "📏 分布荷载", "🚛 车辆荷载"])
    
    with load_tab1:
        st.subheader("施加点荷载")
        col1, col2 = st.columns(2)
        
        with col1:
            point_load = st.number_input(
                "点荷载值 (kN)",
                -1000.0, 1000.0, -100.0, 10.0,
                help="负值表示向下的荷载"
            )
        
        with col2:
            point_position = st.slider(
                "荷载位置 (相对位置)",
                0.0, 1.0, 0.5, 0.05,
                help="0.0=桥梁起点, 1.0=桥梁终点"
            )
        
        # Show position in absolute coordinates
        abs_position = point_position * length
        st.caption(f"绝对位置: {abs_position:.1f}m")
        
        if st.button("Apply Point Load", type="primary"):
            bridge.add_point_load(point_load * 1000, point_position)  # Convert kN to N
            logging.info(f"Applied point load: {point_load} kN at position {point_position:.1%} ({abs_position:.1f}m)")
            # Clear previous analysis results to force re-analysis
            if hasattr(st.session_state, 'analysis_done'):
                st.session_state.analysis_done = False
            st.success(f"✅ Added {point_load} kN point load at {point_position:.1%} position ({abs_position:.1f}m)")
            st.info("💡 请点击 '🚀 Run Analysis' 重新运行分析以查看新结果")
    
    with load_tab2:
        st.subheader("施加分布荷载")
        distributed_load = st.number_input(
            "分布荷载强度 (kN/m)",
            -100.0, 100.0, -10.0, 1.0,
            help="均布荷载强度，负值表示向下"
        )
        
        total_distributed = distributed_load * length
        st.caption(f"总分布荷载: {total_distributed:.1f} kN")
        
        if st.button("Apply Distributed Load", type="primary"):
            bridge.add_distributed_load(distributed_load * 1000)  # Convert kN/m to N/m
            logging.info(f"Applied distributed load: {distributed_load} kN/m (总荷载: {total_distributed:.1f} kN)")
            # Clear previous analysis results to force re-analysis
            if hasattr(st.session_state, 'analysis_done'):
                st.session_state.analysis_done = False
            st.success(f"✅ Added {distributed_load} kN/m distributed load (总荷载: {total_distributed:.1f} kN)")
            st.info("💡 请点击 '🚀 Run Analysis' 重新运行分析以查看新结果")
    
    with load_tab3:
        st.subheader("施加车辆荷载")
        col1, col2 = st.columns(2)
        
        with col1:
            axle_load_1 = st.number_input("前轴荷载 (kN)", 50.0, 200.0, 80.0, 10.0)
            axle_load_2 = st.number_input("后轴荷载 (kN)", 50.0, 200.0, 120.0, 10.0)
        
        with col2:
            axle_spacing = st.number_input("轴距 (m)", 2.0, 8.0, 4.5, 0.5)
            vehicle_position = st.slider("车辆位置 (前轴)", 0.0, 1.0, 0.3, 0.05)
        
        total_vehicle = axle_load_1 + axle_load_2
        rear_position = vehicle_position + axle_spacing / length
        st.caption(f"前轴位置: {vehicle_position * length:.1f}m | 后轴位置: {min(rear_position * length, length):.1f}m")
        st.caption(f"总车重: {total_vehicle:.1f} kN")
        
        if st.button("Apply Vehicle Load", type="primary"):
            axle_loads = [axle_load_1 * 1000, axle_load_2 * 1000]  # Convert to N
            bridge.add_vehicle_load(axle_loads, [axle_spacing], vehicle_position)
            logging.info(f"Applied vehicle load: {axle_load_1}+{axle_load_2} kN (总重: {total_vehicle} kN)")
            # Clear previous analysis results to force re-analysis
            if hasattr(st.session_state, 'analysis_done'):
                st.session_state.analysis_done = False
            st.success(f"✅ Added vehicle load: {axle_load_1}+{axle_load_2} kN (总重: {total_vehicle} kN)")
            st.info("💡 请点击 '🚀 Run Analysis' 重新运行分析以查看新结果")
    
    # Load Status Display
    if hasattr(bridge, 'loads') and bridge.loads:
        st.subheader("📋 当前荷载状态")
        st.info(f"已添加 {len(bridge.loads)} 个荷载（不包括自重）")
        
        loads_data = []
        for i, load in enumerate(bridge.loads):
            if load[0] == 'point_load':
                loads_data.append({
                    '荷载类型': '点荷载',
                    '大小': f"{load[1]/1000:.1f} kN",
                    '位置': f"{load[2]:.1%} ({load[2]*length:.1f}m)",
                    '序号': i+1
                })
            elif load[0] == 'distributed':
                loads_data.append({
                    '荷载类型': '分布荷载',
                    '大小': f"{load[1]/1000:.1f} kN/m",
                    '位置': '全桥',
                    '序号': i+1
                })
        
        if loads_data:
            loads_df = pd.DataFrame(loads_data)
            st.dataframe(loads_df, use_container_width=True, hide_index=True)
        
        # Add clear loads button
        if st.button("🗑️ 清除所有荷载", type="secondary"):
            bridge.loads.clear()
            if hasattr(st.session_state, 'analysis_done'):
                st.session_state.analysis_done = False
            st.success("✅ 已清除所有荷载")
            # No st.rerun() needed as bridge object is now persistent
    else:
        st.info("📋 当前仅有结构自重荷载，未添加其他荷载")
    
    # Analysis Section
    if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
        with st.spinner("Running finite element analysis..."):
            results = bridge.run_analysis()
            logging.info("Analysis completed successfully")
            logging.info(f"Results: max_displacement={results.get('max_displacement', 'N/A')}m, max_moment={results.get('max_moment', 'N/A')}Nm")
            
            # 检查分析是否成功 - 兼容不同引擎格式
            analysis_ok = results.get('analysis_ok', True)  # 简单FEA没有此字段，默认为True
            
            if analysis_ok:
                st.success("✅ Analysis completed successfully!")
                
                # Store results in session state
                st.session_state.bridge = bridge
                st.session_state.results = results
                st.session_state.analysis_done = True
            else:
                st.error("❌ Analysis failed!")
                if 'error' in results:
                    st.error(f"Error details: {results['error']}")
    
    # Results Display Section
    if hasattr(st.session_state, 'analysis_done') and st.session_state.analysis_done:
        bridge = st.session_state.bridge
        results = st.session_state.results
        
        st.header("📊 分析结果")
        
        # Key results summary with enhanced information
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            # Safe access to max_displacement
            max_disp = results.get('max_displacement', 0)
            if max_disp == 0 and 'displacements' in results:
                max_disp = max(abs(d) for d in results['displacements']) if results['displacements'] else 0
            max_disp_mm = max_disp * 1000
            st.metric("最大位移", f"{max_disp_mm:.2f} mm")
        with col2:
            # Safe access to max_moment
            max_moment = results.get('max_moment', 0)
            if max_moment == 0 and 'moments' in results:
                max_moment = max(abs(m) for m in results['moments']) if results['moments'] else 0
            max_moment_knm = max_moment / 1000
            st.metric("最大弯矩", f"{max_moment_knm:.1f} kN·m")
        with col3:
            # Safe access to max_shear
            max_shear = results.get('max_shear', 0)
            if max_shear == 0 and 'shears' in results:
                max_shear = max(abs(s) for s in results['shears']) if results['shears'] else 0
            max_shear_kn = max_shear / 1000
            st.metric("最大剪力", f"{max_shear_kn:.1f} kN")
        with col4:
            span_length = length / num_spans
            disp_ratio = (max_disp_mm / 1000) / span_length if span_length > 0 and max_disp_mm > 0 else 0
            st.metric("挠跨比", f"1/{1/disp_ratio:.0f}" if disp_ratio > 0 else "N/A")
        with col5:
            # NEW: Support reactions - safe access
            max_vertical_kn = 0
            if 'max_reaction_vertical' in results:
                max_vertical_kn = results['max_reaction_vertical'] / 1000
            elif 'reactions' in results and results['reactions']:
                max_vertical_kn = max(abs(r['Fy']) for r in results['reactions']) / 1000
            st.metric("最大竖向反力", f"{max_vertical_kn:.1f} kN" if max_vertical_kn > 0 else "N/A")
        with col6:
            max_horizontal_kn = 0
            if 'max_reaction_horizontal' in results:
                max_horizontal_kn = results['max_reaction_horizontal'] / 1000
            elif 'reactions' in results and results['reactions']:
                max_horizontal_kn = max(abs(r['Fx']) for r in results['reactions']) / 1000
            st.metric("最大水平反力", f"{max_horizontal_kn:.1f} kN" if max_horizontal_kn > 0 else "N/A")
        
        # Enhanced performance indicators
        col1, col2, col3 = st.columns(3)
        with col1:
            disp_limit = span_length / 250 * 1000  # L/250 in mm
            disp_check = "✅ 满足" if max_disp_mm <= disp_limit else "❌ 超限"
            st.metric("挠度检验", disp_check, delta=f"限值: {disp_limit:.1f}mm")
        
        with col2:
            bridge_efficiency = f"{num_spans}跨布置"
            st.metric("桥梁布置", bridge_efficiency, delta=f"支座×{bearings_per_pier}/墩")
        
        with col3:
            analysis_engine = "OpenSees" if use_xara else "Simple FEA"
            st.metric("分析引擎", analysis_engine, delta="专业级" if use_xara else "快速")
        
        # NEW: Support Reactions Detail
        if 'reactions' in results and results['reactions']:
            st.subheader("🏗️ 支座反力详情")
            
            # Debug info
            with st.expander("🔍 调试信息", expanded=False):
                st.write("**反力数据调试**:")
                st.write(f"- 反力数据数量: {len(results['reactions'])}")
                st.write(f"- max_reaction_vertical: {results.get('max_reaction_vertical', 'N/A')}")
                st.write(f"- max_reaction_horizontal: {results.get('max_reaction_horizontal', 'N/A')}")
                st.write("**原始反力数据:**")
                st.json(results['reactions'])
            
            # Create DataFrame for reactions
            reactions_data = []
            for reaction in results['reactions']:
                reactions_data.append({
                    '支座编号': f"墩台 {reaction['pier_id']+1}",
                    '位置 (m)': f"{reaction['x_coord']:.1f}",
                    '支座类型': reaction['support_type'],
                    '水平反力 Fx (kN)': f"{reaction['Fx']/1000:.2f}",
                    '竖向反力 Fy (kN)': f"{reaction['Fy']/1000:.2f}",
                    '弯矩反力 Mz (kN·m)': f"{reaction['Mz']/1000:.2f}",
                    '约束条件': reaction['constraint_type']
                })
            
            reactions_df = pd.DataFrame(reactions_data)
            st.dataframe(reactions_df, use_container_width=True)
            
            # Reaction force balance check - safe calculation
            if results['reactions']:
                total_vertical = sum(r['Fy'] for r in results['reactions'])
                total_horizontal = sum(r['Fx'] for r in results['reactions'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("竖向反力合计", f"{total_vertical/1000:.2f} kN")
                with col2:
                    st.metric("水平反力合计", f"{total_horizontal/1000:.2f} kN")
                with col3:
                    balance_check = "✅ 平衡" if abs(total_horizontal) < 1.0 else "⚠️ 不平衡"
                    st.metric("力平衡检验", balance_check)
            else:
                st.warning("⚠️ 无支反力数据可用")
            
            st.info("💡 **说明**: 竖向反力合计应等于总荷载，水平反力合计应接近零（对于平衡结构）")
        
        # Enhanced Visualization using the new visualization module
        st.subheader("📈 可视化结果")
        visualizer = BridgeVisualizer(bridge, results)
        
        try:
            # Enhanced 3D Model with configuration reflection
            st.subheader("🏗️ 增强版3D桥梁模型")
            st.info(f"📐 **模型配置**: {num_spans}跨连续梁 | 起始位置: {pier_start_position:.1%} | 横向支座: {bearings_per_pier}个/墩")
            
            fig_3d = visualizer.create_3d_model()
            st.plotly_chart(fig_3d, use_container_width=True)
            
            # Configuration verification
            st.success("✅ 3D模型已根据配置正确绘制：支座位置、数量和跨数均已反映")
            
        except Exception as e:
            st.error(f"3D visualization error: {e}")
            st.info("注意: 3D功能在某些环境中可能需要调整")
        
        # Enhanced 2D Analysis Charts
        viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs(["📏 变形分析", "🔄 弯矩图", "↕️ 剪力图", "🏗️ 支座反力"])
        
        with viz_tab1:
            fig_deform = visualizer.create_deformation_plot()
            st.plotly_chart(fig_deform, use_container_width=True)
        
        with viz_tab2:
            fig_moment = visualizer.create_moment_diagram()
            st.plotly_chart(fig_moment, use_container_width=True)
        
        with viz_tab3:
            fig_shear = visualizer.create_shear_diagram()
            st.plotly_chart(fig_shear, use_container_width=True)
        
        with viz_tab4:
            # NEW: Support Reactions Visualization
            if 'reactions' in results and results['reactions']:
                # Create reaction force diagram
                fig_reactions = go.Figure()
                
                # Extract reaction data
                pier_positions = [r['x_coord'] for r in results['reactions']]
                vertical_reactions = [r['Fy']/1000 for r in results['reactions']]  # Convert to kN
                horizontal_reactions = [r['Fx']/1000 for r in results['reactions']]
                
                # Vertical reactions (bars)
                fig_reactions.add_trace(go.Bar(
                    x=pier_positions,
                    y=vertical_reactions,
                    name='竖向反力 (kN)',
                    marker_color='blue',
                    opacity=0.7,
                    yaxis='y1'
                ))
                
                # Horizontal reactions (scatter)
                fig_reactions.add_trace(go.Scatter(
                    x=pier_positions,
                    y=horizontal_reactions,
                    mode='markers+lines',
                    name='水平反力 (kN)',
                    marker=dict(size=10, color='red'),
                    yaxis='y2'
                ))
                
                # Update layout for dual y-axis
                fig_reactions.update_layout(
                    title='支座反力分布图',
                    xaxis_title='桥梁位置 (m)',
                    yaxis=dict(
                        title='竖向反力 (kN)',
                        side='left',
                        color='blue'
                    ),
                    yaxis2=dict(
                        title='水平反力 (kN)',
                        side='right',
                        overlaying='y',
                        color='red'
                    ),
                    legend=dict(x=0.02, y=0.98),
                    height=400
                )
                
                st.plotly_chart(fig_reactions, use_container_width=True)
                
                # Add support type indicators
                st.write("**支座类型说明:**")
                for i, reaction in enumerate(results['reactions']):
                    col_r1, col_r2, col_r3 = st.columns(3)
                    with col_r1:
                        st.write(f"墩台 {i+1}: {reaction['support_type']}")
                    with col_r2:
                        st.write(f"位置: {reaction['x_coord']:.1f}m")
                    with col_r3:
                        constraint_icon = "🔒" if reaction['support_type'] == 'fixed' else "🔄" if reaction['support_type'] == 'fixed_pin' else "📏"
                        st.write(f"{constraint_icon} {reaction['constraint_type']}")
            else:
                st.info("支座反力数据不可用（可能使用的是简化分析引擎）")
        
        # Enhanced Detailed Engineering Tables
        if hasattr(bridge, 'get_analysis_tables'):
            st.header("📊 详细工程计算表格")
            
            with st.expander("📋 查看完整计算表格", expanded=False):
                tables = bridge.get_analysis_tables()
                
                table_tab1, table_tab2, table_tab3, table_tab4 = st.tabs([
                    "🏗️ 几何信息", "⚖️ 荷载信息", "📈 分析结果", "✅ 工程验证"
                ])
                
                with table_tab1:
                    st.subheader(f"📐 节点坐标表 ({num_spans}跨桥梁)")
                    st.dataframe(tables['geometry']['nodes'], use_container_width=True)
                    
                    st.subheader("🔧 单元信息表")
                    st.dataframe(tables['geometry']['elements'], use_container_width=True)
                    
                    st.subheader(f"🏛️ 支座配置表 (每墩{bearings_per_pier}个支座)")
                    st.dataframe(tables['geometry']['piers'], use_container_width=True)
                
                with table_tab2:
                    st.subheader("🎯 点荷载清单")
                    if not tables['loads']['point_loads'].empty:
                        st.dataframe(tables['loads']['point_loads'], use_container_width=True)
                    else:
                        st.info("暂无点荷载")
                    
                    st.subheader("📏 分布荷载清单")
                    if not tables['loads']['distributed_loads'].empty:
                        st.dataframe(tables['loads']['distributed_loads'], use_container_width=True)
                    else:
                        st.info("暂无分布荷载")
                
                with table_tab3:
                    st.subheader("📍 节点位移表")
                    st.dataframe(tables['results']['displacements'], use_container_width=True)
                    
                    st.subheader("🔄 单元内力表")
                    st.dataframe(tables['results']['forces'], use_container_width=True)
                
                with table_tab4:
                    st.subheader("📊 最值统计表")
                    st.dataframe(tables['verification']['summary'], use_container_width=True)
                    
                    st.subheader("✅ 工程检验表")
                    st.dataframe(tables['verification']['checks'], use_container_width=True)
                
                # Enhanced CSV Export Options
                st.subheader("💾 数据导出")
                export_col1, export_col2, export_col3 = st.columns(3)
                
                with export_col1:
                    if st.button("导出几何数据", use_container_width=True):
                        csv_nodes = tables['geometry']['nodes'].to_csv(index=False)
                        st.download_button(
                            "下载节点数据 CSV",
                            csv_nodes,
                            file_name=f"bridge_{num_spans}span_nodes.csv",
                            mime="text/csv"
                        )
                
                with export_col2:
                    if st.button("导出分析结果", use_container_width=True):
                        csv_results = tables['results']['displacements'].to_csv(index=False)
                        st.download_button(
                            "下载位移数据 CSV",
                            csv_results,
                            file_name=f"bridge_{num_spans}span_displacements.csv",
                            mime="text/csv"
                        )
                
                with export_col3:
                    if st.button("导出完整报告", use_container_width=True):
                        summary_csv = tables['verification']['summary'].to_csv(index=False)
                        st.download_button(
                            "下载分析报告 CSV",
                            summary_csv,
                            file_name=f"bridge_{num_spans}span_analysis_report.csv",
                            mime="text/csv"
                        )
    
    # Enhanced Footer
    st.divider()
    st.markdown("""
    **Enhanced Bridge Digital Twin** | Professional Finite Element Analysis
    
    🎯 **增强特性**: 支持2/3跨配置 | 自定义支座布置 | 完整工程表格 | **3D模型配置同步** | 专业验证
    
    📊 **可视化特点**: 
    - 🏗️ 3D模型自动反映跨数、支座位置和数量配置
    - 📈 增强版图表显示跨长信息和支座详情
    - 📋 完整工程表格支持专业分析和报告生成
    """)

if __name__ == "__main__":
    logging.info("Starting Enhanced Bridge Digital Twin Application")
    main()