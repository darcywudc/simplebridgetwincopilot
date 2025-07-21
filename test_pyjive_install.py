#!/usr/bin/env python3
"""
测试pyJive - 一个纯Python有限元库
"""

import sys
import subprocess
import importlib

def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def test_pyjive():
    """测试pyJive安装和基本功能"""
    print("🔧 测试pyJive - 纯Python有限元库")
    print("="*50)
    
    # 尝试安装依赖
    required_packages = [
        'numpy',
        'matplotlib', 
        'scipy',
        'gmsh'  # 网格生成
    ]
    
    print("📦 安装依赖包...")
    for pkg in required_packages:
        try:
            importlib.import_module(pkg.replace('-', '_'))
            print(f"   ✅ {pkg} 已安装")
        except ImportError:
            print(f"   🔧 安装 {pkg}...")
            if install_package(pkg):
                print(f"   ✅ {pkg} 安装成功")
            else:
                print(f"   ❌ {pkg} 安装失败")
    
    # pyJive需要从GitHub克隆，让我们创建一个简化版本
    print("\n🔧 创建简化的PyJive风格FEM框架...")
    return create_simple_fem_framework()

def create_simple_fem_framework():
    """创建一个类似pyJive的简单FEM框架"""
    print("🏗️ 构建简化FEM框架...")
    
    try:
        import numpy as np
        import matplotlib.pyplot as plt
        from scipy.sparse import csr_matrix
        from scipy.sparse.linalg import spsolve
        
        print("   ✅ 核心依赖可用")
        
        # 创建一个简单的2D三角形单元
        return test_simple_triangle_element()
        
    except ImportError as e:
        print(f"   ❌ 缺少依赖: {e}")
        return False

def test_simple_triangle_element():
    """测试简单的三角形单元"""
    print("\n🔧 测试简单三角形单元...")
    
    import numpy as np
    from scipy.sparse import csr_matrix
    from scipy.sparse.linalg import spsolve
    
    try:
        # 定义一个简单的三角形网格
        nodes = np.array([
            [0.0, 0.0],  # 节点0
            [1.0, 0.0],  # 节点1  
            [0.0, 1.0],  # 节点2
            [1.0, 1.0]   # 节点3
        ])
        
        elements = np.array([
            [0, 1, 2],  # 三角形单元1
            [1, 3, 2]   # 三角形单元2
        ])
        
        print(f"   ✅ 网格: {len(nodes)}个节点, {len(elements)}个单元")
        
        # 简单的刚度矩阵组装
        num_dofs = len(nodes) * 2  # 每个节点2个自由度
        K = np.zeros((num_dofs, num_dofs))
        
        # 材料参数
        E = 200e9  # 弹性模量
        nu = 0.3   # 泊松比
        t = 0.01   # 厚度
        
        for elem in elements:
            # 获取单元节点坐标
            elem_nodes = nodes[elem]
            
            # 计算单元刚度矩阵 (简化版本)
            area = 0.5 * abs(np.linalg.det(np.column_stack([
                elem_nodes[1] - elem_nodes[0],
                elem_nodes[2] - elem_nodes[0]
            ])))
            
            # 简化的平面应力刚度矩阵
            D = E / (1 - nu**2) * np.array([
                [1, nu, 0],
                [nu, 1, 0],
                [0, 0, (1-nu)/2]
            ])
            
            # 简化的B矩阵 (常应变三角形)
            x1, y1 = elem_nodes[0]
            x2, y2 = elem_nodes[1] 
            x3, y3 = elem_nodes[2]
            
            # 面积坐标导数
            b1 = y2 - y3
            b2 = y3 - y1
            b3 = y1 - y2
            c1 = x3 - x2
            c2 = x1 - x3
            c3 = x2 - x1
            
            B = 1/(2*area) * np.array([
                [b1, 0, b2, 0, b3, 0],
                [0, c1, 0, c2, 0, c3],
                [c1, b1, c2, b2, c3, b3]
            ])
            
            # 单元刚度矩阵
            k_elem = B.T @ D @ B * area * t
            
            # 组装到全局刚度矩阵
            dofs = []
            for node in elem:
                dofs.extend([2*node, 2*node+1])
            
            for i, global_i in enumerate(dofs):
                for j, global_j in enumerate(dofs):
                    K[global_i, global_j] += k_elem[i, j]
        
        print(f"   ✅ 刚度矩阵组装完成: {K.shape}")
        print(f"   ✅ 矩阵条件数: {np.linalg.cond(K[:6, :6]):.2e}")
        
        # 简单的边界条件和荷载
        f = np.zeros(num_dofs)
        f[3] = 1000.0  # 节点1的y方向荷载
        
        # 固定节点0的所有自由度
        fixed_dofs = [0, 1]  # 节点0的x,y方向
        free_dofs = [i for i in range(num_dofs) if i not in fixed_dofs]
        
        # 求解约化系统
        K_reduced = K[np.ix_(free_dofs, free_dofs)]
        f_reduced = f[free_dofs]
        
        try:
            u_reduced = np.linalg.solve(K_reduced, f_reduced)
            
            # 完整解向量
            u = np.zeros(num_dofs)
            u[free_dofs] = u_reduced
            
            print(f"   ✅ 求解成功!")
            print(f"   📊 最大位移: {np.max(np.abs(u))*1000:.3f} mm")
            
            # 显示节点位移
            for i in range(len(nodes)):
                ux = u[2*i]
                uy = u[2*i+1]
                print(f"      节点{i}: ({ux*1000:.3f}, {uy*1000:.3f}) mm")
            
            return True
            
        except np.linalg.LinAlgError as e:
            print(f"   ❌ 求解失败: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ 三角形单元测试失败: {e}")
        return False

