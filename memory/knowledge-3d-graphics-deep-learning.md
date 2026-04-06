# 3D计算机图形学深度学习——论文知识库
> 基于Computer Graphics + Deep Learning课程文献整理
> 包含：神经渲染 / 3D表征 / 隐式神经 / 场景生成
> 更新：2026-04-06
> 适合：ComfyUI学习计划、AI+3D建模流水线

---

## 一、隐式神经表征（Implicit Neural Representations）

### 1.1 核心思想

**不存储3D点/网格，而是用神经网络连续函数表示3D场景**

```
传统：离散存储（像素、体素、点云）
隐式：f(x) = 颜色/密度/符号距离 → 任意分辨率，内存小
```

### 1.2 Occupancy Fields（Occupancy Net）

```
论文：Occupancy Networks: Learning 3D Reconstruction in Function Space (2019)

核心：MLP直接拟合占用概率
  f(x): R³ → [0,1]  → x点是否被物体表面占用
  等值面提取：用Marching Cubes从占用概率提取Mesh

关键创新：
  - 不存储3D形状，显式→连续
  - 分辨率无关（任意分辨率可采样）
  - 可以自然融合几何先验

Loss = BCE(occ(x), gt_occ(x))

问题：需要3D监督数据（Ground Truth占用）
```

### 1.3 NeRF（神经辐射场）

```
论文：NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis (ECCV 2020)

核心：用MLP表示5D辐射场
  F_θ: (x, y, z, θ, φ) → (c, σ)
  x = 3D位置
  (θ, φ) = 观察方向
  c = RGB颜色
  σ = 体积密度

体积渲染公式：
  C(r) = ∫_{t_n}^{t_f} T(t) · σ(r(t)) · c(r(t), d) dt
  其中 T(t) = exp(-∫_{t_n}^{t} σ(r(s)) ds

训练策略：
  1. 每条光线采样N个点（粗采样）
  2. 分层采样（细采样）：在σ大的区域多采样
  3. MSE Loss：预测RGB与真实RGB的均方误差

关键问题：
  - 每场景需要数小时训练
  - 推理极慢（每场景数分钟）
  - 无法编辑场景

改进方向：
  - 加速（Instant NGP、Plenoxels）
  - 可编辑（NeRFstudio、NeRF editing）
  - 无界场景（mip-NeRF360、UE4-NeRF）
```

### 1.4 密度SLAM（Dense SLAM）

```
论文：Touchstone: Differentiable Rendering Foundation for (Large-scale) Mesh Recovery (2024)
    Neural Implicit SLAM: Indoor and Outdoor Scene Reconstruction (2023)

核心：SLAM = Simultaneous Localization and Mapping
  同时做：建图 + 定位
  神经隐式SLAM：用NeRF类方法做实时建图

关键差异 vs 传统NeRF：
  - 需要实时（30fps+）→ 用更快的表征
  - 增量更新（新的帧加入）→ 不从头训练
  - 主动追踪相机位姿
```

---

## 二、基于学习的渲染（Learning-based Rendering）

### 2.1 可微渲染（Differentiable Rendering）

```
论文：Differential Rendering: A Survey (2021)
    Differentiable Image Rendering (CVPR 2021)

核心：渲染函数可微 → 梯度反向传播 → 端到端优化

传统渲染：不可微（离散采样、光线-物体求交）
可微渲染：近似梯度，使其可微

方法1：Mesh可微渲染
  - Soft rasterization：概率化几何
  - 通过深度/法线等的梯度近似Mesh梯度

方法2：体积可微渲染
  - NeRF体积渲染天然可微
  - σ(r(t))的梯度 = 密度梯度

方法3：光栅化可微
  - 近似离散采样操作为连续可微函数
  - g(k) = 1/(1 + exp(-k·w))  # 软化argmax
```

### 2.2 Neural Rendering（神经渲染）

```
论文：Neural Rendering: A Survey (CVPR 2021)

定义：用神经网络替代/增强渲染器

主要方法：
1. 基于NeRF的神经渲染
   - NeRF → 3D一致新视角
   - G NeRF → 无相机位姿监督
   - NeRF++ → 无界场景

2. 基于GAN的神经渲染
   - GAN用于Novel View Synthesis
   - 在潜在空间生成新视角

3. 基于点云的神经渲染
   - PointsNeRF → 基于点的NeRF
   - 共享特征点 → 生成新视角

4. 体积神经渲染
   - SRN → 神经体积表示
   - Neural Volume → 体积密度场
```

### 2.3 GAN用于Novel View Synthesis

```
论文：GANs for Novel View Synthesis (2022)

核心：用GAN的对抗训练生成新视角

Challenge：
  - 传统插值方法无法生成新视角的几何
  - 需要3D一致性（不同视角看同一物体一致）

方法：
  - View Synthesis GAN：判别器判别视角真实性
  - 3D一致约束：多视角几何一致性损失
```

### 2.4 Point-Based Neural Rendering（点云神经渲染）

