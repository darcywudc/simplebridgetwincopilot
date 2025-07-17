#!/usr/bin/env python3
"""
详细的支座高度逻辑测试
用于诊断支座高度调整的逻辑问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bridge_model_enhanced import BridgeModelXara

def test_pier_height_logic():
    """测试支座高度逻辑的详细分析"""
    print("支座高度效应测试")
    print("=" * 80)
    
    # 基础参数
    length = 60.0
    num_elements = 20
    
    # 测试场景1: 基准情况 - 所有墩台相同高度
    print("\n🔹 基准情况 (所有墩台8m高)")
    bridge1 = BridgeModelXara(
        length=length,
        num_spans=3,
        pier_heights=[8.0, 8.0, 8.0, 8.0],
        num_elements=num_elements
    )
    bridge1.add_point_load(100000, 0.5)  # 100kN at center
    results1 = bridge1.run_analysis()
    reactions1 = results1.get('reactions', [])
    
    print("墩台高度: [8.0, 8.0, 8.0, 8.0]")
    print("支座反力:")
    for i, reaction in enumerate(reactions1):
        print(f"  墩台{i+1}: {reaction['Fy']:.2f}kN")
    
    print("\n" + "=" * 80)
    
    # 测试场景2: 只调高墩台2
    print("\n🔹 墩台2高度调整测试 (8m → 10m)")
    bridge2 = BridgeModelXara(
        length=length,
        num_spans=3,
        pier_heights=[8.0, 10.0, 8.0, 8.0],  # 墩台2变高
        num_elements=num_elements
    )
    bridge2.add_point_load(100000, 0.5)
    results2 = bridge2.run_analysis()
    reactions2 = results2.get('reactions', [])
    
    print("墩台高度: [8.0, 10.0, 8.0, 8.0]")
    print("支座反力:")
    for i, reaction in enumerate(reactions2):
        print(f"  墩台{i+1}: {reaction['Fy']:.2f}kN")
    
    # 直接对比墩台2调高的效果
    print("\n📊 墩台2调高效果对比:")
    print("墩台  |  调整前(kN)  |  调整后(kN)  |  变化(kN)  |  变化率")
    print("-" * 65)
    for i in range(len(reactions1)):
        r1 = reactions1[i]['Fy']
        r2 = reactions2[i]['Fy']
        change = r2 - r1
        change_rate = (change / abs(r1) * 100) if abs(r1) > 0.01 else 0
        status = "📈" if abs(r2) > abs(r1) else "📉" if abs(r2) < abs(r1) else "➡️"
        print(f"墩台{i+1}  |  {r1:>10.2f}  |  {r2:>10.2f}  |  {change:>+8.2f}  |  {change_rate:>+5.1f}% {status}")
    
    # 重点关注调整的墩台
    pier2_change = abs(reactions2[1]['Fy']) - abs(reactions1[1]['Fy'])
    print(f"\n🎯 重点分析 - 墩台2 (调高2m):")
    print(f"   反力绝对值变化: {pier2_change:+.2f}kN")
    if pier2_change > 0:
        print("   ✅ 符合预期: 墩台调高后承担更多荷载")
    else:
        print("   ❌ 不符合预期: 墩台调高后承担荷载减少")
    
    print("\n" + "=" * 80)
    
    # 测试场景3: 只调高墩台3
    print("\n🔹 墩台3高度调整测试 (8m → 10m)")
    bridge3 = BridgeModelXara(
        length=length,
        num_spans=3,
        pier_heights=[8.0, 8.0, 10.0, 8.0],  # 墩台3变高
        num_elements=num_elements
    )
    bridge3.add_point_load(100000, 0.5)
    results3 = bridge3.run_analysis()
    reactions3 = results3.get('reactions', [])
    
    print("墩台高度: [8.0, 8.0, 10.0, 8.0]")
    print("支座反力:")
    for i, reaction in enumerate(reactions3):
        print(f"  墩台{i+1}: {reaction['Fy']:.2f}kN")
    
    # 直接对比墩台3调高的效果
    print("\n📊 墩台3调高效果对比:")
    print("墩台  |  调整前(kN)  |  调整后(kN)  |  变化(kN)  |  变化率")
    print("-" * 65)
    for i in range(len(reactions1)):
        r1 = reactions1[i]['Fy']
        r3 = reactions3[i]['Fy']
        change = r3 - r1
        change_rate = (change / abs(r1) * 100) if abs(r1) > 0.01 else 0
        status = "📈" if abs(r3) > abs(r1) else "📉" if abs(r3) < abs(r1) else "➡️"
        print(f"墩台{i+1}  |  {r1:>10.2f}  |  {r3:>10.2f}  |  {change:>+8.2f}  |  {change_rate:>+5.1f}% {status}")
    
    # 重点关注调整的墩台
    pier3_change = abs(reactions3[2]['Fy']) - abs(reactions1[2]['Fy'])
    print(f"\n🎯 重点分析 - 墩台3 (调高2m):")
    print(f"   反力绝对值变化: {pier3_change:+.2f}kN")
    if pier3_change > 0:
        print("   ✅ 符合预期: 墩台调高后承担更多荷载")
    else:
        print("   ❌ 不符合预期: 墩台调高后承担荷载减少")
    
    print("\n" + "=" * 80)
    
    # 总结分析
    print("\n📋 总结分析:")
    print("物理逻辑: 墩台高度增加 → 支座刚度增大 → 承担更多荷载")
    print("")
    
    success_count = 0
    if pier2_change > 0:
        print("✅ 墩台2调高测试: 通过")
        success_count += 1
    else:
        print("❌ 墩台2调高测试: 失败")
    
    if pier3_change > 0:
        print("✅ 墩台3调高测试: 通过")
        success_count += 1
    else:
        print("❌ 墩台3调高测试: 失败")
    
    print(f"\n🎯 测试结果: {success_count}/2 通过")
    
    if success_count == 2:
        print("🎉 所有测试通过! 墩台高度效应实现正确!")
    else:
        print("⚠️  部分测试失败, 需要进一步调整实现方法")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_pier_height_logic()
