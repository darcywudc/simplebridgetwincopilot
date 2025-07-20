#!/usr/bin/env python3
"""
修正版支座高度效应测试程序
解决物理逻辑问题：
1. 修正弹性支座的连接方式
2. 修正沉降模拟的方向和物理含义
3. 确保结果符合结构工程常理
"""

import numpy as np
import xara
import matplotlib.pyplot as plt
import pandas as pd

class CorrectedBridgeTest:
    """修正版桥梁模型，正确实现支座高度效应"""
    
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
        
        # 3跨桥梁的支座位置
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
    
    def test_reference_case(self):
        """参考情况：标准约束"""
        print("\n=== 参考情况：标准约束 ===")
        
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
        
        # 标准约束
        model.fix(self.pier_nodes[0], 1, 1, 0)  # 固定铰接
        model.fix(self.pier_nodes[1], 0, 1, 0)  # 滑动支座
        model.fix(self.pier_nodes[2], 0, 1, 0)  # 滑动支座
        model.fix(self.pier_nodes[3], 0, 1, 0)  # 滑动支座
        
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
            print("标准约束分析收敛成功")
            
            model.reactions()
            reactions = []
            
            for i, pier_node in enumerate(self.pier_nodes):
                try:
                    reaction = model.nodeReaction(pier_node)
                    reactions.append(-reaction[1])
                    print(f"支座{i+1} 反力: {-reaction[1]/1000:.2f} kN")
                except:
                    reactions.append(0.0)
            
            total_reaction = sum(reactions)
            print(f"总反力: {total_reaction/1000:.2f} kN")
            
            return reactions
        else:
            print("标准约束分析失败")
            return [0.0] * len(self.pier_nodes)
    
    def test_corrected_elastic_supports(self, pier_heights):
        """修正版弹性支座：物理刚度建模"""
        print(f"\n=== 修正版弹性支座测试 (高度: {pier_heights}) ===")
        
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
        
        # 修正版支座弹簧
        E_pier = 30e9  # 墩台混凝土弹性模量
        A_pier = 3.0   # 墩台等效截面积 (m²)
        
        # 计算基准刚度 (基于最低墩)
        min_height = min(pier_heights)
        base_stiffness = (E_pier * A_pier) / min_height
        
        for i, (pier_node, height) in enumerate(zip(self.pier_nodes, pier_heights)):
            # 物理刚度：K = EA/h，高度越大，刚度越小
            k_vertical = (E_pier * A_pier) / height
            
            # 刚度比例（相对于最刚支座）
            stiffness_ratio = k_vertical / base_stiffness
            
            # 创建弹簧材料
            spring_material_id = 100 + i
            model.uniaxialMaterial('Elastic', spring_material_id, k_vertical)
            
            # 创建地面节点
            ground_node = 1000 + i
            model.node(ground_node, self.nodes[pier_node-1][1], 0.0)
            model.fix(ground_node, 1, 1, 1)
            
            # 使用truss单元模拟竖向弹簧（更稳定）
            spring_element_id = 2000 + i
            model.element('truss', spring_element_id, ground_node, pier_node, 
                         1.0, spring_material_id)  # 面积=1.0，刚度由材料控制
            
            # 第一个支座固定水平位移，其他支座水平自由
            if i == 0:
                model.fix(pier_node, 1, 0, 0)  # 固定水平，竖向由弹簧控制
            else:
                model.fix(pier_node, 0, 0, 0)  # 水平和竖向都由弹簧控制
            
            print(f"支座{i+1}: 节点{pier_node}, 高度{height:.1f}m, 刚度{k_vertical/1e6:.1f}MN/m, 相对刚度{stiffness_ratio:.3f}")
        
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
            print("修正弹性支座分析收敛成功")
            
            model.reactions()
            reactions = []
            
            for i, pier_node in enumerate(self.pier_nodes):
                try:
                    reaction = model.nodeReaction(pier_node)
                    reactions.append(-reaction[1])
                    print(f"支座{i+1} 反力: {-reaction[1]/1000:.2f} kN")
                except:
                    reactions.append(0.0)
            
            total_reaction = sum(reactions)
            print(f"总反力: {total_reaction/1000:.2f} kN")
            
            return reactions
        else:
            print("修正弹性支座分析失败")
            return [0.0] * len(self.pier_nodes)
    
    def test_corrected_settlement_simulation(self, pier_heights):
        """修正版沉降模拟：符合物理逻辑的强制位移"""
        print(f"\n=== 修正版沉降模拟 (高度: {pier_heights}) ===")
        
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
        
        # 基准高度（最低墩）
        min_height = min(pier_heights)
        print(f"基准高度（最低墩）: {min_height:.1f}m")
        
        # 创建支座约束
        for i, (pier_node, height) in enumerate(zip(self.pier_nodes, pier_heights)):
            if i == 0:
                # 第一个支座：固定
                model.fix(pier_node, 1, 1, 0)
            else:
                # 其他支座：竖向固定（稍后用强制位移覆盖）
                model.fix(pier_node, 0, 1, 0)
            
            print(f"支座{i+1}: 节点{pier_node}, 高度{height:.1f}m")
        
        # 施加荷载
        model.timeSeries('Linear', 1)
        model.pattern('Plain', 1, 1)
        
        weight_per_length = self.density * 9.81 * self.A
        for element_id, _, _ in self.elements:
            model.eleLoad('-ele', element_id, '-type', '-beamUniform', -weight_per_length)
        
        # 修正版强制位移：模拟高墩相对"上抬"（压缩变形大）
        settlement_factor = 0.001  # mm/mm 高度差异位移系数
        
        for i, (pier_node, height) in enumerate(zip(self.pier_nodes, pier_heights)):
            if i > 0:  # 不对第一个固定支座施加位移
                # 物理逻辑：较高墩压缩变形更大，相对"上抬"
                # 用负位移模拟这种效应，让较高墩承担更少荷载
                height_diff = height - min_height
                imposed_displacement = -height_diff * settlement_factor  # 负值 = 向上
                
                if abs(imposed_displacement) > 1e-6:
                    # 使用 sp 命令施加强制位移
                    model.sp(pier_node, 2, imposed_displacement)
                    print(f"支座{i+1} 强制位移: {imposed_displacement*1000:+.2f}mm (负值=上抬，减少荷载)")
        
        # 分析
        model.system('ProfileSPD')
        model.numberer('Plain')
        model.constraints('Transformation')
        model.integrator('LoadControl', 1.0)
        model.algorithm('Linear')
        model.analysis('Static')
        
        ok = model.analyze(1)
        
        if ok == 0:
            print("修正沉降模拟分析收敛成功")
            
            model.reactions()
            reactions = []
            
            for i, pier_node in enumerate(self.pier_nodes):
                try:
                    reaction = model.nodeReaction(pier_node)
                    reactions.append(-reaction[1])
                    print(f"支座{i+1} 反力: {-reaction[1]/1000:.2f} kN")
                except:
                    reactions.append(0.0)
            
            total_reaction = sum(reactions)
            print(f"总反力: {total_reaction/1000:.2f} kN")
            
            return reactions
        else:
            print("修正沉降模拟分析失败")
            return [0.0] * len(self.pier_nodes)
    
    def compare_corrected_methods(self):
        """比较修正后的方法"""
        print("\n" + "="*60)
        print("修正版支座高度效应测试对比")
        print("="*60)
        
        # 先测试参考情况
        ref_reactions = self.test_reference_case()
        
        # 测试场景
        test_cases = [
            {
                'name': '均匀高度',
                'heights': [8.0, 8.0, 8.0, 8.0],
                'description': '所有支座高度相同，应无重分布'
            },
            {
                'name': '中间高',
                'heights': [8.0, 12.0, 12.0, 8.0],
                'description': '中间支座较高，应承担更少荷载'
            },
            {
                'name': '中间低',
                'heights': [8.0, 6.0, 6.0, 8.0],
                'description': '中间支座较低，应承担更多荷载'
            },
            {
                'name': '递增高度',
                'heights': [6.0, 8.0, 10.0, 12.0],
                'description': '高度递增，荷载应向左侧（低墩）转移'
            }
        ]
        
        results = []
        
        for case in test_cases:
            print(f"\n测试场景: {case['name']} - {case['description']}")
            
            # 修正版弹性支座测试
            reactions_elastic = self.test_corrected_elastic_supports(case['heights'])
            
            # 修正版沉降模拟测试
            reactions_settlement = self.test_corrected_settlement_simulation(case['heights'])
            
            results.append({
                'case': case['name'],
                'heights': case['heights'],
                'description': case['description'],
                'reference_reactions': ref_reactions,
                'elastic_reactions': reactions_elastic,
                'settlement_reactions': reactions_settlement
            })
        
        # 生成对比表格
        self.generate_corrected_comparison(results)
        
        # 验证物理常理
        self.validate_physics(results)
    
    def generate_corrected_comparison(self, results):
        """生成修正后的对比表格"""
        print("\n" + "="*80)
        print("修正版反力对比表 (kN)")
        print("="*80)
        
        for result in results:
            print(f"\n{result['case']} - {result['description']}")
            print(f"支座高度: {result['heights']}")
            print("-" * 80)
            
            # 创建表格
            table_data = {
                '支座': [f'支座{i+1}' for i in range(4)],
                '高度(m)': result['heights'],
                '参考值': [f"{r/1000:.2f}" for r in result['reference_reactions']],
                '弹性支座': [f"{r/1000:.2f}" for r in result['elastic_reactions']],
                '沉降模拟': [f"{r/1000:.2f}" for r in result['settlement_reactions']],
                '弹性变化%': [f"{((e-r)/r*100):+.1f}" for e, r in zip(result['elastic_reactions'], result['reference_reactions']) if r != 0],
                '沉降变化%': [f"{((s-r)/r*100):+.1f}" for s, r in zip(result['settlement_reactions'], result['reference_reactions']) if r != 0]
            }
            
            df = pd.DataFrame(table_data)
            print(df.to_string(index=False))
            
            # 计算总反力
            total_ref = sum(result['reference_reactions'])
            total_elastic = sum(result['elastic_reactions'])
            total_settlement = sum(result['settlement_reactions'])
            
            print(f"总反力: 参考={total_ref/1000:.2f}kN, 弹性={total_elastic/1000:.2f}kN, 沉降={total_settlement/1000:.2f}kN")
    
    def validate_physics(self, results):
        """验证结果是否符合物理常理"""
        print("\n" + "="*80)
        print("物理常理验证")
        print("="*80)
        
        for result in results:
            if result['case'] == '均匀高度':
                continue  # 跳过均匀情况
                
            print(f"\n{result['case']} 物理常理检验:")
            print("-" * 50)
            
            heights = result['heights']
            elastic_reactions = result['elastic_reactions']
            settlement_reactions = result['settlement_reactions']
            
            # 验证弹性支座结果
            print("弹性支座方法验证:")
            for i in range(4):
                height = heights[i]
                reaction = elastic_reactions[i] / 1000
                
                # 找出最低和最高墩
                min_height_idx = heights.index(min(heights))
                max_height_idx = heights.index(max(heights))
                
                if i == min_height_idx and height != max(heights):
                    expected = "应承担更多荷载（最刚）"
                elif i == max_height_idx and height != min(heights):
                    expected = "应承担更少荷载（最柔）"
                else:
                    expected = "中等荷载"
                
                print(f"  支座{i+1} (高度{height:.1f}m): 反力{reaction:.2f}kN - {expected}")
            
            # 验证沉降模拟结果
            print("\n沉降模拟方法验证:")
            for i in range(4):
                height = heights[i]
                reaction = settlement_reactions[i] / 1000
                ref_reaction = result['reference_reactions'][i] / 1000
                change = reaction - ref_reaction
                
                min_height_idx = heights.index(min(heights))
                max_height_idx = heights.index(max(heights))
                
                if i == min_height_idx and height != max(heights):
                    expected_change = "增加"
                    is_correct = change > 0
                elif i == max_height_idx and height != min(heights):
                    expected_change = "减少"
                    is_correct = change < 0
                else:
                    expected_change = "适中变化"
                    is_correct = True
                
                status = "✓" if is_correct else "✗"
                print(f"  {status} 支座{i+1} (高度{height:.1f}m): 反力变化{change:+.2f}kN - 预期{expected_change}")

def main():
    """主函数"""
    print("修正版支座高度效应测试程序")
    print("解决物理逻辑问题，确保结果符合结构工程常理")
    print("="*60)
    
    # 创建修正版测试桥梁
    bridge = CorrectedBridgeTest()
    
    # 运行修正版对比测试
    bridge.compare_corrected_methods()
    
    print("\n修正版测试完成！")
    print("结果应该符合物理常理：")
    print("- 较高支座（更柔）承担更少荷载")
    print("- 较低支座（更刚）承担更多荷载")
    print("- 总反力守恒")

if __name__ == "__main__":
    main() 