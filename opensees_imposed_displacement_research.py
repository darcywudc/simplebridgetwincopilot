#!/usr/bin/env python3
"""
OpenSees强制位移研究
研究如何在OpenSees中施加强制位移来模拟墩台高度效应
"""

def research_imposed_displacement():
    """研究OpenSees中的强制位移方法"""
    
    print("OpenSees强制位移方法研究")
    print("=" * 60)
    
    print("\n1. 使用 fix 和 load 组合:")
    print("   - fix(node, 1, 1, 0)  # 固定x,y方向，z方向自由")
    print("   - load(node, 0, 0, imposed_displacement)  # 施加强制位移")
    
    print("\n2. 使用 SP_Constraint (Single Point Constraint):")
    print("   - sp(node, dof, value)  # 直接指定节点自由度的值")
    print("   - 这是最直接的强制位移方法")
    
    print("\n3. 使用 MP_Constraint (Multi Point Constraint):")
    print("   - equalDOF(masterNode, slaveNode, *dofs)  # 多点约束")
    print("   - 可以让多个节点有相同的位移")
    
    print("\n4. 使用 imposedMotion:")
    print("   - imposedMotion(node, dir, gMotionTag)  # 施加强制运动")
    print("   - 通常用于地震分析")
    
    print("\n5. 使用 displacement 积分器:")
    print("   - integrator('DisplacementControl', ...)  # 位移控制分析")
    print("   - 非线性分析中的位移控制")
    
    print("\n=== 墩台高度效应的正确建模方法 ===")
    print("墩台高度差异 → 支座沉降差异 → 强制位移边界条件")
    print("")
    print("建议方案:")
    print("1. 计算相对沉降: settlement = (h_pier - h_reference) * settlement_factor")
    print("2. 使用 sp() 命令施加强制竖向位移")
    print("3. 不改变刚度，只改变边界条件")
    
    print("\n=== 示例代码结构 ===")
    print("""
    # 创建节点
    model.node(node_id, x, y)
    
    # 计算强制位移
    reference_height = 8.0  # 基准高度
    pier_height = 10.0      # 实际高度
    settlement_factor = 0.001  # 沉降系数 (m/m)
    imposed_displacement = (pier_height - reference_height) * settlement_factor
    
    # 施加强制位移边界条件
    model.fix(node_id, 1, 0, 1)  # 固定x和z，y方向施加位移
    model.sp(node_id, 2, imposed_displacement)  # 在y方向施加强制位移
    
    # 或者使用load在静力分析中
    model.load(node_id, 0, 0, 0)  # 先施加零荷载
    # 然后在分析中施加位移
    """)

if __name__ == "__main__":
    research_imposed_displacement()
