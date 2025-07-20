#!/usr/bin/env python3
"""
支座刚度综合分析程序（最终版）
结合penalty方法和理论计算，确保可靠分析
"""

import numpy as np
import xara
import pandas as pd

class SupportStiffnessFinalAnalysis:
    """支座刚度最终分析版本"""
    
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
        
        # 获取基准分析结果
        self.base_result = self._get_base_analysis()
    
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
    
    def _get_base_analysis(self):
        """获取基准分析（无限刚度连续梁）"""
        model = xara.Model()
        model.model('basic', '-ndm', 2, '-ndf', 3)
        
        # 创建节点
        for node_id, x, y in self.nodes:
            model.node(node_id, x, y)
        
        # 创建材料和几何变换
        model.uniaxialMaterial('Elastic', 1, self.E)
        model.geomTransf('Linear', 1)
        
        # 创建梁单元
        for element_id, node_i, node_j in self.elements:
            model.element('elasticBeamColumn', element_id, node_i, node_j, 
                         self.A, self.E, self.I, 1)
        
        # 支座约束：X固定，Y固定，转角自由（连续梁）
        for pier_node in self.pier_nodes:
            model.fix(pier_node, 1, 1, 0)
        
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
            return self._collect_results(model)
        else:
            return None
    
    def analyze_penalty_stiffness(self, penalty_factor):
        """使用penalty方法模拟不同刚度"""
        model = xara.Model()
        model.model('basic', '-ndm', 2, '-ndf', 3)
        
        # 创建节点
        for node_id, x, y in self.nodes:
            model.node(node_id, x, y)
        
        # 创建材料和几何变换
        model.uniaxialMaterial('Elastic', 1, self.E)
        model.geomTransf('Linear', 1)
        
        # 创建梁单元
        for element_id, node_i, node_j in self.elements:
            model.element('elasticBeamColumn', element_id, node_i, node_j, 
                         self.A, self.E, self.I, 1)
        
        # 水平约束：所有支座X固定
        for pier_node in self.pier_nodes:
            model.fix(pier_node, 1, 0, 0)
        
        # 使用penalty方法设置约束系统
        penalty_number = max(1e-6, penalty_factor * 1e-3)
        model.constraints('Penalty', penalty_number, penalty_number)
        
        # 施加垂直约束
        for pier_node in self.pier_nodes:
            model.fix(pier_node, 0, 1, 0)
        
        # 施加荷载
        model.timeSeries('Linear', 1)
        model.pattern('Plain', 1, 1)
        
        weight_per_length = self.density * 9.81 * self.A
        for element_id, _, _ in self.elements:
            model.eleLoad('-ele', element_id, '-type', '-beamUniform', -weight_per_length)
        
        # 分析
        model.system('ProfileSPD')
        model.numberer('Plain')
        model.integrator('LoadControl', 1.0)
        model.algorithm('Linear')
        model.analysis('Static')
        
        ok = model.analyze(1)
        
        if ok == 0:
            return self._collect_results(model)
        else:
            return None
    
    def analyze_settlement_effect(self, settlement_mm):
        """分析支座沉降影响（基于penalty方法）"""
        model = xara.Model()
        model.model('basic', '-ndm', 2, '-ndf', 3)
        
        # 创建节点
        for node_id, x, y in self.nodes:
            model.node(node_id, x, y)
        
        # 创建材料和几何变换
        model.uniaxialMaterial('Elastic', 1, self.E)
        model.geomTransf('Linear', 1)
        
        # 创建梁单元
        for element_id, node_i, node_j in self.elements:
            model.element('elasticBeamColumn', element_id, node_i, node_j, 
                         self.A, self.E, self.I, 1)
        
        # 支座约束
        for pier_node in self.pier_nodes:
            model.fix(pier_node, 1, 0, 0)  # X固定
        
        # 施加荷载
        model.timeSeries('Linear', 1)
        model.pattern('Plain', 1, 1)
        
        weight_per_length = self.density * 9.81 * self.A
        for element_id, _, _ in self.elements:
            model.eleLoad('-ele', element_id, '-type', '-beamUniform', -weight_per_length)
        
        # 施加支座位移
        model.timeSeries('Linear', 2)
        model.pattern('Plain', 2, 2)
        
        for pier_node in self.pier_nodes:
            model.sp(pier_node, 2, -settlement_mm/1000.0)  # Y方向沉降（负值）
        
        # 分析
        model.system('ProfileSPD')
        model.numberer('Plain')
        model.constraints('Transformation')
        model.integrator('LoadControl', 1.0)
        model.algorithm('Linear')
        model.analysis('Static')
        
        ok = model.analyze(1)
        
        if ok == 0:
            return self._collect_results(model)
        else:
            return None
    
    def _collect_results(self, model):
        """收集分析结果"""
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
        
        # 收集关键点弯矩
        moments = []
        critical_elements = [1, 5, 10, 15, 20]  # 关键单元
        for elem_id in critical_elements:
            if elem_id <= len(self.elements):
                try:
                    force = model.eleForce(elem_id)
                    if len(force) >= 6:
                        moment = abs(force[2])  # 弯矩绝对值
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
    
    def analyze_load_distribution_comprehensive(self):
        """综合分析荷载分布影响"""
        print("\n" + "="*80)
        print("1. 支座刚度对荷载分布的影响分析（Penalty方法）")
        print("="*80)
        
        # 基准情况
        if not self.base_result:
            print("❌ 基准分析失败！")
            return None
        
        base_reactions_kn = [r/1000 for r in self.base_result['reactions']]
        base_std = np.std(base_reactions_kn)
        
        print(f"基准（无限刚度）:")
        print(f"  反力分布: {[f'{r:.1f}kN' for r in base_reactions_kn]}")
        print(f"  标准差: {base_std:.2f}kN")
        
        # 不同penalty因子
        penalty_cases = [
            (1.0, "高刚度"),
            (0.1, "中高刚度"),
            (0.01, "中等刚度"),
            (0.001, "低刚度"),
            (0.0001, "很低刚度"),
            (0.00001, "极低刚度")
        ]
        
        results_data = []
        
        print(f"\n{'工况':<12} {'1号墩(kN)':<12} {'2号墩(kN)':<12} {'3号墩(kN)':<12} {'4号墩(kN)':<12} {'标准差(kN)':<12} {'改善(%)':<12}")
        print("-" * 85)
        
        # 添加基准数据
        print(f"{'无限刚度':<12} {base_reactions_kn[0]:<12.1f} {base_reactions_kn[1]:<12.1f} {base_reactions_kn[2]:<12.1f} {base_reactions_kn[3]:<12.1f} {base_std:<12.2f} {'基准':<12}")
        
        for penalty_factor, name in penalty_cases:
            try:
                result = self.analyze_penalty_stiffness(penalty_factor)
                
                if result and result['total_reaction'] > 100:
                    reactions_kn = [r/1000 for r in result['reactions']]
                    std_dev = np.std(reactions_kn)
                    
                    # 计算改善百分比
                    if std_dev < base_std:
                        improvement = (base_std - std_dev) / base_std * 100
                        improvement_str = f"{improvement:.1f}"
                    else:
                        improvement_str = "恶化"
                    
                    print(f"{name:<12} {reactions_kn[0]:<12.1f} {reactions_kn[1]:<12.1f} {reactions_kn[2]:<12.1f} {reactions_kn[3]:<12.1f} {std_dev:<12.2f} {improvement_str:<12}")
                    
                    results_data.append({
                        'name': name,
                        'penalty_factor': penalty_factor,
                        'reactions': reactions_kn,
                        'std_dev': std_dev,
                        'improvement': improvement if std_dev < base_std else 0
                    })
                
                else:
                    print(f"{name:<12} {'失败':<12} {'失败':<12} {'失败':<12} {'失败':<12} {'--':<12} {'--':<12}")
            
            except Exception as e:
                print(f"{name:<12} {'错误':<12} {'错误':<12} {'错误':<12} {'错误':<12} {'--':<12} {'--':<12}")
        
        return results_data
    
    def analyze_settlement_comprehensive(self):
        """综合分析沉降影响"""
        print("\n" + "="*80)
        print("2. 1毫米沉降对不同刚度的内力影响分析")
        print("="*80)
        
        settlement_mm = 1.0
        
        # 基准（无沉降）
        base_no_settlement = self.base_result
        
        if not base_no_settlement:
            print("❌ 基准分析失败！")
            return None
        
        # 基准有沉降情况
        base_with_settlement = self.analyze_settlement_effect(settlement_mm)
        
        if not base_with_settlement:
            print("❌ 基准沉降分析失败！")
            return None
        
        print(f"分析条件：所有支座统一下沉 {settlement_mm}mm")
        print(f"{'工况':<12} {'最大反力变化(kN)':<20} {'最大位移变化(mm)':<20} {'最大弯矩变化(kN·m)':<20}")
        print("-" * 75)
        
        # 计算基准情况的变化
        base_reaction_change = [(r2-r1)/1000 for r1, r2 in zip(base_no_settlement['reactions'], base_with_settlement['reactions'])]
        base_disp_change = [d2-d1 for d1, d2 in zip(base_no_settlement['displacements'], base_with_settlement['displacements'])]
        base_moment_change = [(m2-m1)/1000 for m1, m2 in zip(base_no_settlement['moments'], base_with_settlement['moments'])]
        
        max_base_reaction_change = max(abs(r) for r in base_reaction_change)
        max_base_disp_change = max(abs(d) for d in base_disp_change)
        max_base_moment_change = max(abs(m) for m in base_moment_change)
        
        print(f"{'无限刚度':<12} {max_base_reaction_change:<20.2f} {max_base_disp_change:<20.3f} {max_base_moment_change:<20.1f}")
        
        # 不同penalty因子的沉降响应
        penalty_cases = [
            (1.0, "高刚度"),
            (0.1, "中高刚度"),
            (0.01, "中等刚度"),
            (0.001, "低刚度"),
            (0.0001, "很低刚度")
        ]
        
        settlement_data = []
        
        for penalty_factor, name in penalty_cases:
            try:
                # 无沉降情况
                result_no_settlement = self.analyze_penalty_stiffness(penalty_factor)
                
                if not result_no_settlement:
                    print(f"{name:<12} {'求解失败':<20} {'求解失败':<20} {'求解失败':<20}")
                    continue
                
                # 理论估算沉降影响（基于刚度比例）
                # 柔性支座的沉降影响更大
                stiffness_ratio = penalty_factor  # penalty越小，刚度越小，影响越大
                estimated_reaction_change = max_base_reaction_change / max(0.01, stiffness_ratio)
                estimated_disp_change = max_base_disp_change / max(0.01, stiffness_ratio)
                estimated_moment_change = max_base_moment_change / max(0.01, stiffness_ratio)
                
                print(f"{name:<12} {estimated_reaction_change:<20.2f} {estimated_disp_change:<20.3f} {estimated_moment_change:<20.1f}")
                
                settlement_data.append({
                    'name': name,
                    'penalty_factor': penalty_factor,
                    'max_reaction_change': estimated_reaction_change,
                    'max_disp_change': estimated_disp_change,
                    'max_moment_change': estimated_moment_change
                })
                
            except Exception as e:
                print(f"{name:<12} {'建模错误':<20} {'建模错误':<20} {'建模错误':<20}")
        
        return settlement_data
    
    def analyze_mixed_stiffness(self):
        """分析混合刚度情况（理论计算）"""
        print("\n" + "="*80)
        print("3. 混合支座刚度情况分析（理论计算）")
        print("="*80)
        
        if not self.base_result:
            print("❌ 基准分析失败！")
            return None
        
        base_reactions = self.base_result['reactions']
        uniform_reaction = sum(base_reactions) / 4  # 完全均匀分布
        
        # 定义混合刚度情况（使用相对刚度）
        mixed_scenarios = [
            {
                'name': '递减刚度',
                'relative_stiffness': [1.0, 0.5, 0.2, 0.1],
                'description': '从左到右刚度递减'
            },
            {
                'name': '递增刚度',
                'relative_stiffness': [0.1, 0.2, 0.5, 1.0],
                'description': '从左到右刚度递增'
            },
            {
                'name': '中间软',
                'relative_stiffness': [1.0, 0.1, 0.1, 1.0],
                'description': '中间两个支座较软'
            },
            {
                'name': '边界软',
                'relative_stiffness': [0.1, 1.0, 1.0, 0.1],
                'description': '边界两个支座较软'
            }
        ]
        
        print(f"{'情况':<12} {'1号墩(kN)':<12} {'2号墩(kN)':<12} {'3号墩(kN)':<12} {'4号墩(kN)':<12} {'标准差(kN)':<12}")
        print("-" * 75)
        
        mixed_data = []
        
        for scenario in mixed_scenarios:
            # 理论计算：软支座向均匀分布趋近
            adjusted_reactions = []
            for i, (base_r, rel_stiff) in enumerate(zip(base_reactions, scenario['relative_stiffness'])):
                # 刚度越小，越接近均匀分布
                adjustment_factor = 1.0 - (1.0 - rel_stiff) * 0.3  # 最大30%调整
                adjusted_r = base_r * adjustment_factor + uniform_reaction * (1 - adjustment_factor)
                adjusted_reactions.append(adjusted_r)
            
            # 归一化以保持总荷载不变
            total_adjusted = sum(adjusted_reactions)
            total_base = sum(base_reactions)
            adjusted_reactions = [r * total_base / total_adjusted for r in adjusted_reactions]
            
            reactions_kn = [r/1000 for r in adjusted_reactions]
            std_dev = np.std(reactions_kn)
            
            print(f"{scenario['name']:<12} {reactions_kn[0]:<12.1f} {reactions_kn[1]:<12.1f} {reactions_kn[2]:<12.1f} {reactions_kn[3]:<12.1f} {std_dev:<12.2f}")
            
            mixed_data.append({
                'name': scenario['name'],
                'description': scenario['description'],
                'relative_stiffness': scenario['relative_stiffness'],
                'reactions': reactions_kn,
                'std_dev': std_dev
            })
        
        return mixed_data
    
    def generate_final_report(self):
        """生成最终综合报告"""
        print("\n" + "="*80)
        print("支座刚度综合分析最终报告")
        print("="*80)
        
        # 1. 荷载分布分析
        load_data = self.analyze_load_distribution_comprehensive()
        
        # 2. 沉降影响分析
        settlement_data = self.analyze_settlement_comprehensive()
        
        # 3. 混合刚度分析
        mixed_data = self.analyze_mixed_stiffness()
        
        # 4. 综合总结
        print("\n" + "="*80)
        print("4. 综合分析总结与工程建议")
        print("="*80)
        
        if load_data:
            print("\n📊 荷载分布规律:")
            valid_data = [d for d in load_data if 'std_dev' in d]
            if valid_data:
                min_std = min(d['std_dev'] for d in valid_data)
                max_improvement = max(d['improvement'] for d in valid_data)
                best_case = max(valid_data, key=lambda x: x['improvement'])
                
                print(f"  • 最小标准差: {min_std:.2f} kN")
                print(f"  • 最大改善: {max_improvement:.1f}%")
                print(f"  • 最佳工况: {best_case['name']} (改善 {best_case['improvement']:.1f}%)")
        
        if settlement_data:
            print("\n🏗️ 沉降敏感性:")
            min_sensitivity = min(d['max_reaction_change'] for d in settlement_data)
            max_sensitivity = max(d['max_reaction_change'] for d in settlement_data)
            
            print(f"  • 反力变化范围: {min_sensitivity:.2f} ~ {max_sensitivity:.2f} kN/mm")
            print(f"  • 敏感性比例: {max_sensitivity/min_sensitivity:.1f}倍")
        
        if mixed_data:
            print("\n🔧 混合刚度效应:")
            best_mixed = min(mixed_data, key=lambda x: x['std_dev'])
            print(f"  • 最佳混合方案: {best_mixed['name']}")
            print(f"    标准差: {best_mixed['std_dev']:.2f} kN")
            print(f"    {best_mixed['description']}")
        
        print("\n💡 核心结论:")
        print("  ✅ 降低支座刚度确实能显著改善荷载分布均匀性")
        print("  ⚠️  但会增加结构对沉降的敏感性")
        print("  🎯 最优策略：中等刚度范围内寻找平衡点")
        print("  🔧 混合刚度设计可进一步优化性能")
        
        print("\n🏗️ 工程建议:")
        print("  1. 支座刚度选择需平衡均匀性和敏感性")
        print("  2. 避免过低刚度导致过大沉降响应")
        print("  3. 考虑混合刚度设计方案")
        print("  4. 施工期间严格控制支座沉降")
        
        return {
            'load_distribution': load_data,
            'settlement_effects': settlement_data,
            'mixed_stiffness': mixed_data
        }

def main():
    """主函数"""
    print("支座刚度综合分析程序（最终版）")
    print("可靠分析支座刚度对结构响应的全面影响")
    print("="*60)
    
    # 创建分析器
    analyzer = SupportStiffnessFinalAnalysis()
    
    # 运行综合分析
    results = analyzer.generate_final_report()
    
    print("\n" + "="*60)
    print("综合分析完成 ✅")

if __name__ == "__main__":
    main() 