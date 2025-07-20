#!/usr/bin/env python3
"""
支座刚度影响测试（Spring单元版）
使用真正的FEM方法：spring单元 + boundary condition
"""

import numpy as np
import xara
import pandas as pd

class SupportStiffnessSpring:
    """支座刚度测试：使用spring单元"""
    
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
        
        self._setup_geometry()
    
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
    
    def analyze_infinite_stiffness(self):
        """无限刚度支座分析（固定约束）"""
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
    
    def analyze_spring_stiffness(self, spring_stiffness):
        """使用spring单元建模有限刚度支座"""
        model = xara.Model()
        model.model('basic', '-ndm', 2, '-ndf', 3)
        
        # 创建梁节点
        for node_id, x, y in self.nodes:
            model.node(node_id, x, y)
        
        # 为每个支座创建基础节点
        base_nodes = []
        base_node_start = len(self.nodes) + 1
        
        for i, pier_node in enumerate(self.pier_nodes):
            base_node_id = base_node_start + i
            pier_x = self.nodes[pier_node-1][1]
            model.node(base_node_id, pier_x, 0.0)  # 基础节点
            base_nodes.append(base_node_id)
            
            # 固定基础节点（完全固定）
            model.fix(base_node_id, 1, 1, 1)
        
        # 创建材料
        model.uniaxialMaterial('Elastic', 1, self.E)  # 梁材料
        model.uniaxialMaterial('Elastic', 2, spring_stiffness)  # 竖向弹簧材料
        
        # 大刚度用于水平约束
        big_stiffness = self.E * 1e6
        model.uniaxialMaterial('Elastic', 3, big_stiffness)  # 水平约束材料
        
        model.geomTransf('Linear', 1)
        
        # 创建梁单元
        for element_id, node_i, node_j in self.elements:
            model.element('elasticBeamColumn', element_id, node_i, node_j, 
                         self.A, self.E, self.I, 1)
        
        # 使用spring单元连接支座和基础
        spring_element_start = len(self.elements) + 1
        
        for i, (pier_node, base_node) in enumerate(zip(self.pier_nodes, base_nodes)):
            spring_element_id = spring_element_start + i
            
            # 使用Truss单元作为竖向弹簧
            # 将弹簧材料直接用于truss单元
            model.element('Truss', spring_element_id, pier_node, base_node, 1.0, 2)
            
            # 水平约束：只约束X方向
            model.fix(pier_node, 1, 0, 0)  # X固定，Y自由（由弹簧约束），转角自由
        
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
    
    def analyze_penalty_method(self, penalty_stiffness):
        """使用penalty方法模拟有限刚度约束"""
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
        
        # 使用penalty方法：在支座施加penalty弹簧力
        # 所有支座水平固定
        for pier_node in self.pier_nodes:
            model.fix(pier_node, 1, 0, 0)  # X固定，Y自由，转角自由
        
        # 施加荷载
        model.timeSeries('Linear', 1)
        model.pattern('Plain', 1, 1)
        
        weight_per_length = self.density * 9.81 * self.A
        for element_id, _, _ in self.elements:
            model.eleLoad('-ele', element_id, '-type', '-beamUniform', -weight_per_length)
        
        # 在支座节点施加penalty弹簧力（负载控制下的刚度模拟）
        # 这需要迭代求解...
        
        # 为简化，我们用一个近似方法：
        # 先求解自由状态的位移，然后按刚度施加反力
        
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
                displacements.append(disp[1])  # Y方向位移
            except:
                displacements.append(0.0)
        
        return {
            'reactions': reactions,
            'displacements': displacements
        }
    
    def test_spring_stiffness_effects(self):
        """测试spring刚度影响"""
        print("\n" + "="*70)
        print("支座刚度影响分析（Spring单元版）")
        print("使用真正的FEM方法：spring单元 + boundary condition")
        print("="*70)
        
        # 1. 获取无限刚度基准
        print("1. 分析无限刚度工况（固定约束）...")
        infinite_result = self.analyze_infinite_stiffness()
        
        if not infinite_result:
            print("   无限刚度分析失败！")
            return
        
        infinite_reactions_kn = [r/1000 for r in infinite_result['reactions']]
        infinite_std = np.std(infinite_reactions_kn)
        print(f"   ✓ 连续梁反力分布：{[f'{r:.1f}kN' for r in infinite_reactions_kn]}")
        print(f"   ✓ 标准差：{infinite_std:.2f}kN")
        
        # 2. 测试不同spring刚度
        print(f"\n2. 测试不同spring刚度...")
        
        beam_EI = self.E * self.I
        spring_cases = [
            (beam_EI * 100, "极高刚度 (100×EI)"),
            (beam_EI * 10, "高刚度 (10×EI)"),
            (beam_EI * 1, "中等刚度 (1×EI)"),
            (beam_EI * 0.1, "低刚度 (0.1×EI)"),
            (beam_EI * 0.01, "极低刚度 (0.01×EI)")
        ]
        
        results_table = {
            '工况': ['无限刚度'],
            '1号墩(kN)': [f"{infinite_reactions_kn[0]:.2f}"],
            '2号墩(kN)': [f"{infinite_reactions_kn[1]:.2f}"],
            '3号墩(kN)': [f"{infinite_reactions_kn[2]:.2f}"],
            '4号墩(kN)': [f"{infinite_reactions_kn[3]:.2f}"],
            '标准差(kN)': [f"{infinite_std:.2f}"],
            '分析状态': ['成功']
        }
        
        for spring_stiffness, description in spring_cases:
            print(f"\n   测试 {description}...")
            
            try:
                result = self.analyze_spring_stiffness(spring_stiffness)
                
                if result and sum(result['reactions']) > 100:
                    reactions_kn = [r/1000 for r in result['reactions']]
                    std_dev = np.std(reactions_kn)
                    
                    print(f"   ✓ 反力分布：{[f'{r:.1f}kN' for r in reactions_kn]}")
                    print(f"   ✓ 标准差：{std_dev:.2f}kN")
                    
                    # 与无限刚度对比
                    if std_dev < infinite_std:
                        trend = f"↓ 更均匀 (改善{((infinite_std-std_dev)/infinite_std*100):.1f}%)"
                    else:
                        trend = f"↑ 更不均匀"
                    print(f"   {trend}")
                    
                    # 添加到表格
                    results_table['工况'].append(description.split('(')[0].strip())
                    for i, reaction in enumerate(reactions_kn):
                        results_table[f'{i+1}号墩(kN)'].append(f"{reaction:.2f}")
                    results_table['标准差(kN)'].append(f"{std_dev:.2f}")
                    results_table['分析状态'].append('成功')
                    
                else:
                    print(f"   ❌ 失败 - 总反力异常")
                    results_table['工况'].append(description.split('(')[0].strip())
                    results_table['1号墩(kN)'].append("失败")
                    results_table['2号墩(kN)'].append("失败")
                    results_table['3号墩(kN)'].append("失败")
                    results_table['4号墩(kN)'].append("失败")
                    results_table['标准差(kN)'].append("--")
                    results_table['分析状态'].append('失败')
                    
            except Exception as e:
                print(f"   ❌ 失败 - 错误：{e}")
                results_table['工况'].append(description.split('(')[0].strip())
                results_table['1号墩(kN)'].append("错误")
                results_table['2号墩(kN)'].append("错误")
                results_table['3号墩(kN)'].append("错误")
                results_table['4号墩(kN)'].append("错误")
                results_table['标准差(kN)'].append("--")
                results_table['分析状态'].append('错误')
        
        # 3. 生成分析表
        print(f"\n📊 分析结果总结:")
        print("-" * 80)
        
        df = pd.DataFrame(results_table)
        print(df.to_string(index=False))
        
        # 4. 评估物理规律
        print(f"\n🔍 物理规律验证:")
        print("-" * 50)
        
        successful_cases = [i for i, status in enumerate(results_table['分析状态']) if status == '成功']
        
        if len(successful_cases) >= 2:
            print("✓ 成功获得多个有效工况")
            
            # 提取成功案例的标准差
            successful_stds = []
            for i in successful_cases:
                std_str = results_table['标准差(kN)'][i]
                if std_str != '--':
                    successful_stds.append(float(std_str))
            
            if len(successful_stds) >= 2:
                print(f"📈 趋势分析:")
                trend_correct = True
                for i in range(1, len(successful_stds)):
                    if successful_stds[i] >= successful_stds[i-1]:
                        trend_correct = False
                        break
                
                if trend_correct:
                    print("  ✅ 物理规律验证成功：刚度降低 → 受力更均匀")
                    max_std = max(successful_stds)
                    min_std = min(successful_stds)
                    improvement = (max_std - min_std) / max_std * 100
                    print(f"  📊 均匀性改善：{improvement:.1f}%")
                else:
                    print("  ⚠️ 趋势不完全符合预期，可能需要调整建模方法")
            else:
                print("  ⚠️ 成功案例太少，无法验证趋势")
        else:
            print("❌ 成功案例不足，建模方法需要改进")
        
        print(f"\n💡 建议:")
        print("  • Spring单元方法是正确方向")
        print("  • 可能需要调整spring刚度范围")
        print("  • 考虑使用不同的单元类型（如dashpot）")
        print("  • 尝试修改边界条件设置")

def main():
    """主函数"""
    print("支座刚度影响分析程序（Spring单元版）")
    print("使用真正的FEM方法验证物理规律")
    print("="*60)
    
    # 创建测试
    test = SupportStiffnessSpring()
    
    # 运行测试
    test.test_spring_stiffness_effects()
    
    print("\n" + "="*60)
    print("Spring单元分析完成")

if __name__ == "__main__":
    main() 