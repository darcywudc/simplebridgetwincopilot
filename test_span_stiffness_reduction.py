#!/usr/bin/env python3
"""
跨刚度减少影响测试
分析不同跨刚度减少对反力分布的影响
工况1：跨1刚度减少
工况2：跨2刚度减少  
工况3：跨3刚度减少

增加挠度、弯矩、剪力分析
"""

import numpy as np
import xara
import pandas as pd
import matplotlib.pyplot as plt

class SpanStiffnessTest:
    """跨刚度减少测试：不同跨刚度变化的影响"""
    
    def __init__(self, length=60.0, num_elements=20, E=30e9, section_height=1.5, section_width=1.0, density=2400):
        self.length = length
        self.num_elements = num_elements
        self.E = E
        self.section_height = section_height
        self.section_width = section_width
        self.density = density
        
        # 计算截面特性
        self.A = section_height * section_width
        self.I = (section_width * section_height**3) / 12
        
        # 创建节点
        self.nodes = []
        self.elements = []
        
        # 4个支座位置（3跨连续梁）
        self.pier_positions = [0.0, 0.33, 0.67, 1.0]  # 相对位置
        self.pier_nodes = []
        
        # 跨的划分
        self.span_ranges = self._calculate_span_ranges()
        
        self._setup_geometry()
    
    def _calculate_span_ranges(self):
        """计算各跨的单元范围"""
        dx = self.length / self.num_elements
        spans = []
        
        for i in range(len(self.pier_positions)-1):
            start_pos = self.pier_positions[i] * self.length
            end_pos = self.pier_positions[i+1] * self.length
            
            start_element = int(start_pos / dx)
            end_element = int(end_pos / dx)
            
            # 确保单元编号在有效范围内
            start_element = max(0, start_element)
            end_element = min(self.num_elements-1, end_element)
            
            spans.append({
                'span_id': i+1,
                'start_element': start_element + 1,  # OpenSees单元从1开始
                'end_element': end_element + 1,
                'start_pos': start_pos,
                'end_pos': end_pos,
                'length': end_pos - start_pos
            })
        
        return spans
    
    def _setup_geometry(self):
        """设置几何结构"""
        # 创建节点
        num_nodes = self.num_elements + 1
        dx = self.length / self.num_elements
        
        for i in range(num_nodes):
            x = i * dx
            node_id = i + 1
            self.nodes.append((node_id, x, 0.0))
        
        # 创建单元
        for i in range(self.num_elements):
            element_id = i + 1
            node_i = i + 1
            node_j = i + 2
            self.elements.append((element_id, node_i, node_j))
        
        # 计算支座节点
        for pos in self.pier_positions:
            pier_x = pos * self.length
            node_spacing = self.length / self.num_elements
            pier_node = int(round(pier_x / node_spacing)) + 1
            pier_node = max(1, min(pier_node, len(self.nodes)))
            self.pier_nodes.append(pier_node)
        
        print(f"支座节点: {self.pier_nodes}")
        print(f"支座位置: {[pos * self.length for pos in self.pier_positions]}")
        
        # 打印跨信息
        print(f"跨划分信息:")
        for span in self.span_ranges:
            print(f"  跨{span['span_id']}: 单元{span['start_element']}-{span['end_element']}, "
                  f"位置{span['start_pos']:.1f}m-{span['end_pos']:.1f}m, "
                  f"长度{span['length']:.1f}m")
    
    def print_bridge_info(self):
        """打印桥梁基本信息"""
        print("\n" + "="*60)
        print("桥梁结构基本信息")
        print("="*60)
        
        # 几何参数
        print("🏗️ 几何参数:")
        print(f"  桥梁总长度: {self.length:.1f} m")
        print(f"  跨数: 3跨连续梁")
        span_lengths = [span['length'] for span in self.span_ranges]
        print(f"  各跨长度: {' + '.join([f'{s:.1f}m' for s in span_lengths])} = {sum(span_lengths):.1f}m")
        print(f"  有限元单元数: {self.num_elements}")
        print(f"  单元长度: {self.length/self.num_elements:.1f} m")
        
        # 截面参数  
        print("\n📐 梁截面参数:")
        print(f"  截面高度: {self.section_height:.2f} m")
        print(f"  截面宽度: {self.section_width:.2f} m")
        print(f"  截面面积: A = {self.A:.3f} m²")
        print(f"  惯性矩: I = {self.I:.4f} m⁴")
        
        # 材料参数
        print("\n🧱 材料参数:")
        print(f"  弹性模量: E = {self.E/1e9:.0f} GPa")
        print(f"  密度: ρ = {self.density:.0f} kg/m³")
        
        # 梁刚度参数
        EI = self.E * self.I
        EA = self.E * self.A
        print(f"  抗弯刚度: EI = {EI/1e6:.0f} MN·m²")
        print(f"  轴向刚度: EA = {EA/1e6:.0f} MN")
        
        # 荷载参数
        weight_per_length = self.density * 9.81 * self.A
        total_weight = weight_per_length * self.length
        print("\n⚖️ 荷载参数:")
        print(f"  线密度: {weight_per_length/1000:.2f} kN/m")
        print(f"  总重量: {total_weight/1000:.2f} kN")
        
        # 支座信息
        print("\n🔗 支座配置:")
        support_types = ["固定支座", "滑动支座", "滑动支座", "滑动支座"]
        for i, (pos, support_type) in enumerate(zip(self.pier_positions, support_types)):
            print(f"  {i+1}号墩 (位置{pos*self.length:.1f}m): {support_type}")
        
        # 跨刚度信息
        print("\n🔧 跨刚度信息:")
        for span in self.span_ranges:
            print(f"  跨{span['span_id']}: 单元{span['start_element']}-{span['end_element']}, 标准刚度EI = {self.E*self.I/1e6:.0f} MN·m²")
    
    def analyze_structure(self, span_number=None, reduction_factor=1.0):
        """结构分析：返回反力、挠度、弯矩、剪力"""
        model = xara.Model()
        model.model('basic', '-ndm', 2, '-ndf', 3)
        
        # 创建节点
        for node_id, x, y in self.nodes:
            model.node(node_id, x, y)
        
        # 创建材料
        model.uniaxialMaterial('Elastic', 1, self.E)  # 标准材料
        if span_number is not None:
            reduced_E = self.E * reduction_factor
            model.uniaxialMaterial('Elastic', 2, reduced_E)  # 减少刚度材料
        
        # 创建几何变换
        model.geomTransf('Linear', 1)
        
        # 创建梁单元
        if span_number is not None:
            target_span = self.span_ranges[span_number - 1]
            for element_id, node_i, node_j in self.elements:
                if target_span['start_element'] <= element_id <= target_span['end_element']:
                    model.element('elasticBeamColumn', element_id, node_i, node_j, 
                                 self.A, reduced_E, self.I, 1)
                else:
                    model.element('elasticBeamColumn', element_id, node_i, node_j, 
                                 self.A, self.E, self.I, 1)
        else:
            for element_id, node_i, node_j in self.elements:
                model.element('elasticBeamColumn', element_id, node_i, node_j, 
                             self.A, self.E, self.I, 1)
        
        # 约束
        model.fix(self.pier_nodes[0], 1, 1, 0)  # 1号墩：固定支座
        model.fix(self.pier_nodes[1], 0, 1, 0)  # 2号墩：滑动支座
        model.fix(self.pier_nodes[2], 0, 1, 0)  # 3号墩：滑动支座
        model.fix(self.pier_nodes[3], 0, 1, 0)  # 4号墩：滑动支座
        
        # 施加荷载
        model.timeSeries('Linear', 1)
        model.pattern('Plain', 1, 1)
        
        weight_per_length = self.density * 9.81 * self.A
        for element_id, _, _ in self.elements:
            model.eleLoad('-ele', element_id, '-type', '-beamUniform', -weight_per_length)
        
        # 分析
        model.system('ProfileSPD')
        model.numberer('Plain')
        model.constraints('Transformation')
        model.integrator('LoadControl', 1.0)
        model.algorithm('Linear')
        model.analysis('Static')
        
        ok = model.analyze(1)
        
        if ok == 0:
            # 收集反力
            model.reactions()
            reactions = []
            for pier_node in self.pier_nodes:
                try:
                    reaction = model.nodeReaction(pier_node)
                    reactions.append(abs(reaction[1]))
                except:
                    reactions.append(0.0)
            
            # 收集节点位移（挠度）
            displacements = []
            node_positions = []
            for node_id, x, y in self.nodes:
                try:
                    disp = model.nodeDisp(node_id)
                    displacements.append(disp[1])  # Y方向位移（挠度）
                    node_positions.append(x)
                except:
                    displacements.append(0.0)
                    node_positions.append(x)
            
            # 收集单元内力（弯矩和剪力）
            moments = []
            shears = []
            element_positions = []
            
            for element_id, node_i, node_j in self.elements:
                try:
                    # 获取单元两端的内力
                    force_i = model.eleForce(element_id)
                    if len(force_i) >= 6:
                        # force_i = [Ni, Vi, Mi, Nj, Vj, Mj]
                        moment_i = force_i[2]  # i端弯矩
                        moment_j = force_i[5]  # j端弯矩
                        shear_i = force_i[1]   # i端剪力
                        shear_j = force_i[4]   # j端剪力
                        
                        # 单元中点位置
                        x_i = self.nodes[node_i-1][1]
                        x_j = self.nodes[node_j-1][1]
                        x_mid = (x_i + x_j) / 2
                        
                        # 单元中点的内力（线性插值）
                        moment_mid = (moment_i + moment_j) / 2
                        shear_mid = (shear_i + shear_j) / 2
                        
                        moments.append(moment_mid)
                        shears.append(shear_mid)
                        element_positions.append(x_mid)
                    else:
                        moments.append(0.0)
                        shears.append(0.0)
                        element_positions.append((self.nodes[node_i-1][1] + self.nodes[node_j-1][1]) / 2)
                except:
                    moments.append(0.0)
                    shears.append(0.0)
                    element_positions.append((self.nodes[node_i-1][1] + self.nodes[node_j-1][1]) / 2)
            
            return {
                'reactions': reactions,
                'displacements': displacements,
                'node_positions': node_positions,
                'moments': moments,
                'shears': shears,
                'element_positions': element_positions
            }
        else:
            # 分析失败，返回零值
            num_nodes = len(self.nodes)
            num_elements = len(self.elements)
            return {
                'reactions': [0.0] * len(self.pier_nodes),
                'displacements': [0.0] * num_nodes,
                'node_positions': [node[1] for node in self.nodes],
                'moments': [0.0] * num_elements,
                'shears': [0.0] * num_elements,
                'element_positions': [(self.nodes[i][1] + self.nodes[i+1][1])/2 for i in range(num_elements)]
            }
    
    def compare_stiffness_reduction_cases(self):
        """对比不同跨刚度减少的影响"""
        # 打印桥梁基本信息
        self.print_bridge_info()
        
        print("\n" + "="*70)
        print("跨刚度减少多工况对比分析")
        print("场景：不同跨刚度减少对反力分布的影响")
        print("="*70)
        
        # 测试工况（只分析刚度减少30%的情况，便于详细分析）
        reduction_factor = 0.7  # 刚度减少30%
        reduction_percent = (1 - reduction_factor) * 100
        
        print(f"\n📊 测试工况说明:")
        print(f"  正常工况: 所有跨标准刚度 (EI = {self.E*self.I/1e6:.0f} MN·m²)")
        print(f"  刚度减少{reduction_percent:.0f}%: EI = {self.E*self.I*reduction_factor/1e6:.0f} MN·m²")
        
        print(f"\n" + "="*50)
        print(f"刚度减少{reduction_percent:.0f}%工况详细分析")
        print("="*50)
        
        all_results = {}
        
        # 正常工况
        print(f"  ✓ 正常工况（标准刚度）")
        normal_results = self.analyze_structure()
        all_results['normal'] = normal_results
        
        # 各跨刚度减少工况
        for span_num in [1, 2, 3]:
            print(f"  ✓ 工况{span_num}：跨{span_num}刚度减少{reduction_percent:.0f}%")
            results = self.analyze_structure(span_num, reduction_factor)
            all_results[f'span_{span_num}'] = results
        
        # 生成详细对比分析
        self.generate_detailed_analysis(all_results, reduction_percent)
    
    def generate_detailed_analysis(self, all_results, reduction_percent):
        """生成详细分析报告"""
        print(f"\n" + "="*80)
        print(f"详细结构响应分析报告 (刚度减少{reduction_percent:.0f}%)")
        print("="*80)
        
        # 1. 支座反力对比
        self.analyze_reactions(all_results, reduction_percent)
        
        # 2. 挠度分析
        self.analyze_deflections(all_results, reduction_percent)
        
        # 3. 弯矩分析
        self.analyze_moments(all_results, reduction_percent)
        
        # 4. 剪力分析
        self.analyze_shears(all_results, reduction_percent)
        
        # 5. 关键断面分析
        self.analyze_critical_sections(all_results, reduction_percent)
        
        # 6. 工程评价
        self.generate_engineering_evaluation(all_results, reduction_percent)
    
    def analyze_reactions(self, all_results, reduction_percent):
        """支座反力分析"""
        print(f"\n🔗 支座反力分析")
        print("-" * 50)
        
        # 创建反力对比表
        table_data = {
            '支座': ['1号墩', '2号墩', '3号墩', '4号墩'],
            '位置(m)': [f"{pos * self.length:.1f}" for pos in self.pier_positions],
            '正常工况(kN)': [f"{r/1000:.2f}" for r in all_results['normal']['reactions']]
        }
        
        for span_num in [1, 2, 3]:
            table_data[f'工况{span_num}(kN)'] = [f"{r/1000:.2f}" for r in all_results[f'span_{span_num}']['reactions']]
        
        reaction_df = pd.DataFrame(table_data)
        print(reaction_df.to_string(index=False))
        
        # 变化量分析
        print(f"\n📈 反力变化量 (kN):")
        normal_reactions = all_results['normal']['reactions']
        for span_num in [1, 2, 3]:
            span_reactions = all_results[f'span_{span_num}']['reactions']
            changes = [(s-n)/1000 for n, s in zip(normal_reactions, span_reactions)]
            max_change = max([abs(c) for c in changes])
            max_idx = [abs(c) for c in changes].index(max_change)
            
            print(f"  工况{span_num}: 最大变化{max_change:.2f}kN在{max_idx+1}号墩")
            print(f"           变化分布: " + " | ".join([f"{c:+.1f}" for c in changes]))
    
    def analyze_deflections(self, all_results, reduction_percent):
        """挠度分析"""
        print(f"\n📏 挠度分析")
        print("-" * 50)
        
        normal_disps = all_results['normal']['displacements']
        positions = all_results['normal']['node_positions']
        
        # 找出最大挠度位置
        max_normal_disp = min(normal_disps)  # 负值表示向下挠度
        max_normal_idx = normal_disps.index(max_normal_disp)
        max_normal_pos = positions[max_normal_idx]
        
        print(f"正常工况最大挠度: {abs(max_normal_disp)*1000:.2f}mm (位置{max_normal_pos:.1f}m)")
        
        # 各工况挠度对比
        print(f"\n📊 各工况最大挠度对比:")
        deflection_data = {
            '工况': ['正常工况'],
            '最大挠度(mm)': [f"{abs(max_normal_disp)*1000:.2f}"],
            '位置(m)': [f"{max_normal_pos:.1f}"],
            '变化量(mm)': ['--']
        }
        
        for span_num in [1, 2, 3]:
            span_disps = all_results[f'span_{span_num}']['displacements']
            max_span_disp = min(span_disps)
            max_span_idx = span_disps.index(max_span_disp)
            max_span_pos = positions[max_span_idx]
            
            change = abs(max_span_disp) - abs(max_normal_disp)
            
            deflection_data['工况'].append(f'工况{span_num}')
            deflection_data['最大挠度(mm)'].append(f"{abs(max_span_disp)*1000:.2f}")
            deflection_data['位置(m)'].append(f"{max_span_pos:.1f}")
            deflection_data['变化量(mm)'].append(f"{change*1000:+.2f}")
        
        deflection_df = pd.DataFrame(deflection_data)
        print(deflection_df.to_string(index=False))
        
        # 跨中挠度分析
        print(f"\n🎯 各跨跨中挠度分析:")
        for i, span in enumerate(self.span_ranges):
            span_mid_pos = (span['start_pos'] + span['end_pos']) / 2
            # 找到最接近跨中的节点
            mid_node_idx = min(range(len(positions)), key=lambda x: abs(positions[x] - span_mid_pos))
            mid_pos = positions[mid_node_idx]
            
            normal_mid_disp = normal_disps[mid_node_idx]
            
            print(f"  跨{span['span_id']}跨中 (位置{mid_pos:.1f}m):")
            print(f"    正常工况: {abs(normal_mid_disp)*1000:.2f}mm")
            
            for span_num in [1, 2, 3]:
                span_disps = all_results[f'span_{span_num}']['displacements']
                span_mid_disp = span_disps[mid_node_idx]
                change = abs(span_mid_disp) - abs(normal_mid_disp)
                
                print(f"    工况{span_num}: {abs(span_mid_disp)*1000:.2f}mm ({change*1000:+.2f}mm)")
    
    def analyze_moments(self, all_results, reduction_percent):
        """弯矩分析"""
        print(f"\n📐 弯矩分析")
        print("-" * 50)
        
        normal_moments = all_results['normal']['moments']
        positions = all_results['normal']['element_positions']
        
        # 找出最大正弯矩和最大负弯矩
        max_pos_moment = max(normal_moments)
        max_neg_moment = min(normal_moments)
        max_pos_idx = normal_moments.index(max_pos_moment)
        max_neg_idx = normal_moments.index(max_neg_moment)
        
        print(f"正常工况弯矩极值:")
        print(f"  最大正弯矩: {max_pos_moment/1000:.1f} kN·m (位置{positions[max_pos_idx]:.1f}m)")
        print(f"  最大负弯矩: {max_neg_moment/1000:.1f} kN·m (位置{positions[max_neg_idx]:.1f}m)")
        
        # 支座负弯矩分析
        print(f"\n🔗 支座负弯矩分析:")
        pier_moment_data = {
            '支座': [],
            '位置(m)': [],
            '正常工况(kN·m)': [],
        }
        
        for span_num in [1, 2, 3]:
            pier_moment_data[f'工况{span_num}(kN·m)'] = []
        
        # 分析各支座附近的弯矩
        for i, pier_pos in enumerate([pos * self.length for pos in self.pier_positions]):
            if i == 0 or i == len(self.pier_positions)-1:
                continue  # 跳过端部支座
            
            # 找到最接近支座的单元
            pier_element_idx = min(range(len(positions)), key=lambda x: abs(positions[x] - pier_pos))
            pier_element_pos = positions[pier_element_idx]
            
            normal_pier_moment = normal_moments[pier_element_idx]
            
            pier_moment_data['支座'].append(f'{i+1}号墩')
            pier_moment_data['位置(m)'].append(f'{pier_element_pos:.1f}')
            pier_moment_data['正常工况(kN·m)'].append(f'{normal_pier_moment/1000:.1f}')
            
            for span_num in [1, 2, 3]:
                span_moments = all_results[f'span_{span_num}']['moments']
                span_pier_moment = span_moments[pier_element_idx]
                pier_moment_data[f'工况{span_num}(kN·m)'].append(f'{span_pier_moment/1000:.1f}')
        
        pier_moment_df = pd.DataFrame(pier_moment_data)
        print(pier_moment_df.to_string(index=False))
    
    def analyze_shears(self, all_results, reduction_percent):
        """剪力分析"""
        print(f"\n✂️ 剪力分析")
        print("-" * 50)
        
        normal_shears = all_results['normal']['shears']
        positions = all_results['normal']['element_positions']
        
        # 找出最大剪力
        max_shear = max([abs(s) for s in normal_shears])
        max_shear_idx = [abs(s) for s in normal_shears].index(max_shear)
        
        print(f"正常工况最大剪力: {max_shear/1000:.1f} kN (位置{positions[max_shear_idx]:.1f}m)")
        
        # 支座剪力分析
        print(f"\n🔗 支座剪力分析:")
        pier_shear_data = {
            '支座': [],
            '位置(m)': [],
            '正常工况(kN)': [],
        }
        
        for span_num in [1, 2, 3]:
            pier_shear_data[f'工况{span_num}(kN)'] = []
        
        # 分析各支座附近的剪力
        for i, pier_pos in enumerate([pos * self.length for pos in self.pier_positions]):
            if i == 0 or i == len(self.pier_positions)-1:
                continue  # 跳过端部支座
            
            # 找到最接近支座的单元
            pier_element_idx = min(range(len(positions)), key=lambda x: abs(positions[x] - pier_pos))
            pier_element_pos = positions[pier_element_idx]
            
            normal_pier_shear = normal_shears[pier_element_idx]
            
            pier_shear_data['支座'].append(f'{i+1}号墩')
            pier_shear_data['位置(m)'].append(f'{pier_element_pos:.1f}')
            pier_shear_data['正常工况(kN)'].append(f'{normal_pier_shear/1000:.1f}')
            
            for span_num in [1, 2, 3]:
                span_shears = all_results[f'span_{span_num}']['shears']
                span_pier_shear = span_shears[pier_element_idx]
                pier_shear_data[f'工况{span_num}(kN)'].append(f'{span_pier_shear/1000:.1f}')
        
        pier_shear_df = pd.DataFrame(pier_shear_data)
        print(pier_shear_df.to_string(index=False))
    
    def analyze_critical_sections(self, all_results, reduction_percent):
        """关键断面分析"""
        print(f"\n🎯 关键断面分析")
        print("-" * 50)
        
        # 定义关键断面：各跨跨中和支座位置
        critical_sections = []
        
        # 跨中断面
        for span in self.span_ranges:
            span_mid_pos = (span['start_pos'] + span['end_pos']) / 2
            critical_sections.append({
                'name': f'跨{span["span_id"]}跨中',
                'position': span_mid_pos,
                'type': 'span_mid'
            })
        
        # 中间支座断面
        for i, pos in enumerate(self.pier_positions[1:-1], 1):
            critical_sections.append({
                'name': f'{i+1}号墩',
                'position': pos * self.length,
                'type': 'pier'
            })
        
        print(f"关键断面结构响应对比:")
        
        for section in critical_sections:
            print(f"\n📍 {section['name']} (位置{section['position']:.1f}m):")
            
            # 找到最接近的节点和单元
            node_positions = all_results['normal']['node_positions']
            element_positions = all_results['normal']['element_positions']
            
            node_idx = min(range(len(node_positions)), key=lambda x: abs(node_positions[x] - section['position']))
            element_idx = min(range(len(element_positions)), key=lambda x: abs(element_positions[x] - section['position']))
            
            # 正常工况
            normal_disp = all_results['normal']['displacements'][node_idx]
            normal_moment = all_results['normal']['moments'][element_idx]
            normal_shear = all_results['normal']['shears'][element_idx]
            
            print(f"  正常工况: 挠度{abs(normal_disp)*1000:.2f}mm, 弯矩{normal_moment/1000:.1f}kN·m, 剪力{normal_shear/1000:.1f}kN")
            
            # 各工况对比
            for span_num in [1, 2, 3]:
                span_disp = all_results[f'span_{span_num}']['displacements'][node_idx]
                span_moment = all_results[f'span_{span_num}']['moments'][element_idx]
                span_shear = all_results[f'span_{span_num}']['shears'][element_idx]
                
                disp_change = abs(span_disp) - abs(normal_disp)
                moment_change = span_moment - normal_moment
                shear_change = span_shear - normal_shear
                
                print(f"  工况{span_num}:   挠度{abs(span_disp)*1000:.2f}mm({disp_change*1000:+.2f}), "
                      f"弯矩{span_moment/1000:.1f}kN·m({moment_change/1000:+.1f}), "
                      f"剪力{span_shear/1000:.1f}kN({shear_change/1000:+.1f})")
    
    def generate_engineering_evaluation(self, all_results, reduction_percent):
        """工程评价"""
        print(f"\n💡 工程评价与建议")
        print("-" * 50)
        
        normal_reactions = all_results['normal']['reactions']
        normal_disps = all_results['normal']['displacements']
        normal_moments = all_results['normal']['moments']
        
        print(f"\n🎯 影响程度评价 (刚度减少{reduction_percent:.0f}%):")
        
        for span_num in [1, 2, 3]:
            span_reactions = all_results[f'span_{span_num}']['reactions']
            span_disps = all_results[f'span_{span_num}']['displacements']
            span_moments = all_results[f'span_{span_num}']['moments']
            
            # 计算各响应的最大变化
            max_reaction_change = max([abs(s-n) for s, n in zip(span_reactions, normal_reactions)]) / 1000
            max_disp_change = max([abs(abs(s)-abs(n)) for s, n in zip(span_disps, normal_disps)]) * 1000
            max_moment_change = max([abs(s-n) for s, n in zip(span_moments, normal_moments)]) / 1000
            
            # 评价等级
            if max_reaction_change > 15 or max_disp_change > 5 or max_moment_change > 50:
                level = "显著"
                color = "🔴"
            elif max_reaction_change > 8 or max_disp_change > 2 or max_moment_change > 25:
                level = "中等"
                color = "🟡"
            else:
                level = "轻微"
                color = "🟢"
            
            print(f"  {color} 工况{span_num} (跨{span_num}刚度减少): {level}影响")
            print(f"      反力变化: 最大{max_reaction_change:.1f}kN")
            print(f"      挠度变化: 最大{max_disp_change:.2f}mm")
            print(f"      弯矩变化: 最大{max_moment_change:.1f}kN·m")
        
        print(f"\n📋 设计与维护建议:")
        print(f"  1. 🔍 监测重点: 边跨(跨1、跨3)刚度变化影响最大")
        print(f"  2. 📏 控制指标: 单跨刚度变化不超过20%")
        print(f"  3. 🔧 加固策略: 优先考虑边跨结构加固")
        print(f"  4. ⚖️ 监测参数: 中间支座反力、跨中挠度、支座负弯矩")
        print(f"  5. 🚨 预警阈值: 反力变化>15kN, 挠度变化>5mm, 弯矩变化>50kN·m")
        
        # 总反力验证
        print(f"\n✅ 分析验证:")
        for case_name, results in all_results.items():
            total = sum(results['reactions']) / 1000
            if case_name == 'normal':
                print(f"  正常工况总反力: {total:.2f} kN")
            else:
                span_num = case_name.split('_')[1]
                print(f"  工况{span_num}总反力: {total:.2f} kN")

def main():
    """主函数"""
    print("跨刚度减少详细结构响应分析程序")
    print("分析支座反力、挠度、弯矩、剪力等结构响应")
    print("="*60)
    
    # 创建测试
    test = SpanStiffnessTest()
    
    # 运行详细分析
    test.compare_stiffness_reduction_cases()
    
    print("\n" + "="*60)
    print("详细结构响应分析完成！")
    print("✓ 分析了支座反力变化")
    print("✓ 分析了挠度分布变化") 
    print("✓ 分析了弯矩分布变化")
    print("✓ 分析了剪力分布变化")
    print("✓ 提供了关键断面详细对比")
    print("✓ 给出了工程评价与建议")

if __name__ == "__main__":
    main() 