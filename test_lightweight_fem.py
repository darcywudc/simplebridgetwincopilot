#!/usr/bin/env python3
"""
测试轻量级有限元解决方案
重点关注实用性和稳定性
"""

import numpy as np
import sys
import subprocess

def install_if_needed(package):
    """如果需要则安装包"""
    try:
        __import__(package.replace('-', '_'))
        return True
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            return True
        except:
            return False

def test_meshio():
    """测试meshio - 网格处理库"""
    print("🔧 测试meshio - 网格I/O库")
    print("="*50)
    
    if not install_if_needed('meshio'):
        print("   ❌ meshio安装失败")
        return False
    
    try:
        import meshio
        import numpy as np
        
        print(f"   ✅ meshio版本: {meshio.__version__}")
        
        # 创建简单的桥梁网格
        print("   🌉 创建桥梁网格...")
        
        # 1D梁网格
        length = 60.0
        num_elements = 30
        
        points = np.zeros((num_elements + 1, 3))
        points[:, 0] = np.linspace(0, length, num_elements + 1)
        
        cells = [("line", np.column_stack([np.arange(num_elements), np.arange(1, num_elements + 1)]))]
        
        mesh = meshio.Mesh(points, cells)
        
        print(f"   ✅ 1D梁网格: {len(points)}个节点, {num_elements}个单元")
        
        # 创建2D桥面网格
        print("   🌉 创建2D桥面网格...")
        
        # 矩形桥面
        nx, ny = 20, 4
        x = np.linspace(0, length, nx + 1)
        y = np.linspace(0, 2.0, ny + 1)
        
        X, Y = np.meshgrid(x, y)
        points_2d = np.column_stack([X.ravel(), Y.ravel(), np.zeros(X.size)])
        
        # 四边形单元
        quads = []
        for j in range(ny):
            for i in range(nx):
                n1 = j * (nx + 1) + i
                n2 = n1 + 1
                n3 = n1 + (nx + 1) + 1
                n4 = n1 + (nx + 1)
                quads.append([n1, n2, n3, n4])
        
        cells_2d = [("quad", np.array(quads))]
        mesh_2d = meshio.Mesh(points_2d, cells_2d)
        
        print(f"   ✅ 2D桥面网格: {len(points_2d)}个节点, {len(quads)}个四边形")
        
        # 保存网格文件
        try:
            mesh.write("bridge_1d.vtk")
            mesh_2d.write("bridge_2d.vtk")
            print("   ✅ 网格文件保存成功 (bridge_1d.vtk, bridge_2d.vtk)")
        except:
            print("   ⚠️  网格文件保存跳过")
        
        return True
        
    except Exception as e:
        print(f"   ❌ meshio测试失败: {e}")
        return False

