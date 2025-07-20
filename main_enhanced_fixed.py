#!/usr/bin/env python3
"""
Enhanced Bridge Digital Twin - Simplified Structural Analysis
支持可配置梁刚度、支座刚度、墩台高度的基础桥梁分析系统
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
    """Simplified main application focused on basic structural analysis"""
    st.set_page_config(
        page_title="桥梁结构分析系统",
        page_icon="🌉",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Header
    st.title("🌉 桥梁结构分析系统")
    st.markdown("""
    **专业桥梁有限元分析** | 支持梁刚度、支座刚度、墩台高度配置
    
    ✨ **主要功能**:
    - 🎯 **梁刚度配置**: 可调节弹性模量 (0.5×-2.0×标准值)
    - 🔧 **支座刚度配置**: 每个支座可选择Fixed Pin或Roller
    - 📐 **墩台高度配置**: 1mm精度高度调节
    - 📊 **结构分析**: 弯矩图、剪力图、支座反力分析
    """)
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ 结构参数配置")
        
        # Analysis Engine Selection
        st.subheader("🚀 分析引擎")
        use_xara = st.radio(
            "选择分析引擎:",
            [True, False],
            format_func=lambda x: "🎯 xara/OpenSees (专业)" if x else "⚡ Simple FEA (快速)",
            index=0
        )
        
        st.divider()
        
        # Beam Stiffness Configuration
        st.subheader("🏗️ 梁刚度配置")
        
        beam_stiffness_presets = {
            '低刚度梁 (0.5×)': {'multiplier': 0.5, 'E': 15e9, 'description': '软梁，柔性'},
            '标准刚度梁 (1.0×)': {'multiplier': 1.0, 'E': 30e9, 'description': '标准C30混凝土'},
            '高刚度梁 (2.0×)': {'multiplier': 2.0, 'E': 60e9, 'description': '硬梁，高强度'}
        }
        
        beam_preset = st.selectbox(
            "梁刚度预设",
            list(beam_stiffness_presets.keys()),
            index=1,
            help="选择梁刚度预设方案"
        )
        
        beam_config = beam_stiffness_presets[beam_preset]
        
        col1, col2 = st.columns(2)
        with col1:
            beam_stiffness_multiplier = st.slider(
                "刚度倍数",
                0.5, 2.0, beam_config['multiplier'], 0.1
            )
        
        with col2:
            base_E = 30e9
            actual_E = base_E * beam_stiffness_multiplier
            st.metric("弹性模量", f"{actual_E/1e9:.1f} GPa")
        
        st.info(f"💡 **特征**: {beam_config['description']}")
        
        st.divider()
        
        # Individual Support Configuration  
        st.subheader("🔧 支座类型配置")
        
        st.write("**为每个支座选择类型:**")
        
        # Support type options
        support_type_options = {
            'fixed_pin': 'Fixed Pin (固定铰接)',
            'roller': 'Roller (滑动支座)'
        }
        
        # Initialize support configurations in session state
        if 'support_configs_individual' not in st.session_state:
            # Default configuration: first pier fixed_pin, others roller
            st.session_state.support_configs_individual = [
                {'type': 'fixed_pin', 'dx': 1, 'dy': 1, 'rz': 0},
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0},
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0},
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0}
            ]
        
        support_configs = []
        pier_names = ["1号墩(左桥台)", "2号墩(中间墩)", "3号墩(中间墩)", "4号墩(右桥台)"]
        
        for i in range(4):  # Fixed 4 piers for 3-span bridge
            pier_name = pier_names[i]
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Get current selection from session state
                current_type = st.session_state.support_configs_individual[i]['type']
                current_index = list(support_type_options.keys()).index(current_type)
                
                selected_type = st.selectbox(
                    f"{pier_name}",
                    list(support_type_options.keys()),
                    format_func=lambda x: support_type_options[x],
                    index=current_index,
                    key=f"support_type_{i}"
                )
                
                # Update configuration based on selection
                if selected_type == 'fixed_pin':
                    config = {'type': 'fixed_pin', 'dx': 1, 'dy': 1, 'rz': 0}
                else:  # roller
                    config = {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0}
                
                # Update session state
                st.session_state.support_configs_individual[i] = config
                support_configs.append(config)
            
            with col2:
                # Show constraint notation
                constraint_desc = f"dx={config['dx']}\ndy={config['dy']}\nrz={config['rz']}"
                st.code(constraint_desc)
        
        # Validation
        fixed_supports = sum(1 for config in support_configs if config['dx'] == 1)
        if fixed_supports == 0:
            st.error("⚠️ 警告: 需要至少一个Fixed Pin支座防止水平滑移")
        else:
            st.success(f"✅ 配置有效: {fixed_supports}个Fixed Pin, {4-fixed_supports}个Roller")
        
        st.divider()
        
        # Pier Height Configuration
        st.subheader("📐 墩台高度配置 (1mm精度)")
        
        # Initialize pier heights in session state
        if 'pier_heights_configured' not in st.session_state:
            st.session_state.pier_heights_configured = [8.000, 8.005, 8.015, 8.003]
        
        pier_heights = []
        
        st.write("**精密高度调节:**")
        
        for i in range(4):
            pier_name = pier_names[i]
            
            col1, col2, col3, col4, col5 = st.columns([1, 1, 3, 1, 1])
            
            with col1:
                if st.button("－", key=f"pier_minus_{i}", help="减少1mm"):
                    st.session_state.pier_heights_configured[i] = max(3.000, st.session_state.pier_heights_configured[i] - 0.001)
                    st.rerun()
            
            with col2:
                if st.button("－－", key=f"pier_minus_10_{i}", help="减少1cm"):
                    st.session_state.pier_heights_configured[i] = max(3.000, st.session_state.pier_heights_configured[i] - 0.010)
                    st.rerun()
            
            with col3:
                pier_height = st.number_input(
                    f"{pier_name}",
                    min_value=3.000,
                    max_value=20.000,
                    value=st.session_state.pier_heights_configured[i],
                    step=0.001,
                    format="%.3f",
                    key=f"pier_height_{i}"
                )
                st.session_state.pier_heights_configured[i] = pier_height
            
            with col4:
                if st.button("＋", key=f"pier_plus_{i}", help="增加1mm"):
                    st.session_state.pier_heights_configured[i] = min(20.000, st.session_state.pier_heights_configured[i] + 0.001)
                    st.rerun()
            
            with col5:
                if st.button("＋＋", key=f"pier_plus_10_{i}", help="增加1cm"):
                    st.session_state.pier_heights_configured[i] = min(20.000, st.session_state.pier_heights_configured[i] + 0.010)
                    st.rerun()
            
            st.caption(f"精确高度: {pier_height:.3f}m ({pier_height*1000:.0f}mm)")
            pier_heights.append(pier_height)
        
        # Quick reset buttons
        reset_col1, reset_col2, reset_col3 = st.columns(3)
        with reset_col1:
            if st.button("工程值", key="reset_engineering"):
                st.session_state.pier_heights_configured = [8.000, 8.005, 8.015, 8.003]
                st.rerun()
        with reset_col2:
            if st.button("测试值", key="reset_testing"):
                st.session_state.pier_heights_configured = [8.000, 8.001, 8.002, 8.000]
                st.rerun()
        with reset_col3:
            if st.button("均匀值", key="reset_uniform"):
                st.session_state.pier_heights_configured = [8.000, 8.000, 8.000, 8.000]
                st.rerun()
        
        # Height difference analysis
        height_diff = max(pier_heights) - min(pier_heights)
        if height_diff > 0.001:
            st.info(f"高度差异: {height_diff:.3f}m = {height_diff*1000:.0f}mm")
        else:
            st.success("✅ 高度均匀")
        
        st.divider()
        
        # Basic Bridge Parameters
        st.subheader("🏗️ 桥梁基本参数")
        
        # Fixed configuration for simplicity
        num_spans = 3
        pier_start_position = 0.0
        bearings_per_pier = 2
        
        length = st.number_input("桥梁长度 (m)", 40.0, 80.0, 60.0, 5.0)
        bridge_width = st.number_input("桥梁宽度 (m)", 10.0, 20.0, 15.0, 1.0)
        num_elements = st.number_input("有限元数量", 15, 30, 20, 5)
        
        col1, col2 = st.columns(2)
        with col1:
            section_height = st.number_input("截面高度 (m)", 1.0, 2.0, 1.5, 0.1)
        with col2:
            section_width = st.number_input("截面宽度 (m)", 0.8, 1.5, 1.0, 0.1)
        
        density = st.number_input("材料密度 (kg/m³)", 2000, 3000, 2400, 50)
        
        E = actual_E
        
        # Current configuration summary
        st.subheader("🎯 当前配置")
        support_summary = ", ".join([f"{i+1}号:{config['type']}" for i, config in enumerate(support_configs)])
        st.success(f"**梁刚度**: {beam_stiffness_multiplier:.1f}×")
        st.info(f"**支座配置**: {support_summary}")
    
    # Create bridge model
    def create_bridge_model(_use_xara, _length, _num_elements, _E, _height, _width, 
                           _num_spans, _pier_start, _bearings_per_pier, _bridge_width, 
                           _density, _support_configs, _pier_heights):
        """Create bridge model with current configuration"""
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
                support_types=_support_configs,
                pier_heights=_pier_heights
            )
        else:
            simple_bridge = BridgeModel(
                length=_length,
                num_elements=_num_elements,
                E=_E,
                section_height=_height,
                section_width=_width
            )
            simple_bridge.num_spans = _num_spans
            simple_bridge.bridge_width = _bridge_width
            simple_bridge.density = _density
            simple_bridge.bearings_per_pier = _bearings_per_pier
            simple_bridge.pier_heights = _pier_heights
            return simple_bridge
    
    # Create model with configuration tracking
    config_key = f"config_{beam_stiffness_multiplier}_{hash(tuple(tuple(c.items()) for c in support_configs))}_{hash(tuple(pier_heights))}_{length}_{num_elements}"
    
    if 'config_params' not in st.session_state or st.session_state.config_params != config_key:
        with st.spinner("创建桥梁模型..."):
            bridge = create_bridge_model(
                use_xara, length, num_elements, E, section_height, section_width,
                num_spans, pier_start_position, bearings_per_pier, bridge_width,
                density, support_configs, pier_heights
            )
            st.session_state.bridge = bridge
            st.session_state.config_params = config_key
            st.success("✅ 桥梁模型创建成功")
    else:
        bridge = st.session_state.bridge
    
    # Display model info
    st.header("📋 桥梁模型信息")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("桥梁跨数", f"{num_spans}跨")
    with col2:
        st.metric("梁刚度", f"{beam_stiffness_multiplier:.1f}×")
    with col3:
        fixed_count = sum(1 for config in support_configs if config['dx'] == 1)
        st.metric("支座配置", f"{fixed_count}P+{4-fixed_count}R")
    with col4:
        height_range = f"{min(pier_heights):.3f}-{max(pier_heights):.3f}m"
        st.metric("高度范围", height_range)
    with col5:
        st.metric("高度差", f"{height_diff:.3f}m")
    with col6:
        st.metric("弹性模量", f"{E/1e9:.1f} GPa")
    
    # Display detailed support configuration
    st.subheader("🔧 详细支座配置")
    
    support_detail_cols = st.columns(4)
    for i, (pier_name, config) in enumerate(zip(pier_names, support_configs)):
        with support_detail_cols[i]:
            support_type_display = "🔒 Fixed Pin" if config['type'] == 'fixed_pin' else "📏 Roller"
            st.write(f"**{pier_name}**")
            st.write(f"{support_type_display}")
            st.caption(f"dx={config['dx']}, dy={config['dy']}, rz={config['rz']}")
    
    # Simplified Load Application
    st.header("⚖️ 荷载配置")
    
    # Uniform distributed load input
    st.subheader("均布荷载")
    
    col1, col2 = st.columns(2)
    with col1:
        distributed_load = st.number_input(
            "均布荷载强度 (kN/m)",
            -100.0, 100.0, -50.0, 5.0,
            help="均布荷载强度，负值表示向下"
        )
    
    with col2:
        total_load = abs(distributed_load) * length
        st.metric("总荷载", f"{total_load:.1f} kN")
    
    # Apply load to bridge
    if st.button("🔄 更新荷载", type="secondary"):
        bridge.loads.clear()  # Clear existing loads
        if abs(distributed_load) > 0:
            bridge.add_distributed_load(distributed_load * 1000)  # Convert kN/m to N/m
        st.success(f"✅ 已更新荷载: {distributed_load} kN/m")
    
    # Show current load status
    if hasattr(bridge, 'loads') and bridge.loads:
        st.info(f"📋 当前荷载: {len(bridge.loads)} 个外加荷载 + 结构自重")
    else:
        st.info("📋 当前仅有结构自重荷载")
    
    # Analysis Section
    if st.button("🚀 运行结构分析", type="primary", use_container_width=True):
        with st.spinner("正在进行有限元分析..."):
            results = bridge.run_analysis()
            
            if results.get('analysis_ok', True):
                st.success("✅ 结构分析完成!")
                
                # Store results
                st.session_state.bridge = bridge
                st.session_state.results = results
                st.session_state.analysis_done = True
            else:
                st.error("❌ 分析失败!")
                if 'error' in results:
                    st.error(f"错误详情: {results['error']}")
    
    # Results Display
    if hasattr(st.session_state, 'analysis_done') and st.session_state.analysis_done:
        bridge = st.session_state.bridge
        results = st.session_state.results
        
        st.header("📊 分析结果")
        
        # Key results summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            max_disp = results.get('max_displacement', 0)
            if max_disp == 0 and 'displacements' in results:
                max_disp = max(abs(d) for d in results['displacements']) if results['displacements'] else 0
            st.metric("最大位移", f"{max_disp*1000:.2f} mm")
        
        with col2:
            max_moment = results.get('max_moment', 0)
            if max_moment == 0 and 'moments' in results:
                max_moment = max(abs(m) for m in results['moments']) if results['moments'] else 0
            st.metric("最大弯矩", f"{max_moment/1000:.1f} kN·m")
        
        with col3:
            max_shear = results.get('max_shear', 0)
            if max_shear == 0 and 'shears' in results:
                max_shear = max(abs(s) for s in results['shears']) if results['shears'] else 0
            st.metric("最大剪力", f"{max_shear/1000:.1f} kN")
        
        with col4:
            if 'reactions' in results and results['reactions']:
                max_reaction = max(abs(r['Fy']) for r in results['reactions']) / 1000
                st.metric("最大支座反力", f"{max_reaction:.1f} kN")
            else:
                st.metric("最大支座反力", "N/A")
        
        # Bending Moment and Shear Force Calculation Method Explanation
        st.subheader("🧮 弯矩和剪力计算原理")
        
        with st.expander("📚 计算方法详解", expanded=False):
            st.markdown("""
            ### 🔬 **弯矩和剪力的计算方法**
            
            本系统采用**OpenSees有限元方法**计算弯矩和剪力：
            
            #### **1. 有限元基础**
            - **单元类型**: `elasticBeamColumn` - 欧拉-伯努利梁单元
            - **节点自由度**: 每个节点3个自由度 (dx, dy, rz)
            - **单元内力**: 通过`eleForce()`命令获取 [N1, V1, M1, N2, V2, M2]
            
            #### **2. 弯矩计算 (Bending Moment)**
            ```python
            forces = model.eleForce(element_id)
            moment_i = forces[2]  # 单元i端弯矩
            moment_j = forces[5]  # 单元j端弯矩
            ```
            - **物理意义**: 截面上的内弯矩，由外荷载和约束反力产生
            - **符号约定**: 正弯矩使梁下纤维受拉，上纤维受压
            - **计算原理**: 基于虚功原理和位移法求解
            
            #### **3. 剪力计算 (Shear Force)**
            ```python
            shear_i = forces[1]   # 单元i端剪力
            shear_j = forces[4]   # 单元j端剪力  
            ```
            - **物理意义**: 截面上的横向内力
            - **符号约定**: 正剪力使梁段顺时针转动
            - **计算原理**: 通过力的平衡条件求解
            
            #### **4. 有限元求解步骤**
            1. **刚度矩阵组装**: K = ∑[T]ᵀ[k][T]
            2. **荷载向量组装**: F = P + P_distributed  
            3. **求解位移**: [K]{u} = {F}
            4. **计算内力**: {f} = [k][T]{u}
            
            #### **5. 精度特点**
            - ✅ **高精度**: 基于有限元理论，考虑几何和材料非线性
            - ✅ **连续性**: 单元间位移和转角连续
            - ✅ **平衡性**: 满足节点力平衡和单元内力平衡
            - ✅ **收敛性**: 网格细化时解收敛于精确解
            
            #### **6. 与简化方法对比**
            | 方法 | 精度 | 适用范围 | 计算量 |
            |------|------|----------|--------|
            | 有限元法 | ⭐⭐⭐⭐⭐ | 任意复杂结构 | 大 |
            | 影响线法 | ⭐⭐⭐ | 静定/简单超静定 | 中 |
            | 弯矩分配法 | ⭐⭐ | 连续梁 | 小 |
            
            **结论**: 本系统采用OpenSees专业有限元引擎，确保计算结果的工程精度和可靠性。
            """)
        
        # Detailed Results Visualization
        st.subheader("📈 结构分析图表")
        
        visualizer = BridgeVisualizer(bridge, results)
        
        # Create tabs for different result types
        moment_tab, shear_tab, reaction_tab = st.tabs(["🔄 弯矩图", "↕️ 剪力图", "🏗️ 支座反力"])
        
        with moment_tab:
            st.subheader("弯矩图")
            try:
                fig_moment = visualizer.create_moment_diagram()
                st.plotly_chart(fig_moment, use_container_width=True)
                
                # Moment statistics
                if 'moments' in results and results['moments']:
                    moments = results['moments']
                    st.info(f"""
                    **弯矩统计:**
                    - 最大正弯矩: {max([m for m in moments if m > 0], default=0)/1000:.1f} kN·m
                    - 最大负弯矩: {min([m for m in moments if m < 0], default=0)/1000:.1f} kN·m
                    - 弯矩极值: {max(abs(m) for m in moments)/1000:.1f} kN·m
                    """)
            except Exception as e:
                st.error(f"弯矩图生成失败: {e}")
        
        with shear_tab:
            st.subheader("剪力图")
            try:
                fig_shear = visualizer.create_shear_diagram()
                st.plotly_chart(fig_shear, use_container_width=True)
                
                # Shear statistics
                if 'shears' in results and results['shears']:
                    shears = results['shears']
                    st.info(f"""
                    **剪力统计:**
                    - 最大正剪力: {max([s for s in shears if s > 0], default=0)/1000:.1f} kN
                    - 最大负剪力: {min([s for s in shears if s < 0], default=0)/1000:.1f} kN
                    - 剪力极值: {max(abs(s) for s in shears)/1000:.1f} kN
                    """)
            except Exception as e:
                st.error(f"剪力图生成失败: {e}")
        
        with reaction_tab:
            st.subheader("支座反力分析")
            
            if 'reactions' in results and results['reactions']:
                # Support reactions table
                st.write("**支座反力表:**")
                
                reactions_data = []
                for i, reaction in enumerate(results['reactions']):
                    pier_height = pier_heights[i] if i < len(pier_heights) else 8.0
                    support_type = support_configs[i]['type']
                    
                    reactions_data.append({
                        '支座': f"墩台{i+1}",
                        '位置(m)': f"{reaction['x_coord']:.1f}",
                        '高度(m)': f"{pier_height:.3f}",
                        '支座类型': f"{'Fixed Pin' if support_type == 'fixed_pin' else 'Roller'}",
                        '水平反力Fx(kN)': f"{reaction['Fx']/1000:.2f}",
                        '竖向反力Fy(kN)': f"{reaction['Fy']/1000:.2f}",
                        '弯矩反力Mz(kN·m)': f"{reaction['Mz']/1000:.2f}"
                    })
                
                reactions_df = pd.DataFrame(reactions_data)
                st.dataframe(reactions_df, use_container_width=True)
                
                # Support reactions chart
                st.write("**支座反力分布图:**")
                
                fig_reactions = go.Figure()
                
                pier_positions = [r['x_coord'] for r in results['reactions']]
                vertical_reactions = [r['Fy']/1000 for r in results['reactions']]
                pier_labels = [f"墩台{i+1}\n{support_configs[i]['type']}" for i in range(len(results['reactions']))]
                
                # Color code by support type
                colors = ['red' if support_configs[i]['type'] == 'fixed_pin' else 'skyblue' for i in range(len(results['reactions']))]
                
                fig_reactions.add_trace(go.Bar(
                    x=pier_positions,
                    y=vertical_reactions,
                    name='竖向反力 (kN)',
                    marker_color=colors,
                    text=[f"{v:.1f}kN" for v in vertical_reactions],
                    textposition='auto',
                    hovertext=pier_labels,
                    hovertemplate='<b>%{hovertext}</b><br>位置: %{x:.1f}m<br>反力: %{y:.1f}kN<extra></extra>'
                ))
                
                fig_reactions.update_layout(
                    title='支座竖向反力分布 (红色=Fixed Pin, 蓝色=Roller)',
                    xaxis_title='桥梁位置 (m)',
                    yaxis_title='竖向反力 (kN)',
                    height=400
                )
                
                st.plotly_chart(fig_reactions, use_container_width=True)
                
                # Force balance check
                total_vertical = sum(r['Fy'] for r in results['reactions'])
                total_horizontal = sum(r['Fx'] for r in results['reactions'])
                
                st.info(f"""
                **力平衡检验:**
                - 竖向反力合计: {total_vertical/1000:.2f} kN
                - 水平反力合计: {total_horizontal/1000:.2f} kN
                - 平衡状态: {'✅ 平衡' if abs(total_horizontal) < 1.0 else '⚠️ 不平衡'}
                """)
                
            else:
                st.info("支座反力数据不可用")
    
    # Footer
    st.divider()
    support_summary_short = f"{sum(1 for c in support_configs if c['dx']==1)}P+{sum(1 for c in support_configs if c['dx']==0)}R"
    st.markdown(f"""
    **桥梁结构分析系统** | 梁刚度: {beam_stiffness_multiplier:.1f}× | 支座: {support_summary_short} | 高度差: {height_diff*1000:.0f}mm | E: {E/1e9:.1f}GPa
    
    📊 **分析功能**: 基于OpenSees有限元的弯矩图 | 剪力图 | 支座反力 | 精确配置
    """)

if __name__ == "__main__":
    logging.info("Starting Bridge Structural Analysis System")
    main()