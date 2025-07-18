#!/usr/bin/env python3
"""
测试脚本: 验证 "3D梁+弹性支座法"
目标: 验证支座的毫米级高度差对支座反力的影响。

方法论:
1.  **3D模型空间**: 建立一个三维(3D)坐标系，每个节点有6个自由度。
2.  **3D梁单元**: 使用 `elasticBeamColumn` 单元模拟桥梁主梁，能够承受弯曲、剪切和扭转。
3.  **弹性支座**: 使用 `zeroLength` 单元模拟弹性支座，每个支座连接主梁上的节点和一个地面上的固定节点。
4.  **高度差模拟**: 通过改变地面固定节点的Z坐标来精确模拟支座的安装高度差。
5.  **对比验证**:
    - 场景A (基准): 所有支座高度相同。
    - 场景B (测试): 将一个中间支座抬高5毫米。
    - 比较两个场景下各支座反力的变化，验证抬高的支座是否承担了更多的荷载。
"""

import openseespy.opensees as ops
import math

def run_bridge_analysis(bearing_heights: dict):
    """
    运行一次完整的3D桥梁分析。

    Args:
        bearing_heights (dict): 一个包含支座节点ID及其Z坐标(高度)的字典。
                                e.g., {101: 0.0, 106: 0.005, 111: 0.0}

    Returns:
        dict: 一个包含支座节点ID及其竖向反力的字典。
    """
    ops.wipe()

    # 1. 建立3D模型空间 (3D-NDM, 6-NDF)
    ops.model('basic', '-ndm', 3, '-ndf', 6)

    # --- 定义参数 ---
    length = 60.0  # 桥梁总长 (m)
    num_girder_nodes = 11
    dx = length / (num_girder_nodes - 1)

    # 材料和截面属性 (混凝土)
    E = 30.0e9  # 弹性模量 (Pa)
    nu = 0.2  # 泊松比
    G = E / (2 * (1 + nu))  # 剪切模量
    section_h = 1.5  # 截面高 (m)
    section_w = 1.0  # 截面宽 (m)
    A = section_h * section_w  # 面积
    Iz = (1/12) * section_w * section_h**3  # 强轴惯性矩
    Iy = (1/12) * section_h * section_w**3  # 弱轴惯性矩
    J = Iy + Iz # 简化计算扭转惯性矩

    # 支座弹簧刚度 (模拟一个非常硬的支座)
    k_bearing = 2.0e10  # N/m

    # --- 节点定义 ---
    # 主梁节点 (在Z=0平面上)
    girder_nodes = list(range(1, num_girder_nodes + 1))
    for i in girder_nodes:
        ops.node(i, (i - 1) * dx, 0.0, 0.0)

    # 地面固定节点 (Z坐标由输入的高度决定)
    ground_nodes = list(bearing_heights.keys())
    support_locations = {101: 1, 106: 6, 111: 11} # 地面节点 -> 主梁节点
    for node_id, height in bearing_heights.items():
        girder_node_id = support_locations[node_id]
        x_coord = ops.nodeCoord(girder_node_id, 1)
        ops.node(node_id, x_coord, 0.0, height)

    # --- 约束和材料 ---
    # 地面节点完全固定
    for node_id in ground_nodes:
        ops.fix(node_id, 1, 1, 1, 1, 1, 1)

    # 定义支座弹簧的单轴材料
    mat_bearing_id = 1
    ops.uniaxialMaterial('Elastic', mat_bearing_id, k_bearing)

    # 定义3D梁的几何变换
    transf_tag = 1
    ops.geomTransf('Linear', transf_tag)

    # --- 单元定义 ---
    # 创建主梁单元 (3D elasticBeamColumn)
    for i in range(len(girder_nodes) - 1):
        node_i = girder_nodes[i]
        node_j = girder_nodes[i+1]
        elem_id = i + 1
        ops.element('elasticBeamColumn', elem_id, node_i, node_j, A, E, G, J, Iy, Iz, transf_tag)

    # 创建弹性支座单元 (zeroLength弹簧)
    for i, ground_node_id in enumerate(ground_nodes):
        girder_node_id = support_locations[ground_node_id]
        elem_id = 100 + i
        # 弹簧连接主梁节点和地面节点，只在竖直方向(dir 3 -> Z轴)起作用
        ops.element('zeroLength', elem_id, girder_node_id, ground_node_id, '-mat', mat_bearing_id, '-dir', 3)

    # --- 荷载和分析 ---
    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)
    # 在跨中施加一个向下的集中荷载
    ops.load(4, 0.0, 0.0, -500e3, 0.0, 0.0, 0.0) # 500kN

    ops.system('BandGeneral')
    ops.numberer('RCM')
    ops.constraints('Plain')
    ops.integrator('LoadControl', 1.0)
    ops.algorithm('Linear')
    ops.analysis('Static')
    ops.analyze(1)

    # --- 结果提取 ---
    reactions = {}
    for node_id in ground_nodes:
        # 提取地面节点的Z方向反力
        ops.reactions()
        reactions[node_id] = ops.nodeReaction(node_id, 3)

    return reactions


