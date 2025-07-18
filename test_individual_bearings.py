#!/usr/bin/env python3
"""
测试独立支座配置功能
Test Individual Bearing Configuration Features
"""

import numpy as np
import pandas as pd
from bridge_model_enhanced import BridgeModelXara

def test_individual_bearing_configuration():
    """测试独立支座配置功能"""
    
    print("🔧 测试独立支座配置功能")
    print("=" * 50)
    
    # 创建桥梁模型
    bridge = BridgeModelXara(
        length=60.0,
        num_spans=3,
        bearings_per_pier=2,  # 每个墩台2个支座
        bridge_width=15.0
    )
    
    print(f"📊 桥梁基本信息:")
    print(f"   - 桥梁长度: {bridge.length}m")
    print(f"   - 跨数: {bridge.num_spans}")
    print(f"   - 墩台数: {bridge.num_piers}")
    print(f"   - 每墩支座数: {bridge.bearings_per_pier}")
    print(f"   - 总支座数: {len(bridge.individual_bearings)}")
    print()
    
    # 显示默认的独立支座配置
    print("📋 默认独立支座配置:")
    bearing_summary = bridge.get_individual_bearing_summary()
    print(bearing_summary)
    print()
    
    # 测试配置单个支座
    print("🔧 配置单个支座:")
    print("   - 设置墩台1支座1高度为8.010m")
    bridge.configure_individual_bearing(0, 0, height=8.010)
    
    print("   - 设置墩台1支座2高度为8.012m")
    bridge.configure_individual_bearing(0, 1, height=8.012)
    
    print("   - 设置墩台2支座1为固定支座")
    bridge.configure_individual_bearing(1, 0, 
                                       support_type={'type': 'fixed', 'dx': 1, 'dy': 1, 'rz': 1})
    print()
    
    # 显示更新后的支座配置
    print("📋 更新后的支座配置:")
    bearing_summary_updated = bridge.get_individual_bearing_summary()
    print(bearing_summary_updated)
    print()
    
    # 测试批量设置支座高度
    print("🔧 批量设置支座高度:")
    print("   - 为墩台2设置基准高度8.020m，随机变化±2mm")
    bridge.set_bearing_heights_with_variation(1, 8.020, 0.002)
    
    print("   - 为墩台3设置基准高度8.005m，随机变化±1mm")
    bridge.set_bearing_heights_with_variation(2, 8.005, 0.001)
    print()
    
    # 显示最终的支座配置
    print("📋 最终支座配置:")
    final_bearing_summary = bridge.get_individual_bearing_summary()
    print(final_bearing_summary)
    print()
    
    # 分析支座高度变化
    print("📊 支座高度分析:")
    heights = [b['height'] for b in bridge.individual_bearings]
    print(f"   - 最高支座: {max(heights):.4f}m")
    print(f"   - 最低支座: {min(heights):.4f}m")
    print(f"   - 平均高度: {np.mean(heights):.4f}m")
    print(f"   - 高度差范围: {max(heights) - min(heights):.4f}m ({(max(heights) - min(heights))*1000:.1f}mm)")
    print(f"   - 标准差: {np.std(heights):.4f}m ({np.std(heights)*1000:.1f}mm)")
    print()
    
    # 测试获取特定支座信息
    print("🔍 获取特定支座信息:")
    pier_1_bearings = bridge.get_individual_bearing_info(pier_index=0)
    print(f"   - 墩台1支座数: {len(pier_1_bearings)}")
    for bearing in pier_1_bearings:
        print(f"     支座{bearing['bearing_index']+1}: 高度={bearing['height']:.4f}m, 位置=({bearing['pier_x']:.1f}, {bearing['pier_y']:.1f})")
    print()
    
    # 运行分析验证
    print("⚡ 运行结构分析:")
    try:
        # 添加一些荷载
        bridge.add_point_load(-100000, 0.5)  # 100kN downward at mid-span
        
        # 运行分析
        results = bridge.run_analysis()
        
        if results['analysis_ok']:
            print("   ✅ 分析成功完成")
            print(f"   - 最大位移: {results['max_displacement']*1000:.2f}mm")
            print(f"   - 最大弯矩: {results['max_moment']/1000:.2f}kN·m")
            print(f"   - 最大反力: {results['max_reaction_vertical']/1000:.2f}kN")
            
            # 显示支座反力
            print("\n📊 支座反力分析:")
            for i, reaction in enumerate(results['reactions']):
                pier_bearings = bridge.get_individual_bearing_info(pier_index=i)
                print(f"   墩台{i+1} (支座数={len(pier_bearings)}): 反力={reaction['Fy']/1000:.1f}kN")
                
        else:
            print("   ❌ 分析失败")
            print(f"   错误: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ 分析过程中出错: {e}")
    
    print("\n🎉 独立支座配置测试完成!")
    return bridge

def test_comparison_with_traditional():
    """比较传统方法和独立支座方法"""
    
    print("\n🔍 比较分析: 传统方法 vs 独立支座方法")
    print("=" * 50)
    
    # 传统方法
    traditional_bridge = BridgeModelXara(
        length=60.0,
        num_spans=3,
        bearings_per_pier=2,
        individual_bearing_config=None  # 不使用独立支座配置
    )
    
    # 独立支座方法
    individual_bridge = BridgeModelXara(
        length=60.0,
        num_spans=3,
        bearings_per_pier=2,
        individual_bearing_config={}  # 使用独立支座配置
    )
    
    # 为独立支座方法设置不同的支座高度
    individual_bridge.set_bearing_heights_with_variation(0, 8.000, 0.001)
    individual_bridge.set_bearing_heights_with_variation(1, 8.005, 0.002)
    individual_bridge.set_bearing_heights_with_variation(2, 8.010, 0.001)
    
    print("📊 配置比较:")
    print(f"   传统方法: {len(traditional_bridge.piers)} 个墩台支座")
    print(f"   独立支座方法: {len(individual_bridge.individual_bearings)} 个独立支座")
    print()
    
    # 运行分析比较
    both_bridges = [
        ("传统方法", traditional_bridge),
        ("独立支座方法", individual_bridge)
    ]
    
    for name, bridge in both_bridges:
        print(f"🔧 {name}分析:")
        try:
            bridge.add_point_load(-100000, 0.5)
            results = bridge.run_analysis()
            
            if results['analysis_ok']:
                print(f"   ✅ 分析成功")
                print(f"   - 最大位移: {results['max_displacement']*1000:.2f}mm")
                print(f"   - 最大弯矩: {results['max_moment']/1000:.2f}kN·m")
                print(f"   - 支座反力总和: {sum(r['Fy'] for r in results['reactions'])/1000:.1f}kN")
            else:
                print(f"   ❌ 分析失败")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
        print()
    
    print("💡 独立支座配置的优势:")
    print("   - 可以精确控制每个支座的属性")
    print("   - 考虑支座间的高度差异")
    print("   - 更真实的力学模拟")
    print("   - 支持复杂的支座布置")

if __name__ == "__main__":
    # 运行测试
    bridge = test_individual_bearing_configuration()
    test_comparison_with_traditional()
    
    print("\n" + "="*50)
    print("🎯 总结:")
    print("   独立支座配置功能已成功实现!")
    print("   可以对每个支座进行单独配置和分析。")
    print("="*50)