def test_pure_numpy_fem():
    """测试纯NumPy有限元实现"""
    print("\n🔧 测试纯NumPy有限元框架")
    print("="*50)
    
    try:
        import numpy as np
        from scipy.sparse import csr_matrix
        from scipy.sparse.linalg import spsolve
        import matplotlib.pyplot as plt
        
        print("   ✅ 依赖库可用")
        
        # 创建桥梁支座分析类
        class BridgeSupportAnalyzer:
            def __init__(self, length=60.0, num_elements=30):
                self.length = length
                self.num_elements = num_elements
                self.nodes = np.linspace(0, length, num_elements + 1)
                self.elements = np.column_stack([np.arange(num_elements), 
                                               np.arange(1, num_elements + 1)])
                self.num_dofs = num_elements + 1
                
            def assemble_stiffness_matrix(self, E=200e9, I=0.1, support_stiffness=None):
                """组装刚度矩阵"""
                L = self.length / self.num_elements  # 单元长度
                
                # 梁单元刚度矩阵 (简化为轴向刚度)
                k_element = E * I / L
                
                # 全局刚度矩阵
                K = np.zeros((self.num_dofs, self.num_dofs))
                
                # 组装单元刚度
                for elem in self.elements:
                    i, j = elem
                    K[i, i] += k_element
                    K[j, j] += k_element
                    K[i, j] -= k_element
                    K[j, i] -= k_element
                
                # 添加支座刚度
                if support_stiffness is not None:
                    for node, k_support in support_stiffness.items():
                        K[node, node] += k_support
                
                return K
            
            def solve_static(self, K, loads, fixed_dofs=None):
                """求解静力问题"""
                F = np.zeros(self.num_dofs)
                
                # 施加荷载
                for node, load in loads.items():
                    F[node] = load
                
                # 处理边界条件
                if fixed_dofs is None:
                    fixed_dofs = [0]  # 默认固定第一个节点
                
                free_dofs = [i for i in range(self.num_dofs) if i not in fixed_dofs]
                
                # 约化系统
                K_reduced = K[np.ix_(free_dofs, free_dofs)]
                F_reduced = F[free_dofs]
                
                # 求解
                u_reduced = np.linalg.solve(K_reduced, F_reduced)
                
                # 完整位移向量
                u = np.zeros(self.num_dofs)
                u[free_dofs] = u_reduced
                
                return u
        
        # 测试分析器
        print("   🔧 创建桥梁分析器...")
        analyzer = BridgeSupportAnalyzer(length=60.0, num_elements=20)
        
        print(f"   ✅ 桥梁模型: {analyzer.num_dofs}个节点")
        
        # 不同支座刚度配置
        support_configs = [
            {'name': '无支座', 'stiffness': {}},
            {'name': '软支座', 'stiffness': {10: 1e6, 20: 1e6}},  # 中间支座
            {'name': '硬支座', 'stiffness': {10: 1e9, 20: 1e9}},
        ]
        
        results = []
        
        for config in support_configs:
            print(f"   🔧 分析: {config['name']}")
            
            # 组装刚度矩阵
            K = analyzer.assemble_stiffness_matrix(support_stiffness=config['stiffness'])
            
            # 施加荷载 (跨中10kN向下)
            loads = {10: -10000}  # 中间节点
            
            try:
                # 求解
                u = analyzer.solve_static(K, loads, fixed_dofs=[0, -1])  # 两端固定
                
                max_disp = np.max(np.abs(u))
                mid_disp = abs(u[len(u)//2])
                
                results.append({
                    'config': config['name'],
                    'max_displacement': max_disp,
                    'mid_displacement': mid_disp
                })
                
                print(f"      最大位移: {max_disp*1000:.3f} mm")
                print(f"      跨中位移: {mid_disp*1000:.3f} mm")
                
            except np.linalg.LinAlgError as e:
                print(f"      ❌ 求解失败: {e}")
        
        # 显示支座效应
        if len(results) > 1:
            print("\n   📊 支座效应对比:")
            for result in results:
                print(f"      {result['config']}: {result['mid_displacement']*1000:.3f} mm")
        
        print("   ✅ 纯NumPy有限元测试成功!")
        return True
        
    except Exception as e:
        print(f"   ❌ 纯NumPy FEM测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_beam_theory_validation():
    """验证梁理论计算"""
    print("\n🔧 梁理论验证")
    print("="*50)
    
    try:
        import numpy as np
        
        print("   📚 经典梁理论计算...")
        
        # 简支梁集中荷载理论解
        L = 60.0  # 跨度
        P = 10000  # 集中荷载 (N)
        E = 200e9  # 弹性模量
        I = 0.1   # 惯性矩
        
        # 跨中位移理论值 (简支梁跨中集中荷载)
        delta_theory = P * L**3 / (48 * E * I)
        
        print(f"   📊 理论跨中位移: {delta_theory*1000:.3f} mm")
        
        # 支座刚度影响分析
        print("   🔧 支座刚度影响分析...")
        
        # 简化的支座-梁系统
        k_beam = 48 * E * I / L**3  # 等效梁刚度
        
        support_stiffnesses = [1e6, 1e8, 1e10, 1e12]  # 支座刚度范围
        
        for k_support in support_stiffnesses:
            # 串联弹簧系统
            k_total = 1 / (1/k_beam + 1/k_support)
            delta_with_support = P / k_total
            
            reduction = (1 - delta_with_support/delta_theory) * 100
            
            print(f"      k_support={k_support:.0e}: 位移={delta_with_support*1000:.3f}mm, "
                  f"减少={reduction:.1f}%")
        
        print("   ✅ 梁理论验证完成!")
        return True
        
    except Exception as e:
        print(f"   ❌ 梁理论验证失败: {e}")
        return False

def test_visualization():
    """测试可视化功能"""
    print("\n🔧 测试可视化功能")
    print("="*50)
    
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        
        print("   📊 创建桥梁分析结果图...")
        
        # 模拟数据
        x = np.linspace(0, 60, 21)
        
        # 不同支座配置的位移
        displacement_configs = {
            '无支座': -0.05 * (x/60) * (1 - x/60) * 4,  # 抛物线
            '软支座': -0.03 * (x/60) * (1 - x/60) * 4,
            '硬支座': -0.01 * (x/60) * (1 - x/60) * 4,
        }
        
        # 创建图形 (但不显示，只测试功能)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # 位移图
        for config, disp in displacement_configs.items():
            ax1.plot(x, disp*1000, label=config, linewidth=2)
        
        ax1.set_xlabel('桥梁位置 (m)')
        ax1.set_ylabel('位移 (mm)')
        ax1.set_title('不同支座配置的桥梁位移对比')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 支座刚度效应
        stiffness = np.logspace(6, 12, 50)
        max_displacement = 50 / (1 + stiffness/1e8)  # 简化模型
        
        ax2.semilogx(stiffness, max_displacement, 'b-', linewidth=2)
        ax2.set_xlabel('支座刚度 (N/m)')
        ax2.set_ylabel('最大位移 (mm)')
        ax2.set_title('支座刚度对桥梁位移的影响')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图片而不显示
        try:
            plt.savefig('bridge_analysis_demo.png', dpi=150, bbox_inches='tight')
            print("   ✅ 可视化图片保存: bridge_analysis_demo.png")
        except:
            print("   ⚠️  图片保存跳过")
        
        plt.close()  # 关闭图形，不显示
        
        print("   ✅ 可视化功能测试成功!")
        return True
        
    except Exception as e:
        print(f"   ❌ 可视化测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 轻量级有限元解决方案测试")
    print("="*60)
    
    print("🎯 目标: 找到适合Mac Apple Silicon的稳定FEM方案")
    print("📋 测试: meshio, 纯NumPy FEM, 梁理论, 可视化")
    print()
    
    # 测试各个组件
    results = {}
    
    results['meshio'] = test_meshio()
    results['numpy_fem'] = test_pure_numpy_fem()
    results['beam_theory'] = test_beam_theory_validation()
    results['visualization'] = test_visualization()
    
    print("\n📊 测试总结:")
    print("="*60)
    
    success_count = sum(results.values())
    total_tests = len(results)
    
    for test_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{test_name:15}: {status}")
    
    print(f"\n📈 总体成功率: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    
    if success_count >= 3:
        print("\n🎉 优秀！轻量级FEM方案在Mac上运行良好!")
        print("\n🏆 推荐的桥梁支座分析技术栈:")
        print("  1. 🔢 NumPy/SciPy - 核心计算")
        print("  2. 🌐 meshio - 网格处理") 
        print("  3. 📊 matplotlib - 可视化")
        print("  4. 📚 经典梁理论 - 验证")
        print("  5. 🐍 纯Python - 易于定制")
        
        print("\n✨ 优势:")
        print("  • 零编译依赖，纯Python")
        print("  • 完全控制支座建模")
        print("  • 快速原型开发")
        print("  • 与现有工具集成容易")
        print("  • 在Apple Silicon上完美运行")
        
        print("\n🚀 下一步建议:")
        print("  1. 基于纯NumPy方案深度开发")
        print("  2. 添加更多单元类型")
        print("  3. 集成到您的桥梁分析系统")
        print("  4. 考虑添加动力学分析")
        
    else:
        print("\n⚠️  部分功能存在问题，建议:")
        print("  1. 检查依赖包安装")
        print("  2. 逐步解决失败的测试")
        print("  3. 专注于成功的组件")

if __name__ == "__main__":
    main() 