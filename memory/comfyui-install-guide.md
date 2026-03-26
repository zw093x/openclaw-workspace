# ComfyUI v0.18.1 安装准备清单

**整理日期：** 2026-03-24
**目标版本：** ComfyUI v0.18.1（2026-03-23 发布）

---

## 一、环境要求

| 项目 | 要求 | 备注 |
|------|------|------|
| 操作系统 | Windows 10/11 64位 | 推荐 Windows |
| 显卡 | NVIDIA GPU（6GB+ 显存） | 推荐 8GB+，RTX 3060 起步 |
| Python | 3.10 ~ 3.12 | 便携版已内置 |
| 磁盘空间 | 至少 20GB | 模型文件较大，建议 50GB+ |
| 内存 | 16GB+ | 推荐 32GB |

---

## 二、下载资源

### 方式一：便携版（推荐新手，开箱即用）

根据显卡选择下载：

| 版本 | 下载链接 | 大小 |
|------|---------|------|
| **NVIDIA（CUDA 12.4）** | https://github.com/Comfy-Org/ComfyUI/releases/download/v0.18.1/ComfyUI_windows_portable_nvidia.7z | 1.87GB |
| **NVIDIA（CUDA 12.6）** | https://github.com/Comfy-Org/ComfyUI/releases/download/v0.18.1/ComfyUI_windows_portable_nvidia_cu126.7z | 1.85GB |
| **AMD** | https://github.com/Comfy-Org/ComfyUI/releases/download/v0.18.1/ComfyUI_windows_portable_amd.7z | 1.59GB |

> 💡 便携版已包含 Python、PyTorch、依赖库，解压即用。

### 方式二：Git 安装（推荐开发者）

```bash
# 1. 克隆仓库
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# 2. 切换到最新版本
git checkout v0.18.1

# 3. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 4. 安装 PyTorch（根据 CUDA 版本选择）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 5. 安装依赖
pip install -r requirements.txt
```

---

## 三、ComfyUI Manager（节点管理器）

**用途：** 一键安装/更新自定义节点

```bash
# 进入 ComfyUI 的 custom_nodes 目录
cd ComfyUI/custom_nodes

# 克隆 Manager
git clone https://github.com/ltdrdata/ComfyUI-Manager.git

# 重启 ComfyUI 即可生效
```

便携版路径：`ComfyUI_windows_portable\ComfyUI\custom_nodes\`

---

## 四、基础模型下载

### 必备模型

| 模型 | 用途 | 下载位置 | 放置目录 |
|------|------|---------|---------|
| **SD 1.5 基础模型** | 文生图入门 | civitai.com 或 huggingface.co | `models/checkpoints/` |
| **SDXL 1.0** | 高质量文生图 | huggingface.co/stabilityai | `models/checkpoints/` |
| **VAE（vae-ft-mse-840000）** | 图像质量提升 | huggingface.co | `models/vae/` |
| **CLIP 模型** | 文本编码 | 便携版已包含 | `models/clip/` |

### 推荐下载的 LoRA

| LoRA | 用途 | 来源 |
|------|------|------|
| Detail Tweaker | 细节增强 | civitai.com |
| Add More Details | 增加细节 | civitai.com |

### ControlNet 模型

| 模型 | 用途 | 目录 |
|------|------|------|
| control_v11p_sd15_canny | 边缘检测控制 | `models/controlnet/` |
| control_v11f1p_sd15_depth | 深度图控制 | `models/controlnet/` |
| control_v11p_sd15_openpose | 姿态控制 | `models/controlnet/` |

> 💡 ControlNet 模型可通过 ComfyUI Manager 自动下载

---

## 五、v0.18.0/0.18.1 更新要点

### v0.18.0（2026-03-21）
- ✅ **CacheProvider API** — 外部分布式缓存支持
- ✅ **腾讯 3D 节点修复** — TextToModel 和 ImageToModel 节点可用
- ✅ **ComfyUI Manager 4.1b5** — 内置更新
- ✅ **MXFP8 支持** — 更低显存占用的量化格式
- ✅ **--fp16-intermediates** — 中间值使用 fp16，节省显存
- ✅ **RAM 压力释放优化** — Windows 速度提升
- ✅ **前端 1.41.20** — UI 更新

### v0.18.1（2026-03-23）— 修复版
- 🔧 Canny 节点 fp16 兼容修复
- 🔧 fp16 中间值采样问题修复
- 🔧 fp16 中间值结果一致性修复
- 🔧 WAN VAE 光线/色彩问题修复

---

## 六、首次启动步骤

### 便携版
1. 解压 7z 文件到任意目录（路径不要有中文/空格）
2. 双击 `run_nvidia_gpu.bat` 启动
3. 浏览器自动打开 `http://127.0.0.1:8188`
4. 确认界面正常加载

### Git 安装版
1. 激活虚拟环境
2. 运行 `python main.py`
3. 浏览器打开 `http://127.0.0.1:8188`

### 启动参数（推荐）
```bash
# 基础启动
python main.py

# 开启监听（局域网访问）
python main.py --listen

# 使用 fp16 中间值（节省显存，v0.18.0+ 新功能）
python main.py --fp16-intermediates

# 低显存模式（6GB 以下）
python main.py --lowvram

# 指定端口
python main.py --port 8188
```

---

## 七、目录结构参考

```
ComfyUI/
├── main.py                  # 主程序入口
├── requirements.txt         # 依赖列表
├── models/
│   ├── checkpoints/         # 主模型（SD/SDXL）
│   ├── vae/                 # VAE 模型
│   ├── lora/                # LoRA 模型
│   ├── controlnet/          # ControlNet 模型
│   ├── clip/                # CLIP 模型
│   ├── unet/                # UNet 模型
│   └── upscale_models/      # 超分模型
├── custom_nodes/            # 自定义节点
│   └── ComfyUI-Manager/     # 节点管理器
├── output/                  # 生成图片输出目录
├── input/                   # 输入图片目录
└── workflows/               # 工作流 JSON 文件
```

---

## 八、常见问题

| 问题 | 解决方案 |
|------|---------|
| 启动报错 CUDA 不可用 | 确认安装 NVIDIA 驱动 >= 535.x |
| 显存不足 OOM | 加 `--lowvram` 或 `--fp16-intermediates` |
| 模型加载慢 | 确认模型放在正确目录，检查文件完整性 |
| 8188 端口被占用 | `--port 8189` 或其他端口 |
| 便携版解压失败 | 用 7-Zip 解压，不要用 WinRAR |

---

## ✅ 准备检查清单

- [ ] 下载 ComfyUI v0.18.1 便携版
- [ ] 准备至少 20GB 磁盘空间
- [ ] 确认 NVIDIA 驱动版本 >= 535.x
- [ ] 下载 SD 1.5 或 SDXL 基础模型
- [ ] 下载 VAE 模型
- [ ] 准备 ControlNet 模型（可选，后续通过 Manager 安装）

---

*明天开始搭建环境。如有问题随时联系。*