def test_alternative_libs():
    """测试其他轻量级FEM库"""
    print("\n🔧 测试其他轻量级FEM库...")
    print("="*50)
    
    # 测试SfePy
    try:
        import subprocess
        result = subprocess.run([sys.executable, "-c", "import sfepy; print('SfePy可用')"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ SfePy 可用")
        else:
            print("   📦 尝试安装SfePy...")
            if install_package("sfepy"):
                print("   ✅ SfePy 安装成功")
            else:
                print("   ❌ SfePy 安装失败")
    except Exception:
        print("   ❌ SfePy 测试失败")
    
    # 测试meshio
    try:
        import meshio
        print("   ✅ meshio 可用 - 网格I/O库")
        
        # 创建简单网格
        import numpy as np
        points = np.array([
            [0.0, 0.0],
            [1.0, 0.0], 
            [0.0, 1.0]
        ])
        cells = [("triangle", np.array([[0, 1, 2]]))]
        mesh = meshio.Mesh(points, cells)
        print("   ✅ 成功创建简单三角形网格")
        
    except ImportError:
        print("   📦 安装meshio...")
        if install_package("meshio"):
            print("   ✅ meshio 安装成功") 
        else:
            print("   ❌ meshio 安装失败")
    
    # 测试GetFEM
    print("   🔧 测试GetFEM...")
    try:
        result = subprocess.run([sys.executable, "-c", "import getfem; print('GetFEM可用')"],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ GetFEM 可用")
        else:
            print("   ❌ GetFEM 不可用 (需要编译安装)")
    except Exception:
        print("   ❌ GetFEM 测试失败")

def main():
    """主函数"""
    print("🧪 Mac Apple Silicon有限元库测试")
    print("="*60)
    
    print("🎯 目标: 找到适合Mac的轻量级FEM库")
    print("📋 测试库: pyJive风格, SfePy, meshio, GetFEM")
    print()
    
    # 测试pyJive风格的实现
    pyjive_success = test_pyjive()
    
    # 测试其他库
    test_alternative_libs()
    
    print("\n📊 测试总结:")
    print("="*50)
    if pyjive_success:
        print("✅ 纯Python FEM框架: 成功")
        print("   - 完全基于NumPy/SciPy")
        print("   - 无编译依赖")
        print("   - 支持基本2D分析")
        print("   - 易于扩展和定制")
    else:
        print("❌ 纯Python FEM框架: 失败")
    
    print("\n🎯 推荐方案:")
    if pyjive_success:
        print("1. ⭐ 继续开发纯Python FEM框架")
        print("2. 🔧 结合meshio进行网格处理")
        print("3. 📊 使用matplotlib进行可视化")
        print("4. 🚀 专注于您的桥梁支座分析需求")
    else:
        print("1. 🔧 解决依赖问题后重试")
        print("2. 考虑使用已有的纯Python实现")

if __name__ == "__main__":
    main() 