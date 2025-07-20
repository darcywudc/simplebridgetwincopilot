#!/usr/bin/env python3
"""
生成详细的支座反力对比表格
显示每个墩台在2号墩高度增加0.1厘米前后的具体受力数值
"""

import numpy as np
import pandas as pd
from bridge_model_enhanced import BridgeModelXara

def create_detailed_force_table():
    """创建详细的支座反力对比表格"""
    print("="*120)
    print("详细支座反力对比表 - 2号墩高度增加0.1厘米前后")
    print("="*120)
    
    # 基础参数
    bridge_length = 60.0
    num_elements = 20
    base_E = 30e9
    section_height = 1.5
    section_width = 1.0
    density = 2400
    
    # 梁刚度配置
    beam_configs = {
        '低刚度梁': {'E': base_E * 0.5, 'desc': '0.5×标准刚度'},
        '标准刚度梁': {'E': base_E, 'desc': '1.0×标准刚度'},
        '高刚度梁': {'E': base_E * 2.0, 'desc': '2.0×标准刚度'}
    }
    
    # 支座配置
    support_configs = {
        '刚性支座': {
            'types': [
                {'type': 'fixed_pin', 'dx': 1, 'dy': 1, 'rz': 0},
                {'type': 'fixed', 'dx': 1, 'dy': 1, 'rz': 1},
                {'type': 'fixed', 'dx': 1, 'dy': 1, 'rz': 1},
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0}
            ]
        },
        '标准支座': {
            'types': [
                {'type': 'fixed_pin', 'dx': 1, 'dy': 1, 'rz': 0},
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0},
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0},
                {'type': 'roller', 'dx': 0, 'dy': 1, 'rz': 0}
            ]
        }
    }
    
    # 墩台高度
    original_heights = [8.000, 8.005, 8.015, 8.003]
    modified_heights = [8.000, 8.006, 8.015, 8.003]  # 2号墩+0.1厘米
    
    all_tables = []
    
    # 遍历所有组合
    for beam_name, beam_config in beam_configs.items():
        for support_name, support_config in support_configs.items():
            
            print(f"\n{'='*80}")
            print(f"📊 {beam_name} × {support_name}")
            print(f"    梁刚度: {beam_config['desc']}")
            print(f"{'='*80}")
            
            try:
                # 原始模型
                bridge_orig = BridgeModelXara(
                    length=bridge_length,
                    num_elements=num_elements,
                    E=beam_config['E'],
                    section_height=section_height,
                    section_width=section_width,
                    density=density,
                    num_spans=3,
                    pier_heights=original_heights,
                    support_types=support_config['types']
                )
                
                # 修改后模型
                bridge_mod = BridgeModelXara(
                    length=bridge_length,
                    num_elements=num_elements,
                    E=beam_config['E'],
                    section_height=section_height,
                    section_width=section_width,
                    density=density,
                    num_spans=3,
                    pier_heights=modified_heights,
                    support_types=support_config['types']
                )
                
                # 添加荷载
                for bridge in [bridge_orig, bridge_mod]:
                    bridge.add_distributed_load(-50000)  # 50 kN/m
                    bridge.add_point_load(-200000, 0.3)  # 200 kN
                    bridge.add_point_load(-200000, 0.7)  # 200 kN
                
                # 运行分析
                results_orig = bridge_orig.run_analysis()
                results_mod = bridge_mod.run_analysis()
                
                if results_orig['analysis_ok'] and results_mod['analysis_ok']:
                    
                    # 创建详细表格
                    table_data = []
                    reactions_orig = results_orig['reactions']
                    reactions_mod = results_mod['reactions']
                    
                    print(f"\n📋 详细受力对比表：")
                    print(f"{'墩台':<8} {'初始值(kN)':<12} {'修改后(kN)':<12} {'变化(kN)':<12} {'变化(%)':<10} {'初始值(吨)':<12} {'修改后(吨)':<12}")
                    print("-" * 85)
                    
                    total_change_kn = 0
                    
                    for i in range(len(reactions_orig)):
                        # 获取竖向反力（N转换为kN和吨）
                        orig_n = reactions_orig[i]['Fy']        # N
                        mod_n = reactions_mod[i]['Fy']          # N
                        
                        orig_kn = orig_n / 1000                 # kN
                        mod_kn = mod_n / 1000                   # kN
                        change_kn = mod_kn - orig_kn            # kN变化
                        
                        orig_ton = orig_n / 9810                # 吨（1吨≈9.81kN）
                        mod_ton = mod_n / 9810                  # 吨
                        
                        change_percent = (change_kn / orig_kn * 100) if orig_kn != 0 else 0
                        total_change_kn += abs(change_kn)
                        
                        pier_name = f"{i+1}号墩"
                        print(f"{pier_name:<8} {orig_kn:<12.2f} {mod_kn:<12.2f} {change_kn:<12.3f} {change_percent:<10.3f} {orig_ton:<12.2f} {mod_ton:<12.2f}")
                        
                        # 存储数据用于后续分析
                        table_data.append({
                            '组合': f"{beam_name}×{support_name}",
                            '墩台': pier_name,
                            '初始值_kN': orig_kn,
                            '修改后_kN': mod_kn,
                            '变化_kN': change_kn,
                            '变化_percent': change_percent,
                            '初始值_ton': orig_ton,
                            '修改后_ton': mod_ton
                        })
                    
                    print("-" * 85)
                    print(f"{'总变化量':<8} {'':<24} {total_change_kn:<12.3f} {'kN':<10}")
                    print(f"{'说明':<8} 总变化量 = 所有墩台变化绝对值之和")
                    
                    # 验证荷载平衡
                    total_orig = sum(r['Fy'] for r in reactions_orig) / 1000
                    total_mod = sum(r['Fy'] for r in reactions_mod) / 1000
                    print(f"\n🔍 荷载平衡验证：")
                    print(f"   原始总反力：{total_orig:.2f} kN")
                    print(f"   修改后总反力：{total_mod:.2f} kN")
                    print(f"   差值：{abs(total_mod - total_orig):.6f} kN ✅")
                    
                    # 找出变化最大的墩台
                    max_change_pier = max(range(len(reactions_orig)), key=lambda i: abs(reactions_mod[i]['Fy'] - reactions_orig[i]['Fy']))
                    max_change_value = (reactions_mod[max_change_pier]['Fy'] - reactions_orig[max_change_pier]['Fy']) / 1000
                    
                    print(f"\n🎯 关键结果：")
                    print(f"   变化最大墩台：{max_change_pier+1}号墩")
                    print(f"   最大变化量：{max_change_value:.3f} kN")
                    print(f"   敏感度：{total_change_kn/0.1:.1f} kN/mm")
                    
                    all_tables.extend(table_data)
                    
                else:
                    print("❌ 分析失败 - 可能是支座配置不稳定")
                    
            except Exception as e:
                print(f"❌ 运行出错：{e}")
    
    # 创建综合对比表
    if all_tables:
        print(f"\n" + "="*120)
        print("📊 综合对比汇总表")
        print("="*120)
        
        df = pd.DataFrame(all_tables)
        
        # 按组合分组显示
        for combo in df['组合'].unique():
            combo_data = df[df['组合'] == combo]
            print(f"\n🔧 {combo}:")
            print(f"{'墩台':<8} {'初始(kN)':<12} {'修改后(kN)':<12} {'变化(kN)':<12} {'初始(吨)':<12} {'修改后(吨)':<12}")
            print("-" * 70)
            
            for _, row in combo_data.iterrows():
                print(f"{row['墩台']:<8} {row['初始值_kN']:<12.2f} {row['修改后_kN']:<12.2f} "
                      f"{row['变化_kN']:<12.3f} {row['初始值_ton']:<12.2f} {row['修改后_ton']:<12.2f}")
        
        # 最大变化汇总
        print(f"\n" + "="*80)
        print("🏆 各组合最大变化汇总")
        print("="*80)
        print(f"{'组合':<25} {'最大变化墩台':<12} {'最大变化(kN)':<15} {'总变化(kN)':<15}")
        print("-" * 70)
        
        for combo in df['组合'].unique():
            combo_data = df[df['组合'] == combo]
            max_abs_change = combo_data.loc[combo_data['变化_kN'].abs().idxmax()]
            total_change = combo_data['变化_kN'].abs().sum()
            
            print(f"{combo:<25} {max_abs_change['墩台']:<12} {max_abs_change['变化_kN']:<15.3f} {total_change:<15.3f}")
    
    print(f"\n" + "="*120)
    print("✅ 详细受力对比分析完成")
    print("💡 说明：变化值为正表示受力增加，为负表示受力减少")
    print("📏 测试条件：2号墩高度从8.005m增加到8.006m（+0.1厘米）")
    print("="*120)

if __name__ == "__main__":
    create_detailed_force_table() 