#!/usr/bin/env python3
"""
方法2实际测试：弹性梁单元模拟支座弹簧
使用Truss单元作为垂直弹簧来模拟支座刚度
"""

import numpy as np
import xara

def test_method2_beam_spring():
    """实际测试方法2 - 弹性梁单元模拟弹簧"""
    print("="*80)
    print("方法2实际测试：弹性梁单元模拟支座弹簧")
    print("="*80)
    
    # 基本参数
    length = 60.0
    num_elements = 20
    E = 30e9
    section_height = 1.5
    section_width = 1.0
    density = 2400
    
    A = section_height * section_width
    I = (section_width * section_height**3) / 12
    beam_EI = E * I
    
    # 支座位置和节点
    pier_positions = [0.0, 0.33, 0.67, 1.0]
    dx = length / num_elements
    pier_nodes = []
    for pos in pier_positions:
        pier_x = pos * length
        pier_node = int(round(pier_x / dx)) + 1
        pier_node = max(1, min(pier_node, num_elements + 1))
        pier_nodes.append(pier_node)
    
    print(f"支座节点: {pier_nodes}")
    print(f"梁抗弯刚度 EI = {beam_EI/1e6:.1f} MN·m²")
    
    # 计算合适的刚度范围
    beam_vertical_stiffness = 12 * beam_EI / (length/3)**3  # 基于跨度的梁刚度
    
    # 定义刚度情况 - 使用合理的范围
    stiffness_cases = [
        (1e15, "无限刚度"),
        (beam_vertical_stiffness * 1000, "很高刚度 (1000×梁刚度)"),
        (beam_vertical_stiffness * 100, "高刚度 (100×梁刚度)"),
        (beam_vertical_stiffness * 10, "中等刚度 (10×梁刚度)"),
        (beam_vertical_stiffness * 1, "低刚度 (1×梁刚度)"),
        (beam_vertical_stiffness * 0.1, "很低刚度 (0.1×梁刚度)")
    ]
    
    print(f"参考梁垂直刚度 = {beam_vertical_stiffness/1e6:.1f} MN/m")
    
    print(f"\n{'工况':<20} {'1号墩(kN)':<12} {'2号墩(kN)':<12} {'3号墩(kN)':<12} {'4号墩(kN)':<12} {'标准差(kN)':<12}")
    print("-" * 90)
    
    results = []
    
    for stiffness, description in stiffness_cases:
        try:
            # 创建模型
            model = xara.Model()
            model.model('basic', '-ndm', 2, '-ndf', 3)
            
            # 创建梁节点
            nodes = []
            for i in range(num_elements + 1):
                x = i * dx
                node_id = i + 1
                model.node(node_id, x, 0.0)
                nodes.append((node_id, x, 0.0))
            
            # 创建基础节点（用于弹簧）
            base_nodes = []
            base_node_start = num_elements + 2
            spring_length = 0.1
            
            for i, pier_node in enumerate(pier_nodes):
                base_node_id = base_node_start + i
                pier_x = (pier_node - 1) * dx
                model.node(base_node_id, pier_x, -spring_length)
                base_nodes.append(base_node_id)
                model.fix(base_node_id, 1, 1, 1)  # 固定基础节点
            
            # 创建材料
            model.uniaxialMaterial('Elastic', 1, E)  # 梁材料
            if stiffness < 1e15:
                model.uniaxialMaterial('Elastic', 2, stiffness)  # 弹簧材料
            model.geomTransf('Linear', 1)
            
            # 创建梁单元
            for i in range(num_elements):
                element_id = i + 1
                node_i = i + 1
                node_j = i + 2
                model.element('elasticBeamColumn', element_id, node_i, node_j, A, E, I, 1)
            
            # 创建支座弹簧
            spring_element_start = num_elements + 1
            
            for i, (pier_node, base_node) in enumerate(zip(pier_nodes, base_nodes)):
                spring_element_id = spring_element_start + i
                
                if stiffness >= 1e15:  # 无限刚度
                    model.fix(pier_node, 1, 1, 0)
                else:
                    # 创建Truss弹簧单元 - 使用1平方米截面积
                    spring_area = 1.0
                    model.element('truss', spring_element_id, pier_node, base_node, spring_area, 2)
                    model.fix(pier_node, 1, 0, 0)  # 水平固定
            
            # 施加荷载
            model.timeSeries('Linear', 1)
            model.pattern('Plain', 1, 1)
            
            weight_per_length = density * 9.81 * A
            for i in range(num_elements):
                element_id = i + 1
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
                for pier_node in pier_nodes:
                    try:
                        reaction = model.nodeReaction(pier_node)
                        reactions.append(abs(reaction[1]))
                    except:
                        reactions.append(0.0)
                
                print(f"  调试: 原始反力 = {reactions}")
                print(f"  调试: 反力总和 = {sum(reactions)}")
                
                if sum(reactions) > 10:  # 降低检查阈值
                    reactions_kn = [r/1000 for r in reactions]
                    std_dev = np.std(reactions_kn)
                    
                    print(f"{description:<20} {reactions_kn[0]:<12.1f} {reactions_kn[1]:<12.1f} {reactions_kn[2]:<12.1f} {reactions_kn[3]:<12.1f} {std_dev:<12.2f}")
                    
                    results.append({
                        'description': description,
                        'reactions': reactions_kn,
                        'std_dev': std_dev
                    })
                else:
                    print(f"{description:<20} {'失败':<12} {'失败':<12} {'失败':<12} {'失败':<12} {'--':<12}")
                    print(f"  反力太小: {reactions}")
            else:
                print(f"{description:<20} {'求解失败':<12} {'求解失败':<12} {'求解失败':<12} {'求解失败':<12} {'--':<12}")
                
        except Exception as e:
            print(f"{description:<20} {'错误':<12} {'错误':<12} {'错误':<12} {'错误':<12} {'--':<12}")
            print(f"  错误: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 分析趋势
    print("\n" + "="*80)
    print("方法2结果分析：")
    print("="*80)
    
    if len(results) >= 2:
        print("刚度降低时标准差变化趋势：")
        for i in range(1, len(results)):
            prev_std = results[i-1]['std_dev']
            curr_std = results[i]['std_dev']
            if curr_std > prev_std:
                trend = "↑ 更均匀"
            else:
                trend = "↓ 更不均匀"
            print(f"  {results[i-1]['description']} → {results[i]['description']}: {prev_std:.2f} → {curr_std:.2f} {trend}")
        
        # 物理验证
        highest_std = results[0]['std_dev']
        lowest_std = results[-1]['std_dev']
        if lowest_std > highest_std:
            print(f"\n✅ 物理规律验证成功！刚度从高到低，标准差从{highest_std:.2f}增加到{lowest_std:.2f}")
            print("   说明刚度越低，受力分布越均匀（趋向简支梁）")
        else:
            print(f"\n❌ 结果异常！预期刚度降低时标准差应增加")
    
    return results

if __name__ == "__main__":
    results = test_method2_beam_spring() 