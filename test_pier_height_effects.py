#!/usr/bin/env python3
"""
支座高度效应测试程序
测试不同支座高度对荷载分布的影响
"""

import numpy as np
import xara
import matplotlib.pyplot as plt
import pandas as pd

class SimpleBridgeTest:
    """简化桥梁模型用于测试支座高度效应"""
    
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
    
    def test_method_1_spring_supports(self, pier_heights):
        """方法1: 使用弹簧支座模拟高度效应"""
        print("\n=== 方法1: 弹簧支座模拟 ===")
        
        # 创建OpenSees模型
        model = xara.Model()
        model.model('basic', '-ndm', 2, '-ndf', 3)
        
        # 创建节点
        for node_id, x, y in self.nodes:
            model.node(node_id, x, y)
        
        # 创建材料
        model.uniaxialMaterial('Elastic', 1, self.E)
        
        # 创建几何变换
        model.geomTransf('Linear', 1)
        
        # 创建梁单元
        for element_id, node_i, node_j in self.elements:
            model.element('elasticBeamColumn', element_id, node_i, node_j, 
                         self.A, self.E, self.I, 1)
        
        # 创建支座弹簧
        E_pier = 30e9  # 支座弹性模量
        A_pier = 4.0   # 支座面积
        
        for i, (pier_node, height) in enumerate(zip(self.pier_nodes, pier_heights)):
            # 计算弹簧刚度
            k_vertical = (E_pier * A_pier) / height
            
            # 创建弹簧材料
            spring_material_id = 100 + i
            model.uniaxialMaterial('Elastic', spring_material_id, k_vertical)
            
            # 创建地面节点
            ground_node = 1000 + i
            model.node(ground_node, self.nodes[pier_node-1][1], -height)
            model.fix(ground_node, 1, 1, 1)
            
            # 创建竖向弹簧
            spring_element_id = 2000 + i
            model.element('truss', spring_element_id, ground_node, pier_node, 1.0, spring_material_id)
            
            # 第一个支座固定水平位移
            if i == 0:
                model.fix(pier_node, 1, 0, 0)
            else:
                model.fix(pier_node, 0, 0, 0)
            
            print(f"支座{i+1}: 节点{pier_node}, 高度{height:.1f}m, 刚度{k_vertical/1e6:.1f}MN/m")
        
        # 施加荷载
        model.timeSeries('Linear', 1)
        model.pattern('Plain', 1, 1)
        
        # 自重
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
            print("分析收敛成功")
            
            # 提取反力
            model.reactions()
            reactions = []
            
            for i, pier_node in enumerate(self.pier_nodes):
                try:
                    reaction = model.nodeReaction(pier_node)
                    reactions.append(-reaction[1])  # 竖向反力
                    print(f"支座{i+1} 反力: {-reaction[1]/1000:.2f} kN")
                except:
                    reactions.append(0.0)
            
            return reactions
        else:
            print("分析失败")
            return [0.0] * len(self.pier_nodes)
    
    def test_method_2_variable_stiffness(self, pier_heights):
        """方法2: 变刚度支座模拟"""
        print("\n=== 方法2: 变刚度支座模拟 ===")
        
        model = xara.Model()
        model.model('basic', '-ndm', 2, '-ndf', 3)
        
        # 创建节点
        for node_id, x, y in self.nodes:
            model.node(node_id, x, y)
        
        # 创建材料
        model.uniaxialMaterial('Elastic', 1, self.E)
        model.geomTransf('Linear', 1)
        
        # 创建梁单元
        for element_id, node_i, node_j in self.elements:
            model.element('elasticBeamColumn', element_id, node_i, node_j, 
                         self.A, self.E, self.I, 1)
        
        # 创建变刚度支座
        base_stiffness = 1e9  # 基础刚度
        
        for i, (pier_node, height) in enumerate(zip(self.pier_nodes, pier_heights)):
            # 根据高度调节刚度 (高度越大，刚度越小)
            height_factor = 8.0 / height  # 8m为基准高度
            k_vertical = base_stiffness * height_factor
            
            # 创建刚度材料
            stiff_material_id = 200 + i
            model.uniaxialMaterial('Elastic', stiff_material_id, k_vertical)
            
            # 创建地面节点
            ground_node = 2000 + i
            model.node(ground_node, self.nodes[pier_node-1][1], 0.0)
            model.fix(ground_node, 1, 1, 1)
            
            # 创建竖向弹簧
            spring_element_id = 3000 + i
            model.element('zeroLength', spring_element_id, ground_node, pier_node, 
                         '-mat', stiff_material_id, '-dir', 2)
            
            # 第一个支座固定水平位移
            if i == 0:
                model.fix(pier_node, 1, 0, 0)
            else:
                model.fix(pier_node, 0, 0, 0)
            
            print(f"支座{i+1}: 节点{pier_node}, 高度{height:.1f}m, 调节刚度{k_vertical/1e6:.1f}MN/m")
        
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
            print("分析收敛成功")
            
            model.reactions()
            reactions = []
            
            for i, pier_node in enumerate(self.pier_nodes):
                try:
                    reaction = model.nodeReaction(pier_node)
                    reactions.append(-reaction[1])
                    print(f"支座{i+1} 反力: {-reaction[1]/1000:.2f} kN")
                except:
                    reactions.append(0.0)
            
            return reactions
        else:
            print("分析失败")
            return [0.0] * len(self.pier_nodes)
    
    def test_method_3_settlement(self, pier_heights):
        """方法3: 支座沉降模拟高度效应"""
        print("\n=== 方法3: 支座沉降模拟 ===")
        
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
        
        # 创建支座约束
        base_height = 8.0  # 基准高度
        
        for i, (pier_node, height) in enumerate(zip(self.pier_nodes, pier_heights)):
            # 计算相对沉降
            settlement = (height - base_height) * 0.001  # 高度差转换为沉降
            
            if i == 0:
                # 第一个支座：固定
                model.fix(pier_node, 1, 1, 0)
            else:
                # 其他支座：竖向固定
                model.fix(pier_node, 0, 1, 0)
            
            # 如果有沉降，施加强制位移
            if abs(settlement) > 1e-6:
                model.sp(pier_node, 2, settlement)  # 强制竖向位移
            
            print(f"支座{i+1}: 节点{pier_node}, 高度{height:.1f}m, 沉降{settlement*1000:.2f}mm")
        
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
            print("分析收敛成功")
            
            model.reactions()
            reactions = []
            
            for i, pier_node in enumerate(self.pier_nodes):
                try:
                    reaction = model.nodeReaction(pier_node)
                    reactions.append(-reaction[1])
                    print(f"支座{i+1} 反力: {-reaction[1]/1000:.2f} kN")
                except:
                    reactions.append(0.0)
            
            return reactions
        else:
            print("分析失败")
            return [0.0] * len(self.pier_nodes)
    
    def compare_methods(self):
        """比较不同方法的结果"""
        print("\n" + "="*60)
        print("支座高度效应测试对比")
        print("="*60)
        
        # 测试场景
        test_cases = [
            {
                'name': '均匀高度',
                'heights': [8.0, 8.0, 8.0, 8.0],
                'description': '所有支座高度相同'
            },
            {
                'name': '中间高',
                'heights': [8.0, 12.0, 12.0, 8.0],
                'description': '中间支座高度较高'
            },
            {
                'name': '中间低',
                'heights': [8.0, 6.0, 6.0, 8.0],
                'description': '中间支座高度较低'
            },
            {
                'name': '递增高度',
                'heights': [6.0, 8.0, 10.0, 12.0],
                'description': '支座高度递增'
            }
        ]
        
        results = []
        
        for case in test_cases:
            print(f"\n测试场景: {case['name']} - {case['description']}")
            print(f"支座高度: {case['heights']}")
            
            # 方法1: 弹簧支座
            reactions_1 = self.test_method_1_spring_supports(case['heights'])
            
            # 方法2: 变刚度支座
            reactions_2 = self.test_method_2_variable_stiffness(case['heights'])
            
            # 方法3: 支座沉降
            reactions_3 = self.test_method_3_settlement(case['heights'])
            
            results.append({
                'case': case['name'],
                'heights': case['heights'],
                'spring_reactions': reactions_1,
                'stiffness_reactions': reactions_2,
                'settlement_reactions': reactions_3
            })
        
        # 生成对比表格
        self.generate_comparison_table(results)
        
        # 生成图表
        self.plot_results(results)
    
    def generate_comparison_table(self, results):
        """生成对比表格"""
        print("\n" + "="*80)
        print("反力对比表 (kN)")
        print("="*80)
        
        for result in results:
            print(f"\n{result['case']} - 支座高度: {result['heights']}")
            print("-" * 60)
            
            # 创建表格
            table_data = {
                '支座': [f'支座{i+1}' for i in range(4)],
                '高度(m)': result['heights'],
                '弹簧法': [f"{r/1000:.2f}" for r in result['spring_reactions']],
                '变刚度法': [f"{r/1000:.2f}" for r in result['stiffness_reactions']], 
                '沉降法': [f"{r/1000:.2f}" for r in result['settlement_reactions']]
            }
            
            df = pd.DataFrame(table_data)
            print(df.to_string(index=False))
            
            # 计算总反力
            total_spring = sum(result['spring_reactions'])
            total_stiffness = sum(result['stiffness_reactions'])
            total_settlement = sum(result['settlement_reactions'])
            
            print(f"总反力: 弹簧法={total_spring/1000:.2f}kN, 变刚度法={total_stiffness/1000:.2f}kN, 沉降法={total_settlement/1000:.2f}kN")
    
    def plot_results(self, results):
        """绘制结果图表"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('支座高度效应测试结果对比', fontsize=16)
        
        for i, result in enumerate(results):
            ax = axes[i//2, i%2]
            
            pier_labels = ['支座1', '支座2', '支座3', '支座4']
            x = np.arange(len(pier_labels))
            width = 0.25
            
            # 绘制柱状图
            ax.bar(x - width, [r/1000 for r in result['spring_reactions']], width, 
                   label='弹簧法', alpha=0.8)
            ax.bar(x, [r/1000 for r in result['stiffness_reactions']], width, 
                   label='变刚度法', alpha=0.8)
            ax.bar(x + width, [r/1000 for r in result['settlement_reactions']], width, 
                   label='沉降法', alpha=0.8)
            
            ax.set_xlabel('支座')
            ax.set_ylabel('反力 (kN)')
            ax.set_title(f'{result["case"]} - 高度: {result["heights"]}')
            ax.set_xticks(x)
            ax.set_xticklabels(pier_labels)
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('/Users/darcyy/Desktop/Python2/simpletwindemocopilot/pier_height_effects_test.png', dpi=300)
        plt.show()

def main():
    """主函数"""
    print("支座高度效应测试程序")
    print("="*40)
    
    # 创建测试桥梁
    bridge = SimpleBridgeTest()
    
    # 运行对比测试
    bridge.compare_methods()
    
    print("\n测试完成！结果已保存为 pier_height_effects_test.png")

if __name__ == "__main__":
    main()