def main():
    """主测试函数"""
    print("=" * 80)
    print("脚本: 验证 '3D梁+弹性支座法' 中支座高度差对反力的影响")
    print("=" * 80)

    # --- 场景 A: 基准情况 (所有支座高度相同) ---
    print("\n🔹 场景 A: 基准分析 (所有支座高度偏移 = 0.0 mm)")
    heights_base = {101: 0.0, 106: 0.0, 111: 0.0}
    reactions_base = run_bridge_analysis(heights_base)
    print("  支座高度: Z_101=0.0mm, Z_106=0.0mm, Z_111=0.0mm")
    print("  计算反力:")
    for node, reaction in reactions_base.items():
        print(f"    - 支座 {node}: {reaction/1000:.2f} kN")

    # --- 场景 B: 测试情况 (中间支座抬高5mm) ---
    print("\n🔹 场景 B: 测试分析 (中间支座 106 高度偏移 = 5.0 mm)")
    height_offset = 0.005  # 5mm
    heights_test = {101: 0.0, 106: height_offset, 111: 0.0}
    reactions_test = run_bridge_analysis(heights_test)
    print(f"  支座高度: Z_101=0.0mm, Z_106={height_offset*1000}mm, Z_111=0.0mm")
    print("  计算反力:")
    for node, reaction in reactions_test.items():
        print(f"    - 支座 {node}: {reaction/1000:.2f} kN")

    # --- 结果对比与验证 ---
    print("\n" + "=" * 80)
    print("📊 结果对比与验证")
    print("-" * 80)
    print(f"{'支座':<10} | {'基准反力 (kN)':<20} | {'抬高后反力 (kN)':<20} | {'变化量 (kN)':<15}")
    print("-" * 80)

    base_106 = reactions_base[106]
    test_106 = reactions_test[106]
    change = test_106 - base_106

    print(f"{'支座 101':<10} | {reactions_base[101]/1000:<20.2f} | {reactions_test[101]/1000:<20.2f} | {(reactions_test[101]-reactions_base[101])/1000:<15.2f}")
    print(f"{'支座 106':<10} | {base_106/1000:<20.2f} | {test_106/1000:<20.2f} | {change/1000:<15.2f}  <-- 验证点")
    print(f"{'支座 111':<10} | {reactions_base[111]/1000:<20.2f} | {reactions_test[111]/1000:<20.2f} | {(reactions_test[111]-reactions_base[111])/1000:<15.2f}")
    print("-" * 80)

    # 验证核心逻辑：抬高后的支座，其反力绝对值应该增加
    # 注意：反力方向与Z轴正方向相反，所以值为负。比较绝对值。
    if abs(test_106) > abs(base_106):
        print("\n✅ 验证通过: 中间支座被抬高后，承担了更多的荷载。")
        print(f"   反力从 {abs(base_106)/1000:.2f} kN 增加到 {abs(test_106)/1000:.2f} kN。")
    else:
        print("\n❌ 验证失败: 支座抬高后反力未按预期增加。")

    print("=" * 80)


if __name__ == "__main__":
    main()
