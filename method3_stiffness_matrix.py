#!/usr/bin/env python3
"""
方法3实际测试：刚度矩阵直接修改
直接在全局刚度矩阵中添加支座刚度项
"""

import numpy as np

def test_method3_stiffness_matrix():
    """实际测试方法3 - 刚度矩阵直接修改"""
    print("="*80)
    print("方法3实际测试：刚度矩阵直接修改")
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
    
    # 支座位置
    pier_positions = [0.0, 0.33, 0.67, 1.0]
    dx = length / num_elements
    pier_nodes = []
    for pos in pier_positions:
        pier_x = pos * length
        pier_node = int(round(pier_x / dx))
        pier_node = max(0, min(pier_node, num_elements))
        pier_nodes.append(pier_node)
    
    print(f"支座节点: {pier_nodes}")
    print(f"梁抗弯刚度 EI = {beam_EI/1e6:.1f} MN·m²")
    
    # 构建刚度矩阵
    num_nodes = num_elements + 1
    num_dof = num_nodes * 3  # 每个节点3个自由度
    
    def build_stiffness_matrix():
        K = np.zeros((num_dof, num_dof))
        EI = E * I
        EA = E * A
        
        # 梁单元刚度矩阵
        k_elem = np.array([
            [EA/dx,    0,          0,         -EA/dx,   0,          0        ],
            [0,        12*EI/dx**3, 6*EI/dx**2, 0,      -12*EI/dx**3, 6*EI/dx**2],
            [0,        6*EI/dx**2,  4*EI/dx,    0,      -6*EI/dx**2,  2*EI/dx   ],
            [-EA/dx,   0,          0,          EA/dx,   0,          0        ],
            [0,       -12*EI/dx**3,-6*EI/dx**2, 0,       12*EI/dx**3,-6*EI/dx**2],
            [0,        6*EI/dx**2,  2*EI/dx,    0,      -6*EI/dx**2,  4*EI/dx   ]
        ])
        
        # 组装总刚度矩阵
        for i in range(num_elements):
            node_i = i
            node_j = i + 1
            dofs_i = [node_i*3, node_i*3+1, node_i*3+2]
            dofs_j = [node_j*3, node_j*3+1, node_j*3+2]
            all_dofs = dofs_i + dofs_j
            
            for p in range(6):
                for q in range(6):
                    K[all_dofs[p], all_dofs[q]] += k_elem[p, q]
        
        return K
    
    def build_load_vector():
        F = np.zeros(num_dof)
        weight_per_length = density * 9.81 * A
        
        # 均布荷载的等效节点力
        for i in range(num_elements):
            node_i = i
            node_j = i + 1
            F_elem = weight_per_length * dx / 2
            
            F[node_i*3 + 1] += F_elem  # y方向
            F[node_j*3 + 1] += F_elem
        
        return F
    
    def apply_support_conditions(K, F, support_stiffnesses):
        K_mod = K.copy()
        F_mod = F.copy()
        
        for i, (node_idx, stiffness) in enumerate(zip(pier_nodes, support_stiffnesses)):
            # 水平约束 - 固定
            u_dof = node_idx * 3
            K_mod[u_dof, :] = 0
            K_mod[:, u_dof] = 0
            K_mod[u_dof, u_dof] = 1e15
            F_mod[u_dof] = 0
            
            # 垂直支座刚度
            v_dof = node_idx * 3 + 1
            if stiffness >= 1e15:  # 无限刚度 - 固定
                K_mod[v_dof, :] = 0
                K_mod[:, v_dof] = 0
                K_mod[v_dof, v_dof] = 1e15
                F_mod[v_dof] = 0
            else:
                # 有限刚度 - 添加弹簧刚度
                K_mod[v_dof, v_dof] += stiffness
        
        return K_mod, F_mod
    
    # 计算合适的刚度范围
    # 梁的垂直刚度参考值
    beam_vertical_stiffness = 12 * beam_EI / (length/3)**3  # 基于跨度的梁刚度
    
    # 定义刚度情况 - 使用更合理的范围
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
            # 构建系统
            K_original = build_stiffness_matrix()
            F_original = build_load_vector()
            
            # 应用支座条件
            support_stiffnesses = [stiffness] * 4
            K, F = apply_support_conditions(K_original, F_original, support_stiffnesses)
            
            # 检查矩阵条件数
            cond_num = np.linalg.cond(K)
            if cond_num > 1e12:
                print(f"{description:<20} {'矩阵病态':<12} {'矩阵病态':<12} {'矩阵病态':<12} {'矩阵病态':<12} {'--':<12}")
                continue
            
            # 求解
            displacements = np.linalg.solve(K, F)
            
            # 计算反力 = K_original * u - F_external
            F_total = K_original @ displacements
            reactions_vec = F_total - F_original
            
            # 提取支座反力
            reactions = []
            for node_idx in pier_nodes:
                v_dof = node_idx * 3 + 1
                reactions.append(abs(reactions_vec[v_dof]))
            
            # 检查力平衡
            total_reaction = sum(reactions)
            total_load = sum(F_original[1::3])  # 所有y方向荷载
            
            if abs(total_reaction - abs(total_load)) / abs(total_load) < 0.1:  # 10%误差内
                reactions_kn = [r/1000 for r in reactions]
                std_dev = np.std(reactions_kn)
                
                print(f"{description:<20} {reactions_kn[0]:<12.1f} {reactions_kn[1]:<12.1f} {reactions_kn[2]:<12.1f} {reactions_kn[3]:<12.1f} {std_dev:<12.2f}")
                
                results.append({
                    'description': description,
                    'reactions': reactions_kn,
                    'std_dev': std_dev
                })
            else:
                print(f"{description:<20} {'力不平衡':<12} {'力不平衡':<12} {'力不平衡':<12} {'力不平衡':<12} {'--':<12}")
                print(f"  荷载={abs(total_load)/1000:.1f}kN, 反力={total_reaction/1000:.1f}kN")
                
        except Exception as e:
            print(f"{description:<20} {'错误':<12} {'错误':<12} {'错误':<12} {'错误':<12} {'--':<12}")
            print(f"  错误: {str(e)[:50]}")
    
    # 分析趋势
    print("\n" + "="*80)
    print("方法3结果分析：")
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
    results = test_method3_stiffness_matrix() 