#!/usr/bin/env python3
"""
测试不同支座刚度和梁刚度组合下0.1厘米沉降对支座反力的影响
"""

import numpy as np
import pandas as pd
from bridge_model_enhanced import BridgeModelXara

def test_stiffness_combinations_with_settlement():
    """测试不同刚度组合下的沉降效应"""
    print("="*100)
    print("支座刚度 × 梁刚度组合下的0.1厘米沉降效应分析")
    print("="*100)
    
    # 基础参数
    bridge_length = 60.0
    num_elements = 20
    base_E = 30e9  # 基础弹性模量30GPa
    section_height = 1.5
    section_width = 1.0
    density = 2400
    
    # 定义梁刚度组合（通过改变弹性模量）
    beam_stiffness_configs = {
        '低刚度梁': {'E': base_E * 0.5, 'description': '0.5×标准刚度(软梁)'},
        '标准刚度梁': {'E': base_E, 'description': '1.0×标准刚度(正常梁)'},
        '高刚度梁': {'E': base_E * 2.0, 'description': '2.0×标准刚度(硬梁)'}
    }
    
    # 定义支座刚度配置（通过修改支座约束和刚度矩阵）
    support_stiffness_configs = {
        '刚性支座': {
            'support_types': [
                {'type': 'fixed_pin', 'dx': 1, 'dy': 1, 'rz': 0},
                {'type': 'fixed', 'dx': 1, 'dy': 1, 'rz': 1},  # 更刚
                {'type': 'fixed', 'dx': 1, 'dy': 1, 'rz': 1},  # 更刚
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0}
            ],
            'description': '高约束支座(接近固定)'
        },
        '标准支座': {
            'support_types': [
                {'type': 'fixed_pin', 'dx': 1, 'dy': 1, 'rz': 0},
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0},
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0},
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0}
            ],
            'description': '标准约束支座(常规设计)'
        },
        '柔性支座': {
            'support_types': [
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0},  # 更柔
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0},
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0},
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0}
            ],
            'description': '低约束支座(仅竖向约束)'
        }
    }
    
    # 原始和修改后的墩台高度
    original_heights = [8.000, 8.005, 8.015, 8.003]
    modified_heights = original_heights.copy()
    modified_heights[1] += 0.001  # 2号墩增加0.1厘米
    
    print(f"📏 测试条件：2号墩高度从 {original_heights[1]:.3f}m 增加到 {modified_heights[1]:.3f}m (+0.1厘米)")
    print(f"🌉 桥梁配置：{bridge_length}m长，{num_elements}个单元，3跨连续梁")
    
    # 存储所有组合的结果
    all_results = []
    
    # 遍历所有刚度组合
    for beam_name, beam_config in beam_stiffness_configs.items():
        for support_name, support_config in support_stiffness_configs.items():
            
            print(f"\n" + "="*80)
            print(f"🔧 测试组合：{beam_name} × {support_name}")
            print(f"   梁刚度：{beam_config['description']}")
            print(f"   支座：{support_config['description']}")
            print("="*80)
            
            # 创建原始模型
            bridge_original = BridgeModelXara(
                length=bridge_length,
                num_elements=num_elements,
                E=beam_config['E'],
                section_height=section_height,
                section_width=section_width,
                density=density,
                num_spans=3,
                pier_heights=original_heights,
                support_types=support_config['support_types']
            )
            
            # 添加荷载
            bridge_original.add_distributed_load(-50000)  # 50 kN/m
            bridge_original.add_point_load(-200000, 0.3)  # 200 kN at 30%
            bridge_original.add_point_load(-200000, 0.7)  # 200 kN at 70%
            
            # 创建修改后模型
            bridge_modified = BridgeModelXara(
                length=bridge_length,
                num_elements=num_elements,
                E=beam_config['E'],
                section_height=section_height,
                section_width=section_width,
                density=density,
                num_spans=3,
                pier_heights=modified_heights,
                support_types=support_config['support_types']
            )
            
            # 添加相同荷载
            bridge_modified.add_distributed_load(-50000)
            bridge_modified.add_point_load(-200000, 0.3)
            bridge_modified.add_point_load(-200000, 0.7)
            
            # 运行分析
            try:
                results_original = bridge_original.run_analysis()
                results_modified = bridge_modified.run_analysis()
                
                if results_original['analysis_ok'] and results_modified['analysis_ok']:
                    # 计算反力变化
                    reactions_orig = results_original['reactions']
                    reactions_mod = results_modified['reactions']
                    
                    reaction_changes = []
                    for i in range(len(reactions_orig)):
                        orig_force = reactions_orig[i]['Fy'] / 1000  # kN
                        mod_force = reactions_mod[i]['Fy'] / 1000   # kN
                        change = mod_force - orig_force
                        change_rate = (change / orig_force * 100) if orig_force != 0 else 0
                        reaction_changes.append({
                            'pier': i+1,
                            'original': orig_force,
                            'modified': mod_force,
                            'change': change,
                            'change_rate': change_rate
                        })
                    
                    # 计算整体指标
                    total_change = sum(abs(r['change']) for r in reaction_changes)
                    max_change = max(abs(r['change']) for r in reaction_changes)
                    max_change_rate = max(abs(r['change_rate']) for r in reaction_changes)
                    
                    # 计算梁的相对刚度
                    beam_EI = beam_config['E'] * (section_width * section_height**3) / 12
                    relative_beam_stiffness = beam_config['E'] / base_E
                    
                    # 存储结果
                    result = {
                        'beam_type': beam_name,
                        'support_type': support_name,
                        'beam_stiffness_ratio': relative_beam_stiffness,
                        'beam_EI': beam_EI / 1e9,  # GN⋅m²
                        'reaction_changes': reaction_changes,
                        'total_change': total_change,
                        'max_change': max_change,
                        'max_change_rate': max_change_rate,
                        'sensitivity': total_change / 0.1,  # 每毫米沉降的总反力变化
                        'analysis_ok': True
                    }
                    all_results.append(result)
                    
                    # 打印详细结果
                    print(f"📊 支座反力变化详情：")
                    print(f"{'墩台':<6} {'原始(kN)':<12} {'修改后(kN)':<12} {'变化(kN)':<12} {'变化率(%)':<10}")
                    print("-" * 60)
                    for r in reaction_changes:
                        print(f"{r['pier']}号墩   {r['original']:<12.2f} {r['modified']:<12.2f} {r['change']:<12.3f} {r['change_rate']:<10.3f}")
                    
                    print(f"\n📈 敏感性指标：")
                    print(f"   总变化量：{total_change:.3f} kN")
                    print(f"   最大变化：{max_change:.3f} kN")
                    print(f"   最大变化率：{max_change_rate:.3f}%")
                    print(f"   敏感度：{total_change/0.1:.2f} kN/mm")
                    
                else:
                    print("❌ 分析失败")
                    all_results.append({
                        'beam_type': beam_name,
                        'support_type': support_name,
                        'analysis_ok': False,
                        'error': '分析未收敛'
                    })
                    
            except Exception as e:
                print(f"❌ 分析出错：{e}")
                all_results.append({
                    'beam_type': beam_name,
                    'support_type': support_name,
                    'analysis_ok': False,
                    'error': str(e)
                })
    
    # 综合分析结果
    print(f"\n" + "="*100)
    print("🎯 综合分析结果")
    print("="*100)
    
    successful_results = [r for r in all_results if r.get('analysis_ok', False)]
    
    if successful_results:
        # 创建敏感性对比表
        print(f"\n📊 敏感性对比表：")
        print(f"{'梁刚度':<12} {'支座类型':<12} {'总变化(kN)':<12} {'最大变化(kN)':<12} {'敏感度(kN/mm)':<15}")
        print("-" * 75)
        
        for result in successful_results:
            print(f"{result['beam_type']:<12} {result['support_type']:<12} "
                  f"{result['total_change']:<12.3f} {result['max_change']:<12.3f} "
                  f"{result['sensitivity']:<15.2f}")
        
        # 找出最敏感和最不敏感的组合
        most_sensitive = max(successful_results, key=lambda x: x['sensitivity'])
        least_sensitive = min(successful_results, key=lambda x: x['sensitivity'])
        
        print(f"\n🔍 关键发现：")
        print(f"   最敏感组合：{most_sensitive['beam_type']} × {most_sensitive['support_type']}")
        print(f"   敏感度：{most_sensitive['sensitivity']:.2f} kN/mm")
        print(f"   ")
        print(f"   最不敏感组合：{least_sensitive['beam_type']} × {least_sensitive['support_type']}")
        print(f"   敏感度：{least_sensitive['sensitivity']:.2f} kN/mm")
        
        sensitivity_ratio = most_sensitive['sensitivity'] / least_sensitive['sensitivity']
        print(f"   敏感度差异：{sensitivity_ratio:.1f}倍")
        
        # 分析刚度匹配效应
        print(f"\n🔬 刚度匹配效应分析：")
        
        # 按梁刚度分组
        beam_groups = {}
        for result in successful_results:
            beam_type = result['beam_type']
            if beam_type not in beam_groups:
                beam_groups[beam_type] = []
            beam_groups[beam_type].append(result)
        
        for beam_type, group in beam_groups.items():
            print(f"   {beam_type}:")
            for result in group:
                print(f"     + {result['support_type']}: {result['sensitivity']:.2f} kN/mm")
        
        # 工程建议
        print(f"\n🏗️ 工程设计建议：")
        
        if most_sensitive['sensitivity'] > 50:
            print(f"   ⚠️  高敏感组合需要严格施工控制")
        if least_sensitive['sensitivity'] < 20:
            print(f"   ✅ 低敏感组合对施工误差容忍度高")
        
        print(f"   🎯 根据项目需求选择合适的刚度匹配：")
        print(f"      - 需要精确控制：选择低敏感度组合")
        print(f"      - 需要敏感监测：选择高敏感度组合")
    
    print(f"\n" + "="*100)
    print("✅ 刚度组合与沉降敏感性分析完成")
    print("="*100)
    
    return all_results

if __name__ == "__main__":
    results = test_stiffness_combinations_with_settlement() 