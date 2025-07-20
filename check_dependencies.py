#!/usr/bin/env python3
"""
桥梁结构分析系统 - 依赖检查脚本
检查运行 main_enhanced_fixed.py 所需的所有文件和Python包
"""

import os
import sys
from importlib import import_module

def check_files():
    """检查必需的文件是否存在"""
    print("🔍 检查必需文件...")
    
    required_files = [
        "main_enhanced_fixed.py",
        "bridge_model_enhanced.py", 
        "visualization_enhanced.py",
        "requirements.txt"
    ]
    
    missing_files = []
    existing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            existing_files.append(file)
            print(f"  ✅ {file}")
        else:
            missing_files.append(file)
            print(f"  ❌ {file} (缺失)")
    
    print(f"\n📋 文件检查结果: {len(existing_files)}/{len(required_files)} 个文件存在")
    
    if missing_files:
        print(f"⚠️  缺失文件: {', '.join(missing_files)}")
        return False
    else:
        print("✅ 所有必需文件都存在")
        return True

def check_packages():
    """检查必需的Python包是否已安装"""
    print("\n🔍 检查Python包...")
    
    required_packages = [
        ("streamlit", "Streamlit Web框架"),
        ("numpy", "数值计算"),
        ("pandas", "数据处理"),
        ("matplotlib", "基础绘图"),
        ("plotly", "交互式图表"),
        ("scipy", "科学计算")
    ]
    
    optional_packages = [
        ("xara", "OpenSees接口 (专业分析需要)")
    ]
    
    missing_packages = []
    existing_packages = []
    
    # 检查必需包
    for package, description in required_packages:
        try:
            import_module(package)
            existing_packages.append(package)
            print(f"  ✅ {package} - {description}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package} - {description} (未安装)")
    
    # 检查可选包
    optional_missing = []
    for package, description in optional_packages:
        try:
            import_module(package)
            print(f"  ✅ {package} - {description}")
        except ImportError:
            optional_missing.append(package)
            print(f"  ⚠️  {package} - {description} (未安装)")
    
    print(f"\n📋 包检查结果: {len(existing_packages)}/{len(required_packages)} 个必需包已安装")
    
    if missing_packages:
        print(f"❌ 缺失必需包: {', '.join(missing_packages)}")
        print("\n💡 安装命令:")
        print("   pip install -r requirements.txt")
        return False
    else:
        print("✅ 所有必需包都已安装")
        
        if optional_missing:
            print(f"⚠️  缺失可选包: {', '.join(optional_missing)}")
            print("💡 专业分析需要安装: pip install xara")
        
        return True

def check_imports():
    """测试关键模块的导入"""
    print("\n🔍 测试模块导入...")
    
    test_imports = [
        ("bridge_model_enhanced", "BridgeModelXara"),
        ("visualization_enhanced", "BridgeVisualizer")
    ]
    
    import_success = []
    import_failures = []
    
    for module_name, class_name in test_imports:
        try:
            module = import_module(module_name)
            cls = getattr(module, class_name)
            import_success.append(f"{module_name}.{class_name}")
            print(f"  ✅ {module_name}.{class_name}")
        except ImportError as e:
            import_failures.append(f"{module_name}.{class_name}")
            print(f"  ❌ {module_name}.{class_name} - {e}")
        except AttributeError as e:
            import_failures.append(f"{module_name}.{class_name}")
            print(f"  ❌ {module_name}.{class_name} - 类不存在")
    
    print(f"\n📋 导入测试结果: {len(import_success)}/{len(test_imports)} 个模块导入成功")
    
    if import_failures:
        print(f"❌ 导入失败: {', '.join(import_failures)}")
        return False
    else:
        print("✅ 所有核心模块导入成功")
        return True

def print_system_info():
    """显示系统信息"""
    print("🖥️  系统信息:")
    print(f"  Python版本: {sys.version}")
    print(f"  操作系统: {os.name}")
    print(f"  当前目录: {os.getcwd()}")

def print_run_instructions():
    """显示运行指令"""
    print("\n🚀 运行指令:")
    print("   streamlit run main_enhanced_fixed.py")
    print("\n🌐 预期URL:")
    print("   http://localhost:8501")

def main():
    """主检查函数"""
    print("="*80)
    print("🌉 桥梁结构分析系统 - 依赖检查")
    print("="*80)
    
    print_system_info()
    print()
    
    # 检查文件
    files_ok = check_files()
    
    # 检查包
    packages_ok = check_packages()
    
    # 测试导入
    imports_ok = check_imports()
    
    # 总结
    print("\n" + "="*80)
    print("📋 检查总结")
    print("="*80)
    
    if files_ok and packages_ok and imports_ok:
        print("🎉 恭喜！所有依赖检查通过")
        print("✅ 系统已准备好运行桥梁结构分析系统")
        print_run_instructions()
    else:
        print("⚠️  检查发现问题，请解决以下问题后重新运行:")
        
        if not files_ok:
            print("   ❌ 缺失必需文件")
        if not packages_ok:
            print("   ❌ 缺失必需Python包")
        if not imports_ok:
            print("   ❌ 模块导入失败")
        
        print("\n💡 解决步骤:")
        print("   1. 确保所有文件在当前目录")
        print("   2. 运行: pip install -r requirements.txt")
        print("   3. 重新运行此检查脚本")

if __name__ == "__main__":
    main() 