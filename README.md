# 桥梁有限元分析系统 - 纯FEM版本

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)

专业的连续梁桥有限元分析系统，基于OpenSees/xara引擎的精确结构计算。

## 🌟 核心特性

- **🎯 纯FEM分析**: 基于OpenSees/xara专业有限元引擎，消除所有物理简化
- **🔬 精确计算**: elasticBeamColumn单元，3DOF/节点，eleForce()内力提取
- **🔧 个性化配置**: 每个支座可独立选择 Fixed Pin 或 Roller 类型
- **📐 精密控制**: 1mm精度的墩台高度调节，强制位移模拟施工误差
- **🏗️ 梁刚度调节**: 0.5×-2.0×弹性模量连续可调
- **📊 专业分析**: 基于虚功原理的弯矩图、剪力图、支座反力分析
- **🌐 Web界面**: 现代化Streamlit界面，实时参数配置和结果展示

## 🚀 快速开始

### 环境要求
- Python 3.8+
- **必需依赖**：xara (OpenSees Python接口)
- 其他依赖：Streamlit, NumPy, Pandas, Plotly

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/darcywudc/simplebridgetwincopilot.git
cd simplebridgetwincopilot

# 2. 切换到生产分支
git checkout production-clean

# 3. 安装依赖
pip install -r requirements.txt
pip install xara

# 4. 依赖检查（可选）
python check_dependencies.py

# 5. 运行应用
streamlit run main_enhanced_fixed.py
```

应用将在浏览器中打开：**http://localhost:8501**

## 🏗️ 项目结构

### 核心文件
```
├── main_enhanced_fixed.py      # 🌐 主程序 - Streamlit Web界面
├── bridge_model_enhanced.py    # 🎯 FEM分析引擎 - OpenSees/xara
├── visualization_enhanced.py  # 📊 图表可视化模块
├── requirements.txt           # 📦 Python依赖清单
├── check_dependencies.py      # ✅ 环境检查工具
└── 运行依赖关系.md             # 📋 详细依赖说明
```

### 技术架构
- **前端**: Streamlit Web框架
- **分析引擎**: OpenSees/xara 纯有限元计算
- **可视化**: Plotly交互式图表
- **计算核心**: NumPy, SciPy科学计算栈

## 💡 主要功能

### 🔧 支座类型配置
- **个别设置**: 每个墩台可独立选择支座类型
- **Fixed Pin**: 固定铰接 (dx=1, dy=1, rz=0)
- **Roller**: 滑动支座 (dx=0, dy=1, rz=0)
- **智能验证**: 自动检查结构稳定性

### 📐 墩台高度控制
- **1mm精度**: 精确到毫米级的高度调节
- **快捷按钮**: ±1mm、±1cm增减按钮
- **预设方案**: 工程值、测试值、均匀值
- **强制位移**: 真实模拟施工高度误差效应

### 🏗️ 梁刚度配置
- **连续调节**: 0.5×-2.0×弹性模量
- **预设方案**: 低刚度(柔性)、标准刚度、高刚度(硬梁)
- **实时显示**: 弹性模量和抗弯刚度EI值

### 📊 结构分析结果
- **弯矩图**: 基于OpenSees `eleForce()` 精确计算
- **剪力图**: 单元两端剪力分布
- **支座反力**: 详细的反力表格和分布图
- **计算原理**: 完整的有限元计算方法说明

## 🔬 技术细节

### 有限元理论基础
- **单元类型**: `elasticBeamColumn` - 欧拉-伯努利梁单元
- **节点自由度**: 3 DOF/节点 (dx, dy, rz)
- **求解方法**: 静力分析，LoadControl积分器，基于虚功原理
- **内力提取**: `eleForce()` 获取 [N1, V1, M1, N2, V2, M2]

### 刚度矩阵组装
```python
# 单元刚度矩阵 (局部坐标系)
K_local = [[EA/L, 0, 0, -EA/L, 0, 0],
           [0, 12EI/L³, 6EI/L², 0, -12EI/L³, 6EI/L²],
           [0, 6EI/L², 4EI/L, 0, -6EI/L², 2EI/L],
           [-EA/L, 0, 0, EA/L, 0, 0],
           [0, -12EI/L³, -6EI/L², 0, 12EI/L³, -6EI/L²],
           [0, 6EI/L², 2EI/L, 0, -6EI/L², 4EI/L]]
```

### 墩台高度效应
- **物理原理**: 高度差直接作为强制位移边界条件
- **实现方法**: OpenSees `sp()` 命令施加强制位移
- **精度**: 毫米级高度差的结构响应，无物理近似

### 支座反力计算
```python
model.reactions()  # 激活反力计算
reaction = model.nodeReaction(node_id)  # [Fx, Fy, Mz]
```

## 📋 使用指南

### 1. 配置桥梁参数
- 在侧边栏设置桥梁长度、截面尺寸、材料参数
- 选择梁刚度倍数 (0.5×-2.0×)

### 2. 设置支座类型
- 为每个墩台选择 Fixed Pin 或 Roller
- 系统自动验证配置合理性

### 3. 调节墩台高度
- 使用±按钮或直接输入精确高度值
- 可选预设的工程值或测试值

### 4. 施加荷载
- 输入均布荷载强度 (kN/m)
- 点击"更新荷载"应用

### 5. 运行分析
- 点击"🚀 运行结构分析"按钮
- 在弯矩图、剪力图、支座反力标签页查看结果

## 🎯 工程应用

### 设计验证
- 不同支座配置对内力分布的影响
- 施工高度误差的结构响应分析
- 梁刚度变化的敏感性研究

### 教学演示
- 连续梁理论的可视化验证
- 支座约束对结构行为的影响
- 有限元方法的实际应用

### 施工指导
- 墩台高度控制精度要求
- 支座更换/维修的影响评估
- 不同刚度梁的结构表现

## ⚠️ 注意事项

- 确保安装了 `xara` 包以使用专业分析功能
- 结果仅供参考，实际工程应用需要专业验证
- 系统假设线性弹性材料和小变形理论

## 🔗 相关资源

- **OpenSees**: [opensees.berkeley.edu](https://opensees.berkeley.edu/)
- **Streamlit**: [streamlit.io](https://streamlit.io/)
- **技术支持**: 通过GitHub Issues提交问题

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

**桥梁结构分析系统** | 专业·精确·易用 | 基于OpenSees有限元引擎 