```
论文：Point-NeRF: Ray-based 3D Point Neural Fields (CVPR 2022)

核心：点云 + 神经场结合

优势：
  - 点云稀疏但精确 → 几何好
  - 神经场连续 → 渲染质量好

Point-NeRF：
  1. 特征点云：每点有D维几何特征
  2. 神经场：用MLP从点特征+位置预测σ和c
  3. 体积渲染：同NeRF
  4. 预训练3D GAN提供初始化点云
```

---

## 三、混合表征（Hybrid Representations）

### 3.1 NeRF与高斯溅射的混合

```
核心：NeRF（连续隐式）+ 高斯（显式稀疏点）

3D Gaussian Splatting (3DGS) = 显式3D高斯函数
  - 位置μ ∈ R³
  - 协方差Σ ∈ R^{3×3}（椭球形）
  - 颜色c ∈ R³
  - 透明度α ∈ R

渲染（溅射）：
  - 不用光线步进
  - 将3D高斯投影到2D图像平面
  - 按深度排序
  - alpha-blending合成

混合优势：
  - NeRF精度高但慢 → 高斯快
  - 高斯稀疏但需初始化 → NeRF提供初始化
  - 编辑性：高斯显式，可直接操作

应用场景：
  - 实时3D重建（SLAM + 3DGS）
  - 文物数字化（高精度+实时）
  - 影视制作（可编辑3D场景）
```

---

## 四、显式神经表征（Explicit Neural Representations）

### 4.1 Mesh-based（网格）

```
论文：Mesh R-CNN (ICCV 2019)
    Texture Fields: Learning Texture Representation in Deep Space (2019)

Mesh R-CNN：
  - Mask R-CNN做2D检测
  - → 3D Mesh预测
  - → Mesh细化（GRSop + Mesh refinement）

Texture Fields（纹理场）：
  - 不预测Mesh
  - 直接学习：3D位置 → 纹理颜色
  - 可以生成高质量纹理（无需UV展开）

可微Mesh生成：
  - 学一个隐式SDF + Marching Cubes提取Mesh
  - 或直接用点云 + Poisson Surface Reconstruction
```

### 4.2 可微网格生成

```
论文：Differentiable Mesh Generation (2022)

核心：从图像/深度直接生成Mesh

流程：
  1. 图像 → 深度估计 / 3D预测
  2. 深度 → 点云
  3. 点云 → Mesh（Poisson / Delaunay）
  4. Mesh细化（可微渲染反馈）

挑战：
  - 网格拓扑（面数、连接性）难以优化
  - SDF + Marching Cubes：拓扑由等值面决定，难以控制
```

---

## 五、点云表征（Point Cloud）

### 5.1 PointNet / PointNet++

```
论文：PointNet: Deep Learning on Point Sets (CVPR 2017)
    PointNet++: Hierarchical Point Learning (NeurIPS 2017)

PointNet：
  - 输入：N × 3 点云（无结构）
  - 共享MLP：每个点独立映射到高维特征
  - Max Pooling：对称函数聚合全局特征
  - 分割/分类头

问题：丢失了局部几何信息

PointNet++：
  - 层级采样：远处→近处→局部细节
  - Set Abstraction = Sampling + Grouping + PointNet
  - 解决了局部几何感知问题

3D应用：
  - 点云分类、分割、检测
  - 点云生成（反问题）
```

### 5.2 点云神经渲染

```
Point-NeRF (CVPR 2022)：
  - 用预训练3D GAN生成初始点云
  - 每点有神经特征
  - MLP解码器：点特征→σ和c
  - 体积渲染（同NeRF）

优势 vs NeRF：
  - 显式几何初始化（点云）
  - 训练速度更快（预训练特征）
  - 编辑更容易（点云可操作）
```

---

## 六、符号距离场（SDF）

### 6.1 DeepSDF

```
论文：DeepSDF: Learning Continuous Signed Distance Functions (CVPR 2020)

核心：MLP拟合SDF
  f_θ(x) ∈ R → x到最近表面的符号距离
  f(x) < 0 → 内部
  f(x) = 0 → 表面
  f(x) > 0 → 外部

训练：
  - Auto-decoder：输入位置x+Latent Code z
  - f_θ(x, z) = SDF
  - 优化：θ和z同时优化

优势：
  - 连续：任意分辨率
  - 可插值：Latent Space插值 → Shape插值
  - 可预测：未知类别的SDF
```

### 6.2 SDF Studio / IM-Net

```
IM-Net (CVPR 2019)：
  - 输入：坐标x + 特征z
  - 输出：二值占用（occupancy）
  - 不同于DeepSDF：IM-Net预测占用，DeepSDF预测SDF

SDF Studio：
  - 集成多种SDF方法
  - 可微SDF渲染工具
  - 支持NeRF + SDF混合
```

---

## 七、多视角立体重建（MVS）

### 7.1 MVSNet系列

