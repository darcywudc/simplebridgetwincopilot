#!/usr/bin/env python3
"""
基于OpenSees文档的正确墩台高度效应实现
使用zeroLength元素创建弹簧支座
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bridge_model_enhanced import BridgeModelXara

def create_spring_support_bridge():
    """
    创建一个使用zeroLength弹簧支座的桥梁模型
    根据OpenSees文档的标准做法
    """
    print("基于OpenSees文档的弹簧支座实现方案")
    print("=" * 60)
    
    print("\n1. zeroLength元素的基本原理:")
    print("   - 在同一位置创建两个节点")
    print("   - 节点之间用zeroLength元素连接")
    print("   - 通过材料定义弹簧刚度")
    print("   - 固定下层节点，上层节点连接到结构")
    
    print("\n2. 墩台高度对刚度的影响:")
    print("   - 墩台可以看作竖向弹簧")
    print("   - 刚度K = E*A/L (E-弹性模量, A-截面面积, L-高度)")
    print("   - 墩台越高，刚度越小")
    print("   - 墩台越矮，刚度越大")
    
    print("\n3. 实现步骤:")
    print("   a) 为每个墩台位置创建两个节点")
    print("   b) 计算基于高度的弹簧刚度")
    print("   c) 创建弹性材料")
    print("   d) 创建zeroLength元素")
    print("   e) 固定下层节点")
    
    return demonstrate_spring_stiffness()

def demonstrate_spring_stiffness():
    """演示不同墩台高度的弹簧刚度计算"""
    print("\n=" * 60)
    print("弹簧刚度计算示例")
    print("=" * 60)
    
    # 材料参数 (典型混凝土墩台)
    E = 30e9  # 弹性模量 Pa (30 GPa)
    A = 2.0   # 墩台截面面积 m² (典型1.5m x 1.5m方形墩)
    
    # 不同高度的墩台
    heights = [6.0, 8.0, 10.0, 12.0, 15.0]
    
    print(f"材料参数:")
    print(f"  弹性模量: {E/1e9:.1f} GPa")
    print(f"  截面面积: {A:.1f} m²")
    print()
    
    print("墩台高度对刚度的影响:")
    print("高度(m)  刚度(MN/m)  相对刚度")
    print("-" * 35)
    
    base_height = 8.0
    base_stiffness = E * A / base_height
    
    stiffness_values = []
    for h in heights:
        stiffness = E * A / h
        relative_stiffness = stiffness / base_stiffness
        stiffness_values.append(stiffness)
        print(f"{h:6.1f}   {stiffness/1e6:8.1f}     {relative_stiffness:6.3f}")
    
    print()
    print("观察:")
    print("- 6m高墩台比8m高墩台刚度大33%")
    print("- 12m高墩台比8m高墩台刚度小33%")
    print("- 15m高墩台比8m高墩台刚度小47%")
    print()
    print("这意味着:")
    print("- 矮墩台(高刚度)将承担更多荷载")
    print("- 高墩台(低刚度)将承担更少荷载")
    
    return stiffness_values

def create_opensees_spring_code():
    """生成OpenSees弹簧支座的示例代码"""
    print("\n=" * 60)
    print("OpenSees弹簧支座代码示例")
    print("=" * 60)
    
    code = '''
# 示例：为不同高度的墩台创建弹簧支座

# 材料参数
set E 30e9;     # 弹性模量 Pa
set A 2.0;      # 截面面积 m²

# 墩台高度 (m)
set pier_heights [list 6.0 8.0 10.0 12.0]

# 为每个墩台创建弹簧支座
for {set i 0} {$i < [llength $pier_heights]} {incr i} {
    set pier_id [expr $i + 1]
    set height [lindex $pier_heights $i]
    
    # 计算弹簧刚度
    set stiffness [expr $E * $A / $height]
    
    # 创建节点 (上层节点连接到桥梁，下层节点固定)
    set upper_node [expr $pier_id * 10]      # 上层节点
    set lower_node [expr $pier_id * 10 + 1]  # 下层节点
    
    # 节点位置 (假设在x方向等间距分布)
    set x_pos [expr $i * 20.0]
    
    node $upper_node $x_pos 0.0
    node $lower_node $x_pos 0.0
    
    # 创建弹性材料
    set mat_id [expr $pier_id + 100]
    uniaxialMaterial Elastic $mat_id $stiffness
    
    # 创建zeroLength弹簧元素
    set elem_id [expr $pier_id + 200]
    element zeroLength $elem_id $lower_node $upper_node -mat $mat_id -dir 2
    
    # 固定下层节点
    fix $lower_node 1 1 1
    
    puts "Pier $pier_id: height=${height}m, stiffness=${stiffness}N/m"
}
'''
    
    print(code)
    print("\n关键点:")
    print("1. 每个墩台位置创建两个节点")
    print("2. 弹簧刚度 = E*A/height")
    print("3. zeroLength元素连接上下节点")
    print("4. 下层节点完全固定")
    print("5. 上层节点连接到桥梁结构")

if __name__ == "__main__":
    stiffness_values = create_spring_support_bridge()
    create_opensees_spring_code()
    
    print("\n" + "="*60)
    print("下一步: 在bridge_model_enhanced.py中实现这个方案")
    print("="*60)
