#!/usr/bin/env python3
"""
简化3D支座分析方法实现
Simplified 3D Bearing Analysis Method Implementation
"""

import numpy as np
import pandas as pd
from bridge_model_enhanced import BridgeModelXara

class Bridge3DAnalysis:
    """
    简化的3D桥梁分析类
    基于刚性横梁假设和弹性支座理论
    """
    
    def __init__(self, bridge_model):
        """
        初始化3D分析
        
        Args:
            bridge_model: BridgeModelXara实例
        """
        self.bridge = bridge_model
        self.bearing_stiffness = {}
        self.load_distribution_matrix = None
        
    def calculate_bearing_stiffness(self, bearing):
        """
        计算支座刚度
        
        Args:
            bearing: 支座信息字典
            
        Returns:
            dict: 支座刚度信息
        """
        bearing_type = bearing['parameters']['type']
        bearing_size = bearing['parameters']['size']
        material = bearing['parameters']['material']
        
        # 基本参数
        if bearing_size == 'large':
            area = 0.5 * 0.5  # 0.25 m²
            thickness = 0.1   # 0.1 m
        elif bearing_size == 'medium':
            area = 0.4 * 0.4  # 0.16 m²
            thickness = 0.08  # 0.08 m
        else:  # standard或small
            area = 0.3 * 0.3  # 0.09 m²
            thickness = 0.06  # 0.06 m
        
        # 材料参数
        if material == 'rubber':
            E_bearing = 1e6   # 1 MPa (橡胶)
        elif material == 'steel':
            E_bearing = 200e9  # 200 GPa (钢)
        else:  # default
            E_bearing = 5e6   # 5 MPa (标准橡胶)
        
        # 支座类型影响
        if bearing_type == 'spherical':
            # 球形支座，垂直刚度很大
            k_vertical = 1e12
            k_horizontal = 1e6
        elif bearing_type == 'sliding':
            # 滑动支座，水平刚度很小
            k_vertical = E_bearing * area / thickness
            k_horizontal = 1e3
        else:  # elastomeric
            # 弹性支座
            k_vertical = E_bearing * area / thickness
            k_horizontal = k_vertical * 0.1  # 水平刚度约为垂直刚度的10%
        
        return {
            'k_vertical': k_vertical,
            'k_horizontal': k_horizontal,
            'area': area,
            'thickness': thickness,
            'E_bearing': E_bearing
        }
    
    def build_stiffness_matrix(self):
        """
        构建支座刚度矩阵
        考虑每个支座的位置和刚度
        """
        n_bearings = len(self.bridge.individual_bearings)
        
        # 每个支座6个自由度的刚度矩阵
        K_global = np.zeros((n_bearings * 6, n_bearings * 6))
        
        bearing_stiffness_list = []
        
        for i, bearing in enumerate(self.bridge.individual_bearings):
            # 计算支座刚度
            stiffness = self.calculate_bearing_stiffness(bearing)
            bearing_stiffness_list.append(stiffness)
            
            # 支座在全局坐标系中的位置
            x = bearing['pier_x']
            y = bearing['pier_y']
            z = bearing['height']
            
            # 局部刚度矩阵 (6x6)
            k_local = np.zeros((6, 6))
            
            # 支座约束类型
            support_type = bearing['support_type']
            
            if support_type['type'] == 'fixed':
                # 固定支座：限制所有自由度
                k_local[0, 0] = stiffness['k_horizontal']  # X方向
                k_local[1, 1] = stiffness['k_horizontal']  # Y方向
                k_local[2, 2] = stiffness['k_vertical']    # Z方向
                k_local[3, 3] = stiffness['k_vertical'] * 0.1  # 绕X轴转动
                k_local[4, 4] = stiffness['k_vertical'] * 0.1  # 绕Y轴转动
                k_local[5, 5] = stiffness['k_vertical'] * 0.1  # 绕Z轴转动
                
            elif support_type['type'] == 'roller':
                # 滚动支座：只限制垂直位移
                k_local[2, 2] = stiffness['k_vertical']    # Z方向
                
            elif support_type['type'] == 'fixed_pin':
                # 固定铰接：限制位移，允许转动
                k_local[0, 0] = stiffness['k_horizontal']  # X方向
                k_local[1, 1] = stiffness['k_horizontal']  # Y方向
                k_local[2, 2] = stiffness['k_vertical']    # Z方向
            
            # 将局部刚度矩阵集成到全局刚度矩阵
            start_idx = i * 6
            end_idx = start_idx + 6
            K_global[start_idx:end_idx, start_idx:end_idx] = k_local
        
        self.bearing_stiffness = bearing_stiffness_list
        self.K_global = K_global
        
        return K_global
    
    def calculate_load_distribution(self, pier_loads):
        """
        计算荷载在支座间的分配
        
        Args:
            pier_loads: 各墩台的荷载 {pier_id: {'Fx': xx, 'Fy': yy, 'Mz': zz}}
            
        Returns:
            dict: 每个支座的荷载分配
        """
        load_distribution = {}
        
        # 按墩台分组处理
        pier_bearings = {}
        for bearing in self.bridge.individual_bearings:
            pier_id = bearing['longitudinal_id']
            if pier_id not in pier_bearings:
                pier_bearings[pier_id] = []
            pier_bearings[pier_id].append(bearing)
        
        # 对每个墩台计算荷载分配
        for pier_id, bearings in pier_bearings.items():
            if pier_id not in pier_loads:
                continue
                
            pier_load = pier_loads[pier_id]
            
            # 计算该墩台支座的相对刚度
            bearing_stiffness_info = []
            total_k_vertical = 0
            total_k_horizontal = 0
            
            for bearing in bearings:
                stiffness = self.calculate_bearing_stiffness(bearing)
                bearing_stiffness_info.append(stiffness)
                total_k_vertical += stiffness['k_vertical']
                total_k_horizontal += stiffness['k_horizontal']
            
            # 基于高度差的荷载重分配
            # 简化方法：高度差导致的强制位移产生的附加力
            
            # 计算平均高度
            avg_height = np.mean([b['height'] for b in bearings])
            
            # 为每个支座计算荷载
            for i, bearing in enumerate(bearings):
                bearing_id = bearing['bearing_id']
                stiffness = bearing_stiffness_info[i]
                
                # 基本荷载分配（按刚度比例）
                if total_k_vertical > 0:
                    vertical_ratio = stiffness['k_vertical'] / total_k_vertical
                else:
                    vertical_ratio = 1.0 / len(bearings)
                
                if total_k_horizontal > 0:
                    horizontal_ratio = stiffness['k_horizontal'] / total_k_horizontal
                else:
                    horizontal_ratio = 1.0 / len(bearings)
                
                # 基础荷载分配
                base_vertical = pier_load['Fy'] * vertical_ratio
                base_horizontal = pier_load['Fx'] * horizontal_ratio
                
                # 高度差导致的荷载重分配
                height_diff = bearing['height'] - avg_height
                
                # 简化计算：高度差产生的附加竖向力
                # 假设桥梁刚度为EI，支座间距为L
                L = self.bridge.bridge_width if len(bearings) > 1 else 1.0
                EI = self.bridge.E * self.bridge.I
                
                # 高度差产生的附加力（简化公式）
                if abs(height_diff) > 1e-6:  # 如果有高度差
                    # 使用简化的梁理论计算附加力
                    additional_force = 12 * EI * height_diff / (L ** 3)
                    
                    # 限制附加力的大小（不超过基础荷载的50%）
                    max_additional = abs(base_vertical) * 0.5
                    additional_force = np.sign(additional_force) * min(abs(additional_force), max_additional)
                else:
                    additional_force = 0
                
                # 最终荷载
                final_vertical = base_vertical + additional_force
                final_horizontal = base_horizontal
                
                load_distribution[bearing_id] = {
                    'Fx': final_horizontal,
                    'Fy': final_vertical,
                    'Mz': 0,  # 简化处理
                    'base_vertical': base_vertical,
                    'additional_force': additional_force,
                    'height_diff': height_diff,
                    'stiffness_ratio': vertical_ratio,
                    'stiffness': stiffness
                }
        
        return load_distribution
    
    def analyze_bridge_3d(self, pier_reactions):
        """
        进行简化的3D桥梁分析
        
        Args:
            pier_reactions: 从2D分析得到的墩台反力
            
        Returns:
            dict: 3D分析结果
        """
        # 构建支座刚度矩阵
        self.build_stiffness_matrix()
        
        # 准备墩台荷载数据
        pier_loads = {}
        for reaction in pier_reactions:
            pier_id = reaction['pier_id'] + 1  # 转换为1-based
            pier_loads[pier_id] = {
                'Fx': reaction['Fx'],
                'Fy': reaction['Fy'],
                'Mz': reaction['Mz']
            }
        
        # 计算荷载分配
        load_distribution = self.calculate_load_distribution(pier_loads)
        
        # 生成详细的分析报告
        analysis_results = {
            'load_distribution': load_distribution,
            'bearing_stiffness': self.bearing_stiffness,
            'total_vertical_reaction': sum(ld['Fy'] for ld in load_distribution.values()),
            'total_horizontal_reaction': sum(ld['Fx'] for ld in load_distribution.values()),
            'analysis_summary': self._generate_analysis_summary(load_distribution)
        }
        
        return analysis_results
    
    def _generate_analysis_summary(self, load_distribution):
        """生成分析摘要"""
        summary = {
            'max_bearing_load': max(ld['Fy'] for ld in load_distribution.values()),
            'min_bearing_load': min(ld['Fy'] for ld in load_distribution.values()),
            'max_height_effect': max(abs(ld['additional_force']) for ld in load_distribution.values()),
            'bearings_with_height_effect': len([ld for ld in load_distribution.values() if abs(ld['additional_force']) > 1e-3])
        }
        return summary
    
    def get_detailed_results_table(self, analysis_results):
        """
        生成详细的结果表格
        
        Args:
            analysis_results: 3D分析结果
            
        Returns:
            pandas.DataFrame: 详细结果表格
        """
        results_data = []
        
        for bearing_id, load_data in analysis_results['load_distribution'].items():
            # 找到对应的支座信息
            bearing_info = None
            for bearing in self.bridge.individual_bearings:
                if bearing['bearing_id'] == bearing_id:
                    bearing_info = bearing
                    break
            
            if bearing_info:
                results_data.append({
                    '支座编号': bearing_id,
                    '纵向位置 (m)': f"{bearing_info['pier_x']:.2f}",
                    '横向位置 (m)': f"{bearing_info['pier_y']:.2f}",
                    '高度偏移 (mm)': f"{bearing_info['height_offset'] * 1000:.1f}",
                    '基础反力 (kN)': f"{load_data['base_vertical'] / 1000:.1f}",
                    '高度效应 (kN)': f"{load_data['additional_force'] / 1000:.1f}",
                    '最终反力 (kN)': f"{load_data['Fy'] / 1000:.1f}",
                    '垂直刚度 (MN/m)': f"{load_data['stiffness']['k_vertical'] / 1e6:.1f}",
                    '刚度比例 (%)': f"{load_data['stiffness_ratio'] * 100:.1f}",
                    '支座类型': bearing_info['support_type']['type']
                })
        
        return pd.DataFrame(results_data)

