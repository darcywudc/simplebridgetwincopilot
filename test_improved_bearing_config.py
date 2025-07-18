#!/usr/bin/env python3
"""
测试改进的独立支座配置功能 - 新编号系统
Test Improved Individual Bearing Configuration - New ID System
"""

import numpy as np
import pandas as pd
from bridge_model_enhanced import BridgeModelXara

def test_improved_bearing_id_system():
    """测试改进的支座编号系统"""
    
    print("🚀 测试改进的支座编号系统")
    print("=" * 60)
    
    # 创建桥梁模型
    bridge = BridgeModelXara(
        length=60.0,
        num_spans=3,
        bearings_per_pier=2,  # 每个墩台2个支座
        bridge_width=15.0
    )
    
    print(f"📊 桥梁配置:")
    print(f"   - 桥梁长度: {bridge.length}m")
    print(f"   - 跨数: {bridge.num_spans}")
    print(f"   - 墩台数: {bridge.num_piers}")
    print(f"   - 每墩支座数: {bridge.bearings_per_pier}")
    print(f"   - 总支座数: {len(bridge.individual_bearings)}")
    print()
    
    # 显示默认配置（所有支座在同一水平面）
    print("📋 默认支座配置 (高度偏移=0，同一水平面):")
    bearing_summary = bridge.get_individual_bearing_summary()
    print(bearing_summary.to_string(index=False))
    print()
    
    # 测试新的编号系统配置
    print("🔧 使用新编号系统配置支座:")
    print("   支座编号格式: 墩台纵向编号-横向编号")
    print()
    
    # 配置墩台1的支座
    print("   配置墩台1 (pier_id=1):")
    bridge.configure_bearing_height_offset(1, 1, 0.002)  # 支座1-1: +2mm
    bridge.configure_bearing_height_offset(1, 2, 0.003)  # 支座1-2: +3mm
    print("     支座1-1: +2mm")
    print("     支座1-2: +3mm")
    print()
    
    # 配置墩台2的支座
    print("   配置墩台2 (pier_id=2):")
    bridge.configure_pier_bearings_height_offset(2, [0.005, 0.001])  # 批量配置
    print("     支座2-1: +5mm")
    print("     支座2-2: +1mm")
    print()
    
    # 配置墩台3的支座（使用随机变化）
    print("   配置墩台3 (pier_id=3) - 随机变化:")
    bridge.set_bearing_heights_with_variation(3, base_height_offset=0.008, variation_std=0.001)
    print("     基准偏移: +8mm ± 1mm")
    print()
    
    # 配置墩台4的支座类型和参数
    print("   配置墩台4 (pier_id=4) - 支座类型和参数:")
    bridge.configure_individual_bearing(4, 1, 
                                       height_offset=0.000,
                                       support_type={'type': 'fixed', 'dx': 1, 'dy': 1, 'rz': 1},
                                       material='steel',
                                       bearing_type='spherical',
                                       size='large')
    bridge.configure_individual_bearing(4, 2, 
                                       height_offset=0.004,
                                       material='rubber',
                                       bearing_type='elastomeric',
                                       size='medium')
    print("     支座4-1: 固定支座, 钢材, 球形支座, 大型")
    print("     支座4-2: 标准支座, 橡胶, 板式支座, 中型")
    print()
    
    # 显示最终配置
    print("📋 最终支座配置:")
    final_summary = bridge.get_individual_bearing_summary()
    print(final_summary.to_string(index=False))
    print()
    
    # 分析支座配置
    print("📊 支座配置分析:")
    heights = [b['height'] for b in bridge.individual_bearings]
    offsets = [b['height_offset'] for b in bridge.individual_bearings]
    
    print(f"   高度统计:")
    print(f"     最高支座: {max(heights):.4f}m")
    print(f"     最低支座: {min(heights):.4f}m")
    print(f"     平均高度: {np.mean(heights):.4f}m")
    print(f"     高度差范围: {max(heights) - min(heights):.4f}m ({(max(heights) - min(heights))*1000:.1f}mm)")
    print()
    
    print(f"   偏移统计:")
    print(f"     最大偏移: {max(offsets)*1000:.1f}mm")
    print(f"     最小偏移: {min(offsets)*1000:.1f}mm")
    print(f"     平均偏移: {np.mean(offsets)*1000:.1f}mm")
    print(f"     偏移标准差: {np.std(offsets)*1000:.1f}mm")
    print()
    
    return bridge

