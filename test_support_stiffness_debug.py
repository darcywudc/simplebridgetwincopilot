#!/usr/bin/env python3
"""
支座刚度影响测试（调试版）
使用zeroLength单元正确建模竖向弹簧
"""

import numpy as np
import xara
import pandas as pd

class SupportStiffnessDebug:
    """支座刚度测试（调试版）：使用zeroLength单元"""
    
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
        """无限刚度支座分析"""
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
        
        # 所有支座约束：X固定，Y固定，转角自由
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
    
    def analyze_finite_stiffness(self, support_stiffness):
        """有限刚度支座分析：使用zeroLength单元"""
        model = xara.Model()
        model.model('basic', '-ndm', 2, '-ndf', 3)
        
        # 创建原始梁节点
        for node_id, x, y in self.nodes:
            model.node(node_id, x, y)
        
        # 为每个支座创建基础节点（相同位置）
        base_nodes = []
        base_node_start = len(self.nodes) + 1
        
        for i, pier_node in enumerate(self.pier_nodes):
            base_node_id = base_node_start + i
            pier_x = self.nodes[pier_node-1][1]
            model.node(base_node_id, pier_x, 0.0)  # 基础节点在相同位置
            base_nodes.append(base_node_id)
            
            # 固定基础节点
            model.fix(base_node_id, 1, 1, 1)
        
        # 创建材料和几何变换
        model.uniaxialMaterial('Elastic', 1, self.E)  # 梁材料
        model.uniaxialMaterial('Elastic', 2, support_stiffness)  # 竖向弹簧材料
        
        # 创建大刚度材料用于水平约束
        big_stiffness = self.E * 1000
        model.uniaxialMaterial('Elastic', 3, big_stiffness)  # 水平约束材料
        
        model.geomTransf('Linear', 1)
        
        # 创建梁单元
        for element_id, node_i, node_j in self.elements:
            model.element('elasticBeamColumn', element_id, node_i, node_j, 
                         self.A, self.E, self.I, 1)
        
        # 创建zeroLength弹簧单元
        spring_element_start = len(self.elements) + 1
        
        for i, (pier_node, base_node) in enumerate(zip(self.pier_nodes, base_nodes)):
            # 竖向弹簧
            spring_element_id = spring_element_start + i * 2
            
            # zeroLength单元：1-X方向(水平固定), 2-Y方向(弹簧), 3-旋转方向(自由)
            model.element('zeroLength', spring_element_id, pier_node, base_node,
                         '-mat', 3, 2, '-dir', 1, 2)
        
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
        
        return {'reactions': reactions}
    
    def test_different_stiffness(self):
        """测试不同刚度"""
        print("支座刚度影响测试（调试版）")
        print("="*50)
        
        # 无限刚度
        print("1. 测试无限刚度工况...")
        infinite_result = self.analyze_infinite_stiffness()
        
        if infinite_result:
            print(f"   成功！反力分布：{[f'{r/1000:.1f}kN' for r in infinite_result['reactions']]}")
            total = sum(infinite_result['reactions'])/1000
            print(f"   总反力：{total:.1f}kN")
        else:
            print("   失败！")
            return
        
        # 测试几个有限刚度
        beam_EI = self.E * self.I
        test_cases = [
            (beam_EI * 10, "高刚度 (10×EI)"),
            (beam_EI * 1, "中等刚度 (1×EI)"),
            (beam_EI * 0.1, "低刚度 (0.1×EI)"),
            (beam_EI * 0.01, "极低刚度 (0.01×EI)")
        ]
        
        print(f"\n2. 测试有限刚度工况...")
        print(f"   梁抗弯刚度EI = {beam_EI/1e6:.0f} MN·m²")
        
        for stiffness, description in test_cases:
            print(f"\n   测试 {description}...")
            try:
                result = self.analyze_finite_stiffness(stiffness)
                if result and sum(result['reactions']) > 100:
                    reactions_kn = [r/1000 for r in result['reactions']]
                    print(f"   成功！反力分布：{[f'{r:.1f}kN' for r in reactions_kn]}")
                    
                    # 计算均匀性
                    std = np.std(reactions_kn)
                    print(f"   标准差：{std:.2f}kN")
                    
                    # 与无限刚度对比
                    infinite_std = np.std([r/1000 for r in infinite_result['reactions']])
                    if std < infinite_std:
                        print(f"   ✓ 比无限刚度更均匀 ({infinite_std:.2f} → {std:.2f})")
                    else:
                        print(f"   ✗ 比无限刚度更不均匀 ({infinite_std:.2f} → {std:.2f})")
                else:
                    print(f"   失败！")
            except Exception as e:
                print(f"   失败！错误：{e}")

def main():
    """主函数"""
    test = SupportStiffnessDebug()
    test.test_different_stiffness()

if __name__ == "__main__":
    main() 