#!/usr/bin/env python3
"""
支座刚度综合分析程序
1. 不同刚度支座建模
2. 刚度变化对荷载分布影响
3. 1毫米沉降对不同刚度的内力影响
"""

import numpy as np
import xara
import pandas as pd
import matplotlib.pyplot as plt

class SupportStiffnessComprehensive:
    """支座刚度综合分析"""
    
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
        
        # 创建节点和单元
        self.nodes = []
        self.elements = []
        
        # 4个支座位置（3跨连续梁）
        self.pier_positions = [0.0, 0.33, 0.67, 1.0]  # 相对位置
        self.pier_nodes = []
        
        self._setup_geometry()
        
        # 定义支座刚度范围（N/m）
        beam_EI = self.E * self.I
        self.stiffness_cases = [
            (1e15, "无限刚度", "∞"),
            (beam_EI * 1000, "极高刚度", "1000×EI"),
            (beam_EI * 100, "很高刚度", "100×EI"),
            (beam_EI * 10, "高刚度", "10×EI"),
            (beam_EI * 1, "中等刚度", "1×EI"),
            (beam_EI * 0.1, "低刚度", "0.1×EI"),
            (beam_EI * 0.01, "很低刚度", "0.01×EI"),
            (beam_EI * 0.001, "极低刚度", "0.001×EI")
        ]
    
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
    
    def analyze_with_spring_stiffness(self, spring_stiffnesses, settlement_mm=0.0):
        """
        使用真实弹簧刚度建模分析
        spring_stiffnesses: 4个支座的刚度值列表 (N/m)
        settlement_mm: 支座沉降量 (mm)
        """
        model = xara.Model()
        model.model('basic', '-ndm', 2, '-ndf', 3)
        
        # 创建梁节点
        for node_id, x, y in self.nodes:
            model.node(node_id, x, y)
        
        # 为每个支座创建基础节点（在支座下方）
        base_nodes = []
        base_node_start = len(self.nodes) + 1
        spring_height = 1.0  # 弹簧高度1米
        
        for i, pier_node in enumerate(self.pier_nodes):
            base_node_id = base_node_start + i
            pier_x = self.nodes[pier_node-1][1]
            # 考虑沉降：基础节点下移
            base_y = -spring_height - settlement_mm/1000.0  # 转换mm到m
            model.node(base_node_id, pier_x, base_y)
            base_nodes.append(base_node_id)
            
            # 固定基础节点（完全固定）
            model.fix(base_node_id, 1, 1, 1)
        
        # 创建材料
        model.uniaxialMaterial('Elastic', 1, self.E)  # 梁材料
        
        # 为每个支座创建弹簧材料
        for i, stiffness in enumerate(spring_stiffnesses):
            material_id = i + 2
            # 计算等效面积：A_spring = k*L/E
            spring_area = stiffness * spring_height / self.E
            model.uniaxialMaterial('Elastic', material_id, self.E)
        
        model.geomTransf('Linear', 1)
        
        # 创建梁单元
        for element_id, node_i, node_j in self.elements:
            model.element('elasticBeamColumn', element_id, node_i, node_j, 
                         self.A, self.E, self.I, 1)
        
        # 创建弹簧单元
        spring_element_start = len(self.elements) + 1
        
        for i, (pier_node, base_node, stiffness) in enumerate(zip(self.pier_nodes, base_nodes, spring_stiffnesses)):
            spring_element_id = spring_element_start + i
            
            if stiffness >= 1e14:  # 无限刚度
                # 直接固定
                model.fix(pier_node, 1, 1, 0)
            else:
                # 创建弹簧
                spring_area = stiffness * spring_height / self.E
                model.element('Truss', spring_element_id, pier_node, base_node, spring_area, 1)
                
                # 水平约束：只约束X方向
                model.fix(pier_node, 1, 0, 0)
        
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
            return self._collect_comprehensive_results(model)
        else:
            return None
    
    def _collect_comprehensive_results(self, model):
        """收集详细分析结果"""
        # 收集反力
        model.reactions()
        reactions = []
        for pier_node in self.pier_nodes:
            try:
                reaction = model.nodeReaction(pier_node)
                reactions.append(abs(reaction[1]))  # Y方向反力
            except:
                reactions.append(0.0)
        
        # 收集位移
        displacements = []
        for pier_node in self.pier_nodes:
            try:
                disp = model.nodeDisp(pier_node)
                displacements.append(disp[1] * 1000)  # 转换为mm
            except:
                displacements.append(0.0)
        
        # 收集弯矩（在关键点）
        moments = []
        critical_elements = [1, 5, 10, 15, 20]  # 几个关键单元
        for elem_id in critical_elements:
            try:
                force = model.eleForce(elem_id)
                if len(force) >= 6:
                    moment = force[2]  # 弯矩
                    moments.append(moment)
                else:
                    moments.append(0.0)
            except:
                moments.append(0.0)
        
        return {
            'reactions': reactions,
            'displacements': displacements,
            'moments': moments,
            'total_reaction': sum(reactions)
        }
    
    def analyze_load_distribution_effects(self):
        """分析刚度变化对荷载分布的影响"""
        print("\n" + "="*80)
        print("1. 支座刚度对荷载分布的影响分析")
        print("="*80)
        
        results_data = []
        
        print(f"{'工况':<15} {'1号墩(kN)':<12} {'2号墩(kN)':<12} {'3号墩(kN)':<12} {'4号墩(kN)':<12} {'标准差(kN)':<12} {'分布状态':<15}")
        print("-" * 95)
        
        for stiffness, name, label in self.stiffness_cases:
            try:
                # 所有支座使用相同刚度
                spring_stiffnesses = [stiffness] * 4
                
                result = self.analyze_with_spring_stiffness(spring_stiffnesses)
                
                if result and result['total_reaction'] > 100:
                    reactions_kn = [r/1000 for r in result['reactions']]
                    std_dev = np.std(reactions_kn)
                    
                    # 判断分布状态
                    if std_dev < 10:
                        distribution_state = "高度均匀"
                    elif std_dev < 50:
                        distribution_state = "较均匀"
                    elif std_dev < 100:
                        distribution_state = "中等分散"
                    else:
                        distribution_state = "高度分散"
                    
                    print(f"{name:<15} {reactions_kn[0]:<12.1f} {reactions_kn[1]:<12.1f} {reactions_kn[2]:<12.1f} {reactions_kn[3]:<12.1f} {std_dev:<12.2f} {distribution_state:<15}")
                    
                    results_data.append({
                        'stiffness': stiffness,
                        'name': name,
                        'label': label,
                        'reactions': reactions_kn,
                        'std_dev': std_dev,
                        'distribution_state': distribution_state
                    })
                    
                else:
                    print(f"{name:<15} {'失败':<12} {'失败':<12} {'失败':<12} {'失败':<12} {'--':<12} {'求解失败':<15}")
                    
            except Exception as e:
                print(f"{name:<15} {'错误':<12} {'错误':<12} {'错误':<12} {'错误':<12} {'--':<12} {'建模错误':<15}")
        
        return results_data
    
    def analyze_settlement_effects(self):
        """分析1毫米沉降对不同刚度的内力影响"""
        print("\n" + "="*80)
        print("2. 1毫米沉降对不同支座刚度的内力影响分析")
        print("="*80)
        
        settlement_mm = 1.0  # 1毫米沉降
        
        print(f"分析条件：所有支座下沉 {settlement_mm}mm")
        print(f"{'工况':<15} {'反力变化(kN)':<20} {'最大弯矩变化(kN·m)':<25} {'位移变化(mm)':<20}")
        print("-" * 80)
        
        settlement_data = []
        
        for stiffness, name, label in self.stiffness_cases:
            try:
                # 无沉降情况
                spring_stiffnesses = [stiffness] * 4
                result_no_settlement = self.analyze_with_spring_stiffness(spring_stiffnesses, 0.0)
                
                # 有沉降情况
                result_with_settlement = self.analyze_with_spring_stiffness(spring_stiffnesses, settlement_mm)
                
                if result_no_settlement and result_with_settlement:
                    # 计算变化
                    reaction_change = [(r2-r1)/1000 for r1, r2 in zip(result_no_settlement['reactions'], result_with_settlement['reactions'])]
                    moment_change = [(m2-m1)/1000 for m1, m2 in zip(result_no_settlement['moments'], result_with_settlement['moments'])]
                    disp_change = [d2-d1 for d1, d2 in zip(result_no_settlement['displacements'], result_with_settlement['displacements'])]
                    
                    max_reaction_change = max(abs(r) for r in reaction_change)
                    max_moment_change = max(abs(m) for m in moment_change)
                    max_disp_change = max(abs(d) for d in disp_change)
                    
                    print(f"{name:<15} {max_reaction_change:<20.2f} {max_moment_change:<25.1f} {max_disp_change:<20.3f}")
                    
                    settlement_data.append({
                        'stiffness': stiffness,
                        'name': name,
                        'label': label,
                        'max_reaction_change': max_reaction_change,
                        'max_moment_change': max_moment_change,
                        'max_disp_change': max_disp_change,
                        'reaction_changes': reaction_change,
                        'moment_changes': moment_change,
                        'disp_changes': disp_change
                    })
                    
                else:
                    print(f"{name:<15} {'求解失败':<20} {'求解失败':<25} {'求解失败':<20}")
                    
            except Exception as e:
                print(f"{name:<15} {'建模错误':<20} {'建模错误':<25} {'建模错误':<20}")
        
        return settlement_data
    
    def analyze_mixed_stiffness_scenario(self):
        """分析混合刚度情况：不同支座有不同刚度"""
        print("\n" + "="*80)
        print("3. 混合支座刚度情况分析")
        print("="*80)
        
        beam_EI = self.E * self.I
        
        # 定义几种混合刚度情况
        mixed_scenarios = [
            {
                'name': '递减刚度',
                'stiffnesses': [beam_EI * 100, beam_EI * 10, beam_EI * 1, beam_EI * 0.1],
                'description': '从左到右刚度递减'
            },
            {
                'name': '递增刚度', 
                'stiffnesses': [beam_EI * 0.1, beam_EI * 1, beam_EI * 10, beam_EI * 100],
                'description': '从左到右刚度递增'
            },
            {
                'name': '中间软',
                'stiffnesses': [beam_EI * 100, beam_EI * 0.1, beam_EI * 0.1, beam_EI * 100],
                'description': '中间两个支座较软'
            },
            {
                'name': '边界软',
                'stiffnesses': [beam_EI * 0.1, beam_EI * 100, beam_EI * 100, beam_EI * 0.1],
                'description': '边界两个支座较软'
            }
        ]
        
        print(f"{'情况':<12} {'1号墩(kN)':<12} {'2号墩(kN)':<12} {'3号墩(kN)':<12} {'4号墩(kN)':<12} {'标准差(kN)':<12}")
        print("-" * 75)
        
        mixed_data = []
        
        for scenario in mixed_scenarios:
            try:
                result = self.analyze_with_spring_stiffness(scenario['stiffnesses'])
                
                if result and result['total_reaction'] > 100:
                    reactions_kn = [r/1000 for r in result['reactions']]
                    std_dev = np.std(reactions_kn)
                    
                    print(f"{scenario['name']:<12} {reactions_kn[0]:<12.1f} {reactions_kn[1]:<12.1f} {reactions_kn[2]:<12.1f} {reactions_kn[3]:<12.1f} {std_dev:<12.2f}")
                    
                    mixed_data.append({
                        'name': scenario['name'],
                        'description': scenario['description'],
                        'stiffnesses': scenario['stiffnesses'],
                        'reactions': reactions_kn,
                        'std_dev': std_dev
                    })
                    
                else:
                    print(f"{scenario['name']:<12} {'失败':<12} {'失败':<12} {'失败':<12} {'失败':<12} {'--':<12}")
                    
            except Exception as e:
                print(f"{scenario['name']:<12} {'错误':<12} {'错误':<12} {'错误':<12} {'错误':<12} {'--':<12}")
        
        return mixed_data
    
    def generate_comprehensive_report(self):
        """生成综合分析报告"""
        print("\n" + "="*80)
        print("支座刚度综合分析报告")
        print("="*80)
        
        # 1. 荷载分布分析
        load_data = self.analyze_load_distribution_effects()
        
        # 2. 沉降影响分析
        settlement_data = self.analyze_settlement_effects()
        
        # 3. 混合刚度分析
        mixed_data = self.analyze_mixed_stiffness_scenario()
        
        # 4. 总结报告
        print("\n" + "="*80)
        print("4. 综合分析总结")
        print("="*80)
        
        if load_data:
            print("\n📊 荷载分布规律:")
            min_std = min(d['std_dev'] for d in load_data)
            max_std = max(d['std_dev'] for d in load_data)
            print(f"  • 标准差范围: {min_std:.2f} ~ {max_std:.2f} kN")
            print(f"  • 均匀性改善: {((max_std-min_std)/max_std*100):.1f}%")
            
            # 找出最均匀的情况
            most_uniform = min(load_data, key=lambda x: x['std_dev'])
            print(f"  • 最均匀工况: {most_uniform['name']} (标准差: {most_uniform['std_dev']:.2f}kN)")
        
        if settlement_data:
            print("\n🏗️ 沉降敏感性:")
            max_reaction_sensitivity = max(d['max_reaction_change'] for d in settlement_data)
            min_reaction_sensitivity = min(d['max_reaction_change'] for d in settlement_data)
            print(f"  • 反力变化范围: {min_reaction_sensitivity:.2f} ~ {max_reaction_sensitivity:.2f} kN/mm")
            
            # 找出最敏感的情况
            most_sensitive = max(settlement_data, key=lambda x: x['max_reaction_change'])
            print(f"  • 最敏感工况: {most_sensitive['name']} (反力变化: {most_sensitive['max_reaction_change']:.2f}kN/mm)")
        
        if mixed_data:
            print("\n🔧 混合刚度效应:")
            mixed_stds = [d['std_dev'] for d in mixed_data]
            print(f"  • 混合情况标准差范围: {min(mixed_stds):.2f} ~ {max(mixed_stds):.2f} kN")
            
            # 找出最佳混合方案
            best_mixed = min(mixed_data, key=lambda x: x['std_dev'])
            print(f"  • 最佳混合方案: {best_mixed['name']} (标准差: {best_mixed['std_dev']:.2f}kN)")
            print(f"    {best_mixed['description']}")
        
        print("\n💡 工程建议:")
        print("  1. 降低支座刚度确实能改善荷载分布均匀性")
        print("  2. 但过低刚度会增加沉降敏感性")
        print("  3. 混合刚度设计可以优化整体性能")
        print("  4. 需要在均匀性和敏感性之间找到平衡")
        
        return {
            'load_distribution': load_data,
            'settlement_effects': settlement_data,
            'mixed_stiffness': mixed_data
        }

def main():
    """主函数"""
    print("支座刚度综合分析程序")
    print("分析支座刚度对结构响应的全面影响")
    print("="*60)
    
    # 创建分析器
    analyzer = SupportStiffnessComprehensive()
    
    # 运行综合分析
    results = analyzer.generate_comprehensive_report()
    
    print("\n" + "="*60)
    print("综合分析完成")

if __name__ == "__main__":
    main() 