def test_3d_analysis():
    """测试3D分析方法"""
    print("🎯 3D支座分析方法测试")
    print("=" * 60)
    
    # 创建桥梁模型
    bridge = BridgeModelXara(
        length=60.0,
        num_spans=3,
        bearings_per_pier=2,
        bridge_width=15.0,
        individual_bearing_config={
            '1-1': {'height_offset': 0.005},  # 5mm
            '1-2': {'height_offset': 0.000},  # 0mm
            '2-1': {'height_offset': 0.002},  # 2mm
            '2-2': {'height_offset': 0.008},  # 8mm
        }
    )
    
    # 运行2D分析获取墩台反力
    bridge.add_point_load(-150000, 0.3)
    bridge.add_point_load(-100000, 0.7)
    results_2d = bridge.run_analysis()
    
    if results_2d['analysis_ok']:
        print("✅ 2D分析完成")
        print(f"   总反力: {sum(r['Fy'] for r in results_2d['reactions']) / 1000:.1f}kN")
        print()
        
        # 进行3D分析
        analyzer_3d = Bridge3DAnalysis(bridge)
        results_3d = analyzer_3d.analyze_bridge_3d(results_2d['reactions'])
        
        print("🔧 3D分析结果:")
        print(f"   总垂直反力: {results_3d['total_vertical_reaction'] / 1000:.1f}kN")
        print(f"   最大支座荷载: {results_3d['analysis_summary']['max_bearing_load'] / 1000:.1f}kN")
        print(f"   最小支座荷载: {results_3d['analysis_summary']['min_bearing_load'] / 1000:.1f}kN")
        print(f"   最大高度效应: {results_3d['analysis_summary']['max_height_effect'] / 1000:.1f}kN")
        print()
        
        # 生成详细表格
        detailed_table = analyzer_3d.get_detailed_results_table(results_3d)
        print("📊 详细支座分析结果:")
        print(detailed_table.to_string(index=False))
        print()
        
        # 对比2D和3D结果
        print("📈 2D vs 3D 结果对比:")
        print("墩台级反力 (2D分析):")
        for reaction in results_2d['reactions']:
            pier_id = reaction['pier_id'] + 1
            print(f"   墩台{pier_id}: {reaction['Fy'] / 1000:.1f}kN")
        
        print("\n支座级反力 (3D分析):")
        for bearing_id, load_data in results_3d['load_distribution'].items():
            pier_id = int(bearing_id.split('-')[0])
            print(f"   支座{bearing_id}: {load_data['Fy'] / 1000:.1f}kN "
                  f"(基础: {load_data['base_vertical'] / 1000:.1f}kN, "
                  f"高度效应: {load_data['additional_force'] / 1000:.1f}kN)")
        
    else:
        print("❌ 2D分析失败")
        print(f"   错误: {results_2d.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_3d_analysis()
