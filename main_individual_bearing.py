#!/usr/bin/env python3
"""
Enhanced Bridge Digital Twin - Individual Bearing Configuration Interface
支持独立支座配置的专业桥梁分析系统
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from bridge_model_enhanced import BridgeModelXara
from bridge_model import BridgeModel
from visualization_enhanced import BridgeVisualizer
from bridge_3d_analysis import Bridge3DAnalysis
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
    """Enhanced main application with individual bearing configuration"""
    st.set_page_config(
        page_title="桥梁数字孪生 - 独立支座配置",
        page_icon="🌉",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.title("🌉 桥梁数字孪生系统 - 独立支座配置")
    st.markdown("""
    **专业桥梁有限元分析系统** | 支持独立支座精确配置
    
    ✨ **最新功能特性**:
    - 🎯 **独立支座配置** - 每个支座独立设置参数
    - 📐 **新编号系统** - 墩台编号-支座编号 (1-1, 1-2, 2-1, 2-2...)
    - 🔧 **精确高度控制** - 毫米级高度偏移配置
    - 📊 **支座参数管理** - 材质、型式、规格等完整参数
    - 🏗️ **批量配置功能** - 整个墩台的支座批量设置
    """)
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ 桥梁基本配置")
        
        # Analysis Engine Selection
        st.subheader("🚀 分析引擎")
        use_xara = st.radio(
            "选择分析引擎:",
            [True, False],
            format_func=lambda x: "🎯 xara/OpenSees" if x else "⚡ Simple FEA",
            index=0
        )
        
        st.divider()
        
        # Bridge Geometry Configuration
        st.subheader("🏗️ 桥梁几何")
        
        # Bridge basic parameters
        col1, col2 = st.columns(2)
        with col1:
            length = st.number_input("桥长 (m)", 30.0, 120.0, 60.0, 5.0)
            num_spans = st.selectbox("跨数", [2, 3], index=1)
        
        with col2:
            section_height = st.number_input("梁高 (m)", 0.5, 3.0, 1.5, 0.1)
            section_width = st.number_input("梁宽 (m)", 0.5, 2.0, 1.0, 0.1)
        
        # Bearing configuration
        bearings_per_pier = st.number_input(
            "每墩支座数",
            min_value=1,
            max_value=4,
            value=2,
            help="每个墩台的横向支座数量"
        )
        
        bridge_width = st.number_input("桥宽 (m)", 5.0, 25.0, 15.0, 1.0)
        
        # Material properties
        st.subheader("🔧 材料参数")
        E = st.number_input("弹性模量 (GPa)", 20.0, 50.0, 30.0, 1.0) * 1e9
        density = st.number_input("密度 (kg/m³)", 2000, 3000, 2400, 50)
        
        # Analysis parameters
        st.subheader("📊 分析参数")
        num_elements = st.number_input("单元数", 10, 100, 30, 5)
        pier_start_position = st.slider("支座起始位置", 0.0, 0.3, 0.0, 0.05)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🎯 独立支座配置")
        
        # Create bridge model to get pier information
        bridge = BridgeModelXara(
            length=length,
            num_elements=num_elements,
            E=E,
            section_height=section_height,
            section_width=section_width,
            density=density,
            num_spans=num_spans,
            pier_start_position=pier_start_position,
            bearings_per_pier=bearings_per_pier,
            bridge_width=bridge_width
        )
        
        # Initialize individual bearing config in session state
        if 'individual_bearing_config' not in st.session_state:
            st.session_state['individual_bearing_config'] = {}
        
        # Display pier and bearing configuration
        st.write(f"**桥梁配置**: {num_spans}跨, {bridge.num_piers}个墩台, 每墩{bearings_per_pier}个支座")
        st.write(f"**总支座数**: {bridge.num_piers * bearings_per_pier}个")
        
        # Configuration tabs
        tab1, tab2, tab3 = st.tabs(["📐 高度配置", "🔧 支座参数", "📊 配置汇总"])
        
        with tab1:
            st.write("**支座高度偏移配置** (默认0表示同一水平面)")
            
            for pier_idx in range(bridge.num_piers):
                pier_id = pier_idx + 1
                st.write(f"**墩台 {pier_id}**:")
                
                # Pier-level controls
                col_pier1, col_pier2 = st.columns(2)
                with col_pier1:
                    if st.button(f"设置墩台{pier_id}所有支座为0", key=f"reset_pier_{pier_id}"):
                        for bearing_idx in range(bearings_per_pier):
                            bearing_id = bearing_idx + 1
                            bearing_key = f"{pier_id}-{bearing_id}"
                            if bearing_key not in st.session_state['individual_bearing_config']:
                                st.session_state['individual_bearing_config'][bearing_key] = {}
                            st.session_state['individual_bearing_config'][bearing_key]['height_offset'] = 0.0
                        st.rerun()
                
                with col_pier2:
                    if st.button(f"随机设置墩台{pier_id}", key=f"random_pier_{pier_id}"):
                        for bearing_idx in range(bearings_per_pier):
                            bearing_id = bearing_idx + 1
                            bearing_key = f"{pier_id}-{bearing_id}"
                            if bearing_key not in st.session_state['individual_bearing_config']:
                                st.session_state['individual_bearing_config'][bearing_key] = {}
                            # Random offset between -5mm to +5mm
                            random_offset = np.random.uniform(-0.005, 0.005)
                            st.session_state['individual_bearing_config'][bearing_key]['height_offset'] = random_offset
                        st.rerun()
                
                # Individual bearing controls
                for bearing_idx in range(bearings_per_pier):
                    bearing_id = bearing_idx + 1
                    bearing_key = f"{pier_id}-{bearing_id}"
                    
                    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
                    
                    with col_b1:
                        st.write(f"支座{bearing_key}")
                    
                    with col_b2:
                        # Get current offset
                        current_offset = 0.0
                        if bearing_key in st.session_state['individual_bearing_config']:
                            current_offset = st.session_state['individual_bearing_config'][bearing_key].get('height_offset', 0.0)
                        
                        # Height offset input
                        height_offset = st.number_input(
                            f"高度偏移 (mm)",
                            min_value=-50.0,
                            max_value=50.0,
                            value=current_offset * 1000,  # Convert to mm
                            step=0.1,
                            format="%.1f",
                            key=f"height_offset_{bearing_key}"
                        ) / 1000.0  # Convert back to meters
                        
                        # Update session state
                        if bearing_key not in st.session_state['individual_bearing_config']:
                            st.session_state['individual_bearing_config'][bearing_key] = {}
                        st.session_state['individual_bearing_config'][bearing_key]['height_offset'] = height_offset
                    
                    with col_b3:
                        if height_offset == 0.0:
                            st.success("基准")
                        elif height_offset > 0:
                            st.info(f"+{height_offset*1000:.1f}mm")
                        else:
                            st.warning(f"{height_offset*1000:.1f}mm")
                
                st.divider()
        
        with tab2:
            st.write("**支座参数配置**")
            
            # Support type options
            support_options = {
                'fixed_pin': '固定铰接',
                'roller': '滑动支座',
                'fixed': '固定支座'
            }
            
            material_options = ['default', 'steel', 'rubber', 'concrete']
            bearing_type_options = ['elastomeric', 'spherical', 'sliding']
            size_options = ['standard', 'large', 'medium', 'small']
            
            for pier_idx in range(bridge.num_piers):
                pier_id = pier_idx + 1
                st.write(f"**墩台 {pier_id}**:")
                
                for bearing_idx in range(bearings_per_pier):
                    bearing_id = bearing_idx + 1
                    bearing_key = f"{pier_id}-{bearing_id}"
                    
                    with st.expander(f"支座 {bearing_key} 参数"):
                        col_p1, col_p2 = st.columns(2)
                        
                        with col_p1:
                            # Support type
                            default_support = 'fixed_pin' if pier_idx == 0 else 'roller'
                            support_type = st.selectbox(
                                "支座类型",
                                list(support_options.keys()),
                                format_func=lambda x: support_options[x],
                                index=list(support_options.keys()).index(default_support),
                                key=f"support_type_{bearing_key}"
                            )
                            
                            # Material
                            material = st.selectbox(
                                "材质",
                                material_options,
                                key=f"material_{bearing_key}"
                            )
                        
                        with col_p2:
                            # Bearing type
                            bearing_type = st.selectbox(
                                "支座型式",
                                bearing_type_options,
                                key=f"bearing_type_{bearing_key}"
                            )
                            
                            # Size
                            size = st.selectbox(
                                "规格",
                                size_options,
                                key=f"size_{bearing_key}"
                            )
                        
                        # Update session state
                        if bearing_key not in st.session_state['individual_bearing_config']:
                            st.session_state['individual_bearing_config'][bearing_key] = {}
                        
                        # Convert support type to constraint
                        if support_type == 'fixed_pin':
                            support_config = {'type': 'fixed_pin', 'dx': 1, 'dy': 1, 'rz': 0}
                        elif support_type == 'roller':
                            support_config = {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0}
                        elif support_type == 'fixed':
                            support_config = {'type': 'fixed', 'dx': 1, 'dy': 1, 'rz': 1}
                        
                        st.session_state['individual_bearing_config'][bearing_key].update({
                            'support_type': support_config,
                            'material': material,
                            'bearing_type': bearing_type,
                            'size': size
                        })
        
        with tab3:
            st.write("**配置汇总**")
            
            # Create updated bridge model with individual bearing config
            updated_bridge = BridgeModelXara(
                length=length,
                num_elements=num_elements,
                E=E,
                section_height=section_height,
                section_width=section_width,
                density=density,
                num_spans=num_spans,
                pier_start_position=pier_start_position,
                bearings_per_pier=bearings_per_pier,
                bridge_width=bridge_width,
                individual_bearing_config=st.session_state['individual_bearing_config']
            )
            
            # Display bearing summary
            bearing_summary = updated_bridge.get_individual_bearing_summary()
            st.dataframe(bearing_summary, use_container_width=True)
            
            # Statistics
            st.subheader("📊 配置统计")
            heights = [b['height'] for b in updated_bridge.individual_bearings]
            offsets = [b['height_offset'] for b in updated_bridge.individual_bearings]
            
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                st.metric("最高支座", f"{max(heights):.4f}m")
            with col_s2:
                st.metric("最低支座", f"{min(heights):.4f}m")
            with col_s3:
                st.metric("平均高度", f"{np.mean(heights):.4f}m")
            with col_s4:
                st.metric("高度差", f"{(max(heights) - min(heights))*1000:.1f}mm")
    
    with col2:
        st.subheader("🔧 荷载配置与分析")
        
        # Load configuration
        st.write("**荷载配置**:")
        
        # Point loads
        with st.expander("点荷载配置"):
            num_point_loads = st.number_input("点荷载数量", 0, 5, 2)
            
            point_loads = []
            for i in range(num_point_loads):
                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    magnitude = st.number_input(f"荷载{i+1} (kN)", -500, 0, -150, 10, key=f"load_mag_{i}")
                with col_l2:
                    position = st.slider(f"位置{i+1} (%)", 0, 100, 30+i*20, 5, key=f"load_pos_{i}")
                point_loads.append((magnitude * 1000, position / 100))
        
        # Distributed loads
        with st.expander("分布荷载配置"):
            add_distributed = st.checkbox("添加分布荷载")
            distributed_load = 0
            if add_distributed:
                distributed_load = st.number_input("分布荷载强度 (kN/m)", -50, 0, -20) * 1000
        
        # Analysis button
        analysis_method = st.radio(
            "分析方法选择:",
            ["2D简化分析", "3D精确分析"],
            index=1,
            help="2D方法快速但不考虑支座间相互作用；3D方法考虑高度差对荷载分配的影响"
        )
        
        if st.button("🚀 运行结构分析", type="primary"):
            # Create final bridge model
            final_bridge = BridgeModelXara(
                length=length,
                num_elements=num_elements,
                E=E,
                section_height=section_height,
                section_width=section_width,
                density=density,
                num_spans=num_spans,
                pier_start_position=pier_start_position,
                bearings_per_pier=bearings_per_pier,
                bridge_width=bridge_width,
                individual_bearing_config=st.session_state['individual_bearing_config']
            )
            
            # Add loads
            for magnitude, position in point_loads:
                final_bridge.add_point_load(magnitude, position)
            
            if add_distributed:
                final_bridge.add_distributed_load(distributed_load)
            
            # Run analysis
            with st.spinner("正在运行结构分析..."):
                results = final_bridge.run_analysis()
            
            if results['analysis_ok']:
                st.success("✅ 分析完成!")
                
                # Choose analysis method
                if analysis_method == "3D精确分析":
                    # 3D Analysis
                    st.info("🎯 使用3D精确分析方法，考虑支座高度差的影响")
                    
                    analyzer_3d = Bridge3DAnalysis(final_bridge)
                    results_3d = analyzer_3d.analyze_bridge_3d(results['reactions'])
                    
                    # Display 3D results
                    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
                    with col_r1:
                        st.metric("最大位移", f"{results['max_displacement']*1000:.2f}mm")
                    with col_r2:
                        st.metric("最大弯矩", f"{results['max_moment']/1000:.2f}kN·m")
                    with col_r3:
                        st.metric("最大剪力", f"{results['max_shear']/1000:.2f}kN")
                    with col_r4:
                        st.metric("最大支座反力", f"{results_3d['analysis_summary']['max_bearing_load']/1000:.2f}kN")
                    
                    # 3D Analysis Summary
                    st.subheader("🎯 3D分析摘要")
                    col_s1, col_s2, col_s3 = st.columns(3)
                    with col_s1:
                        st.metric("最大支座荷载", f"{results_3d['analysis_summary']['max_bearing_load']/1000:.1f}kN")
                    with col_s2:
                        st.metric("最小支座荷载", f"{results_3d['analysis_summary']['min_bearing_load']/1000:.1f}kN")
                    with col_s3:
                        st.metric("最大高度效应", f"{results_3d['analysis_summary']['max_height_effect']/1000:.1f}kN")
                    
                    # Detailed 3D results table
                    st.subheader("📊 详细支座分析结果")
                    detailed_table = analyzer_3d.get_detailed_results_table(results_3d)
                    st.dataframe(detailed_table, use_container_width=True)
                    
                    # Individual bearing analysis
                    st.subheader("🔍 支座荷载分配分析")
                    
                    # Group by pier for comparison
                    pier_analysis = {}
                    for bearing_id, load_data in results_3d['load_distribution'].items():
                        pier_id = int(bearing_id.split('-')[0])
                        if pier_id not in pier_analysis:
                            pier_analysis[pier_id] = []
                        pier_analysis[pier_id].append((bearing_id, load_data))
                    
                    for pier_id, pier_bearings in pier_analysis.items():
                        with st.expander(f"墩台{pier_id} 支座分析"):
                            total_pier_load = sum(load_data['Fy'] for _, load_data in pier_bearings)
                            st.write(f"**墩台{pier_id}总荷载**: {total_pier_load/1000:.1f}kN")
                            
                            for bearing_id, load_data in pier_bearings:
                                col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                                with col_b1:
                                    st.write(f"**支座{bearing_id}**")
                                with col_b2:
                                    st.metric("基础反力", f"{load_data['base_vertical']/1000:.1f}kN")
                                with col_b3:
                                    if abs(load_data['additional_force']) > 0.1:
                                        st.metric("高度效应", f"{load_data['additional_force']/1000:.1f}kN",
                                                delta=f"{load_data['height_diff']*1000:.1f}mm")
                                    else:
                                        st.metric("高度效应", "0.0kN")
                                with col_b4:
                                    st.metric("最终反力", f"{load_data['Fy']/1000:.1f}kN")
                    
                else:
                    # 2D Analysis (original method)
                    st.info("⚡ 使用2D简化分析方法")
                    
                    # Display results
                    col_r1, col_r2, col_r3 = st.columns(3)
                    with col_r1:
                        st.metric("最大位移", f"{results['max_displacement']*1000:.2f}mm")
                    with col_r2:
                        st.metric("最大弯矩", f"{results['max_moment']/1000:.2f}kN·m")
                    with col_r3:
                        st.metric("最大剪力", f"{results['max_shear']/1000:.2f}kN")
                    
                    # Support reactions
                    st.subheader("📊 支座反力 (2D分析)")
                    reactions_data = []
                    for reaction in results['reactions']:
                        reactions_data.append({
                            '墩台': f"墩台{reaction['pier_id']+1}",
                            '位置 (m)': f"{reaction['x_coord']:.1f}",
                            '水平反力 (kN)': f"{reaction['Fx']/1000:.1f}",
                            '竖向反力 (kN)': f"{reaction['Fy']/1000:.1f}",
                            '支座类型': reaction['support_type']
                        })
                    
                    reactions_df = pd.DataFrame(reactions_data)
                    st.dataframe(reactions_df, use_container_width=True)
                    
                    # Individual bearing reactions (simplified)
                    st.subheader("🎯 独立支座反力分析 (简化)")
                    for i, reaction in enumerate(results['reactions']):
                        pier_id = i + 1
                        pier_bearings = final_bridge.get_individual_bearing_info(pier_id=pier_id)
                        
                        if pier_bearings:
                            st.write(f"**墩台{pier_id}**: 总反力 {reaction['Fy']/1000:.1f}kN")
                            
                            # Simplified: assume equal distribution among bearings
                            bearing_reaction = reaction['Fy'] / len(pier_bearings)
                            
                            for bearing in pier_bearings:
                                bearing_id = bearing['bearing_id']
                                offset = bearing['height_offset'] * 1000
                                st.write(f"  - 支座{bearing_id}: {bearing_reaction/1000:.1f}kN (偏移:{offset:.1f}mm) [简化分配]")
                            
                            st.warning("⚠️ 注意：2D分析假设同一墩台的支座反力相等，不考虑高度差的影响。建议使用3D分析获得更准确的结果。")
                
                # Visualization
                st.subheader("📈 结果可视化")
                
                # Create visualization
                visualizer = BridgeVisualizer(final_bridge)
                
                # Displacement plot
                fig_disp = visualizer.plot_displacement(results['displacements'])
                st.plotly_chart(fig_disp, use_container_width=True)
                
                # Moment plot
                fig_moment = visualizer.plot_moment(results['moments'])
                st.plotly_chart(fig_moment, use_container_width=True)
                
            else:
                st.error(f"❌ 分析失败: {results.get('error', '未知错误')}")

if __name__ == "__main__":
    main()
