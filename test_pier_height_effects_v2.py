#!/usr/bin/env python3
"""
修复版支座高度效应测试程序
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
    
    def test_elastic_supports(self, pier_heights):
        """方法1: 弹性支座 (更合理的刚度)"""
        print(f"\n=== 弹性支座测试 (高度: {pier_heights}) ===")
        
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
        
        # 创建支座弹簧
        E_pier = 25e9  # 支座混凝土弹性模量
        base_area = 2.0  # 基础截面积
        
        for i, (pier_node, height) in enumerate(zip(self.pier_nodes, pier_heights)):
            # 计算弹簧刚度 - 简化为柱的轴向刚度
            k_vertical = (E_pier * base_area) / height
            
            # 创建弹簧材料
            spring_material_id = 100 + i
            model.uniaxialMaterial('Elastic', spring_material_id, k_vertical)
            
            # 创建地面节点
            ground_node = 1000 + i
            model.node(ground_node, self.nodes[pier_node-1][1], 0.0)
            model.fix(ground_node, 1, 1, 1)
            
            # 创建竖向弹簧 (使用zeroLength单元)
            spring_element_id = 2000 + i
            model.element('zeroLength', spring_element_id, ground_node, pier_node, 
                         '-mat', spring_material_id, '-dir', 2)
            
            # 第一个支座固定水平位移
            if i == 0:
                model.fix(pier_node, 1, 0, 0)
            else:
                model.fix(pier_node, 0, 0, 0)
            
            print(f"支座{i+1}: 节点{pier_node}, 高度{height:.1f}m, 刚度{k_vertical/1e6:.1f}MN/m")
        
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
            print("弹性支座分析收敛成功")
            
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
            print("弹性支座分析失败")
            return [0.0] * len(self.pier_nodes)
    
    def test_rigid_supports_with_settlement(self, pier_heights):
        """方法2: 刚性支座 + 强制位移"""
        print(f"\n=== 刚性支座+沉降测试 (高度: {pier_heights}) ===")
        
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
        base_height = 8.0
        
        for i, (pier_node, height) in enumerate(zip(self.pier_nodes, pier_heights)):
            if i == 0:
                # 第一个支座：固定
                model.fix(pier_node, 1, 1, 0)
            else:
                # 其他支座：竖向固定
                model.fix(pier_node, 0, 1, 0)
            
            print(f"支座{i+1}: 节点{pier_node}, 高度{height:.1f}m")
        
        # 施加荷载
        model.timeSeries('Linear', 1)
        model.pattern('Plain', 1, 1)
        
        weight_per_length = self.density * 9.81 * self.A
        for element_id, _, _ in self.elements:
            model.eleLoad('-ele', element_id, '-type', '-beamUniform', -weight_per_length)
        
        # 施加强制位移 (模拟支座沉降)
        for i, (pier_node, height) in enumerate(zip(self.pier_nodes, pier_heights)):
            if i > 0:  # 不对第一个支座施加位移
                settlement = (height - base_height) * 0.002  # 沉降系数
                if abs(settlement) > 1e-6:
                    model.load(pier_node, 0.0, 0.0, 0.0)  # 先加载模式
                    model.sp(pier_node, 2, settlement)  # 强制竖向位移
                    print(f"支座{i+1} 沉降: {settlement*1000:.2f}mm")
        
        # 分析
        model.system('ProfileSPD')
        model.numberer('Plain')
        model.constraints('Transformation')
        model.integrator('LoadControl', 1.0)
        model.algorithm('Linear')
        model.analysis('Static')
        
        ok = model.analyze(1)
        
        if ok == 0:
            print("刚性支座+沉降分析收敛成功")
            
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
            print("刚性支座+沉降分析失败")
            return [0.0] * len(self.pier_nodes)
    
    def compare_methods(self):
        """比较不同方法的结果"""
        print("\n" + "="*60)
        print("支座高度效应测试对比")
        print("="*60)
        
        # 先测试参考情况
        ref_reactions = self.test_reference_case()
        
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
            
            # 弹性支座测试
            reactions_elastic = self.test_elastic_supports(case['heights'])
            
            # 刚性支座+沉降测试
            reactions_settlement = self.test_rigid_supports_with_settlement(case['heights'])
            
            results.append({
                'case': case['name'],
                'heights': case['heights'],
                'reference_reactions': ref_reactions,
                'elastic_reactions': reactions_elastic,
                'settlement_reactions': reactions_settlement
            })
        
        # 生成对比表格
        self.generate_comparison_table(results)
        
        # 分析荷载重分布
        self.analyze_load_redistribution(results)
    
    def generate_comparison_table(self, results):
        """生成对比表格"""
        print("\n" + "="*80)
        print("反力对比表 (kN)")
        print("="*80)
        
        for result in results:
            print(f"\n{result['case']} - 支座高度: {result['heights']}")
            print("-" * 70)
            
            # 创建表格
            table_data = {
                '支座': [f'支座{i+1}' for i in range(4)],
                '高度(m)': result['heights'],
                '参考值': [f"{r/1000:.2f}" for r in result['reference_reactions']],
                '弹性支座': [f"{r/1000:.2f}" for r in result['elastic_reactions']],
                '沉降模拟': [f"{r/1000:.2f}" for r in result['settlement_reactions']]
            }
            
            df = pd.DataFrame(table_data)
            print(df.to_string(index=False))
            
            # 计算总反力
            total_ref = sum(result['reference_reactions'])
            total_elastic = sum(result['elastic_reactions'])
            total_settlement = sum(result['settlement_reactions'])
            
            print(f"总反力: 参考={total_ref/1000:.2f}kN, 弹性={total_elastic/1000:.2f}kN, 沉降={total_settlement/1000:.2f}kN")
    
    def analyze_load_redistribution(self, results):
        """分析荷载重分布"""
        print("\n" + "="*80)
        print("荷载重分布分析")
        print("="*80)
        
        ref_reactions = results[0]['reference_reactions']  # 使用均匀高度作为参考
        
        for result in results:
            if result['case'] == '均匀高度':
                continue
                
            print(f"\n{result['case']} 荷载重分布:")
            print("-" * 40)
            
            # 分析弹性支座结果
            elastic_reactions = result['elastic_reactions']
            
            for i in range(4):
                ref_load = ref_reactions[i] / 1000
                elastic_load = elastic_reactions[i] / 1000
                change = elastic_load - ref_load
                change_percent = (change / ref_load * 100) if ref_load != 0 else 0
                
                print(f"支座{i+1}: 参考{ref_load:.2f}kN → 弹性{elastic_load:.2f}kN (变化{change:+.2f}kN, {change_percent:+.1f}%)")

def main():
    """主函数"""
    print("支座高度效应测试程序 (修复版)")
    print("="*50)
    
    # 创建测试桥梁
    bridge = SimpleBridgeTest()
    
    # 运行对比测试
    bridge.compare_methods()
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()