```
论文：MVSNet: Depth Inference from Multi-Soft 3D Volumes (ECCV 2018)
    PatchmatchNet (ICCV 2021)
    MVDepthNet (ECCV 2018)
    Depthsup (ICCV 2019)

MVSNet：
  - 输入：多视角图像 + 相机位姿
  - 构建3D cost volume
  - 3D CNN正则化
  - 软argmin → 深度图

Cost Volume（成本体）：
  - 对于每个视角像素，假设不同深度
  - 计算不同深度下的特征相似度
  - 3D cost = 特征差异的平均

Depthsup：
  - 无监督：用光度一致性作为监督
  - 多视角渲染：I_i(render) 应 ≈ I_j
```

---

## 八、场景表征与生成（Scene Representation & Generation）

### 8.1 语义场景补全

```
Semantic Scene Completion (SSC)：
  - 输入：单视角深度图
  - 输出：3D语义场景（含可见+不可见区域）

数据集：SemanticKITTI
  -  KITTI 3D语义分割 + 场景完成

方法：
  - SSCNet：3D occupancy grid + 语义标签
  - 2D→3D提升：TSDF融合
```

### 8.2 场景数据集

```
Place360：全景场景理解
SceneNet：室内轨迹RGB-D数据集
Structured3D：结构化3D室内场景（CAD模型）
SceneGraph：场景图（物体关系）

关键应用：
  - 场景生成：给定描述 → 生成3D场景
  - 场景编辑：改变物体/布局
  - 物理推理：场景中的物理关系
```

---

## 九、渲染的深度学习（Deep Learning for Rendering）

### 9.1 真实场景NeRF

```
NeRF in the Wild (ICCV 2021)：
  - 非理想条件下NeRF
  - 暂态建模（光线穿过透明物体）
  - 外观变化（不同光照/天气）

Unbounded NeRF（mip-NeRF360）：
  - 360°全景NeRF（室外大场景）
  - 用proposal网络避免在大空间内采样过密
  - 束调整（Bundle Adjustment）优化相机

Human NeRF：
  - 人体专属NeRF
  - SMPL先验：人体形状标准化
  - 动态NeRF：人体运动建模
```

### 9.2 Instant NGP（即时NGP）

```
论文：Instant Neural Graphics Primitives (SIGGRAPH 2022)

核心：多分辨率哈希编码 → 极速NeRF

架构：
  - 输入坐标x → Multi-Resolution Hash Encoding
  - 不同分辨率的网格节点存储特征
  - 插值 + MLP解码
  - 训练速度：提升1000倍（分钟级 vs 小时级）

关键技术：
  - 可学习的网格节点（通过MLP反向传播优化）
  - 粗→精搜索：快速定位表面
  - CUDA实现：GPU并行
```

---

## 十、P工3D建模工作流建议

### 10.1 AI+3D技术地图

```
当前最实用（可本地运行）：
  ⭐⭐⭐ Instant NGP → 快速3D场景重建（需多视角图）
  ⭐⭐⭐ 3D Gaussian Splatting → 高质量实时渲染（可编辑）
  ⭐⭐⭐ TripoSG → 2D图→3D模型（API可用）

ComfyUI集成路径：
  2D图 → TripoSG/Meshy API → 3D模型
  → ComfyUI工作流（手动精修）
  → 最终输出

长期技术储备：
  - NeRF → 场景表征基础
  - SDF → 可编辑3D几何
  - 3DGS → 当前最佳渲染质量
```

### 10.2 论文阅读优先级（P工视角）

```
第一优先（最实用）：
  1. Instant NGP (2022) — 速度革命
  2. 3D Gaussian Splatting (2023) — 质量+速度
  3. TripoSG (2024) — 2D→3D SOTA

第二优先（理解原理）：
  4. NeRF (2020) — 神经渲染基础
  5. DeepSDF (2020) — SDF+隐式表征
  6. Point-NeRF (2022) — 点云+神经渲染

第三优先（研究前沿）：
  7. Mesh R-CNN — Mesh生成
  8. Neural Volume — 体积渲染
  9. Semantic Scene Completion — 3D语义理解
```

---

## 关键论文索引

| 论文 | 年 | arXiv | 核心贡献 |
|------|---|-------|---------|
| Occupancy Networks | 2019 | — | 隐式占用网络 |
| NeRF | 2020 | 2003.13425 | 神经辐射场 |
| PointNet | 2017 | 1612.00593 | 点云深度学习 |
| PointNet++ | 2017 | 1706.02413 | 层级点云学习 |
| DeepSDF | 2020 | 1901.05103 | SDF隐式表征 |
| Mesh R-CNN | 2019 | 1906.02739 | Mesh生成 |
| Instant NGP | 2022 | 2201.01289 | 极速NeRF |
| 3D Gaussian Splatting | 2023 | 2308.04079 | 高斯渲染 |
| Point-NeRF | 2022 | 2201.10433 | 点云+NeRF |
| MVSNet | 2018 | 1804.02502 | 多视角立体重建 |
| Touchstone | 2024 | 2401.14483 | 可微渲染 |

---
*基于Computer Graphics + DL课程整理，适合3D AI建模流水线学习*