def test_bearing_info_retrieval():
    """测试支座信息获取功能"""
    
    print("🔍 测试支座信息获取功能")
    print("=" * 60)
    
    # 使用前面配置的桥梁
    bridge = test_improved_bearing_id_system()
    
    print("📋 按墩台查询支座信息:")
    for pier_id in range(1, bridge.num_piers + 1):
        pier_bearings = bridge.get_individual_bearing_info(pier_id=pier_id)
        print(f"   墩台{pier_id}: {len(pier_bearings)}个支座")
        for bearing in pier_bearings:
            print(f"     支座{bearing['bearing_id']}: "
                  f"偏移={bearing['height_offset']*1000:.1f}mm, "
                  f"高度={bearing['height']:.4f}m, "
                  f"类型={bearing['support_type']['type']}")
    print()
    
    # 查询特定支座
    print("🔍 查询特定支座:")
    specific_bearing = bridge.get_individual_bearing_info(pier_id=2, bearing_id=1)
    if specific_bearing:
        bearing = specific_bearing[0]
        print(f"   支座2-1详细信息:")
        print(f"     纵向位置: {bearing['pier_x']:.2f}m")
        print(f"     横向位置: {bearing['pier_y']:.2f}m")
        print(f"     基准高度: {bearing['base_height']:.4f}m")
        print(f"     高度偏移: {bearing['height_offset']*1000:.1f}mm")
        print(f"     最终高度: {bearing['height']:.4f}m")
        print(f"     支座类型: {bearing['support_type']['type']}")
        print(f"     支座型式: {bearing['parameters']['type']}")
        print(f"     材质: {bearing['parameters']['material']}")
    print()
    
    return bridge

def test_structural_analysis():
    """测试结构分析功能"""
    
    print("⚡ 测试结构分析功能")
    print("=" * 60)
    
    # 使用配置好的桥梁
    bridge = test_bearing_info_retrieval()
    
    try:
        # 添加荷载
        bridge.add_point_load(-150000, 0.3)  # 150kN at 30% span
        bridge.add_point_load(-100000, 0.7)  # 100kN at 70% span
        
        # 运行分析
        print("🔧 运行结构分析...")
        results = bridge.run_analysis()
        
        if results['analysis_ok']:
            print("✅ 分析成功完成")
            print(f"   最大位移: {results['max_displacement']*1000:.2f}mm")
            print(f"   最大弯矩: {results['max_moment']/1000:.2f}kN·m")
            print(f"   最大剪力: {results['max_shear']/1000:.2f}kN")
            print(f"   最大反力: {results['max_reaction_vertical']/1000:.2f}kN")
            print()
            
            # 详细的支座反力分析
            print("📊 支座反力分析:")
            total_reaction = 0
            for i, reaction in enumerate(results['reactions']):
                pier_id = i + 1
                pier_bearings = bridge.get_individual_bearing_info(pier_id=pier_id)
                
                print(f"   墩台{pier_id}: 反力={reaction['Fy']/1000:.1f}kN")
                print(f"     支座数: {len(pier_bearings)}")
                for bearing in pier_bearings:
                    avg_reaction = reaction['Fy'] / len(pier_bearings)  # 简化：假设均匀分布
                    print(f"     支座{bearing['bearing_id']}: "
                          f"反力≈{avg_reaction/1000:.1f}kN, "
                          f"偏移={bearing['height_offset']*1000:.1f}mm")
                
                total_reaction += reaction['Fy']
            
            print(f"   总反力: {total_reaction/1000:.1f}kN")
            print(f"   荷载验证: {(150+100+bridge.density*9.81*bridge.A*bridge.length/1000):.1f}kN")
            
        else:
            print("❌ 分析失败")
            print(f"   错误: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ 分析过程中出错: {e}")
    
    print()

def main():
    """主测试函数"""
    
    print("🎯 改进的独立支座配置系统测试")
    print("=" * 60)
    print()
    
    # 运行所有测试
    test_improved_bearing_id_system()
    test_bearing_info_retrieval()
    test_structural_analysis()
    
    print("🎉 所有测试完成!")
    print()
    print("💡 改进要点:")
    print("   ✅ 支座编号系统: 纵向编号-横向编号 (如: 1-1, 2-2)")
    print("   ✅ 高度偏移配置: 默认0表示同一水平面")
    print("   ✅ 基准+偏移模式: 基准高度 + 高度偏移 = 最终高度")
    print("   ✅ 支座参数配置: 材质、型式、规格等")
    print("   ✅ 批量配置功能: 整个墩台的支座配置")
    print("   ✅ 精确信息查询: 按墩台或按支座查询")
    print("=" * 60)

if __name__ == "__main__":
    main()
