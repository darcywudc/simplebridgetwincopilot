#!/usr/bin/env python3
"""
简单的支座高度效应测试
测试支座高度调整是否真正影响支座反力分布
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bridge_model_enhanced import BridgeModelXara

def test_pier_height_effects():
    """测试支座高度效应"""
    print("支座高度效应测试 (简化版)")
    print("=" * 60)
    
    # 基础参数
    length = 60.0  # 60米桥梁
    num_elements = 20
    
    # 测试场景1: 均匀高度
    print("\n=== 测试场景1: 均匀高度 ===")
    pier_heights_1 = [8.0, 8.0, 8.0, 8.0]
    bridge1 = BridgeModelXara(
        length=length,
        num_spans=3,
        pier_start_position=0.0,
        pier_heights=pier_heights_1,
        num_elements=num_elements
    )
    
    # 添加一个简单的点荷载
    bridge1.add_point_load(100000, 0.5)  # 100kN at center
    
    # 运行分析
    results1 = bridge1.run_analysis()
    
    # 提取支座反力
    reactions1 = results1.get('reactions', [])
    print(f"支座高度: {pier_heights_1}")
    print("支座反力:")
    for i, reaction in enumerate(reactions1):
        print(f"  支座{i+1}: {reaction['Fy']:.2f} kN")
    
    # 测试场景2: 中间支座较低
    print("\n=== 测试场景2: 中间支座较低 ===")
    pier_heights_2 = [8.0, 6.0, 6.0, 8.0]
    bridge2 = BridgeModelXara(
        length=length,
        num_spans=3,
        pier_start_position=0.0,
        pier_heights=pier_heights_2,
        num_elements=num_elements
    )
    
    # 添加相同的点荷载
    bridge2.add_point_load(100000, 0.5)  # 100kN at center
    
    # 运行分析
    results2 = bridge2.run_analysis()
    
    # 提取支座反力
    reactions2 = results2.get('reactions', [])
    print(f"支座高度: {pier_heights_2}")
    print("支座反力:")
    for i, reaction in enumerate(reactions2):
        print(f"  支座{i+1}: {reaction['Fy']:.2f} kN")
    
    # 比较反力变化
    print("\n=== 反力变化对比 ===")
    print("场景1 (均匀) → 场景2 (中间低)")
    for i in range(len(reactions1)):
        r1 = reactions1[i]['Fy']
        r2 = reactions2[i]['Fy']
        change = r2 - r1
        percent = (change / r1 * 100) if r1 != 0 else 0
        print(f"  支座{i+1}: {r1:.2f} → {r2:.2f} kN (变化: {change:+.2f} kN, {percent:+.1f}%)")
    
    # 测试场景3: 端支座较高
    print("\n=== 测试场景3: 端支座较高 ===")
    pier_heights_3 = [10.0, 8.0, 8.0, 10.0]
    bridge3 = BridgeModelXara(
        length=length,
        num_spans=3,
        pier_start_position=0.0,
        pier_heights=pier_heights_3,
        num_elements=num_elements
    )
    
    # 添加相同的点荷载
    bridge3.add_point_load(100000, 0.5)  # 100kN at center
    
    # 运行分析
    results3 = bridge3.run_analysis()
    
    # 提取支座反力
    reactions3 = results3.get('reactions', [])
    print(f"支座高度: {pier_heights_3}")
    print("支座反力:")
    for i, reaction in enumerate(reactions3):
        print(f"  支座{i+1}: {reaction['Fy']:.2f} kN")
    
    # 比较反力变化
    print("\n=== 反力变化对比 ===")
    print("场景1 (均匀) → 场景3 (端高)")
    for i in range(len(reactions1)):
        r1 = reactions1[i]['Fy']
        r3 = reactions3[i]['Fy']
        change = r3 - r1
        percent = (change / r1 * 100) if r1 != 0 else 0
        print(f"  支座{i+1}: {r1:.2f} → {r3:.2f} kN (变化: {change:+.2f} kN, {percent:+.1f}%)")
    
    # 总结
    print("\n=== 测试总结 ===")
    total_reactions = [
        sum(r['Fy'] for r in reactions1),
        sum(r['Fy'] for r in reactions2),
        sum(r['Fy'] for r in reactions3)
    ]
    print(f"总反力 - 场景1: {total_reactions[0]:.2f} kN")
    print(f"总反力 - 场景2: {total_reactions[1]:.2f} kN")
    print(f"总反力 - 场景3: {total_reactions[2]:.2f} kN")
    
    # 检查是否有意义的变化
    max_change = 0
    for i in range(len(reactions1)):
        r1 = reactions1[i]['Fy']
        r2 = reactions2[i]['Fy']
        r3 = reactions3[i]['Fy']
        change2 = abs(r2 - r1)
        change3 = abs(r3 - r1)
        max_change = max(max_change, change2, change3)
    
    if max_change > 1.0:  # 超过1kN的变化
        print(f"✅ 支座高度效应正常工作! 最大反力变化: {max_change:.2f} kN")
    else:
        print(f"❌ 支座高度效应可能没有生效! 最大反力变化: {max_change:.2f} kN")

if __name__ == "__main__":
    test_pier_height_effects()
