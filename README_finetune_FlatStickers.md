# 🎯 LoRA微调模块 (LoRA Fine-tuning Module for Flat Stickers)
**声明**: 该project共进行三种风格的微调，本文件所述仅针对扁平化风格贴纸微调(Flat stickers)  
**负责人**: [@luwang](https://github.com/Bulu04bulu)
<div align="center">
  
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-orange.svg)
![Diffusers](https://img.shields.io/badge/Diffusers-0.21+-green.svg)
![LoRA](https://img.shields.io/badge/LoRA-PEFT-red.svg)

**DreamBooth + LoRA 贴纸风格微调模块**

[技术原理](#-技术原理) • [文件结构](#-文件结构) • [使用方法](#-使用方法) • [输出说明](#-输出说明) • [常见问题](#-常见问题)

</div>

---

## 📋 模块概述

### 职责说明
本模块负责**贴纸风格的模型微调**，后续模块依赖本模块输出的LoRA权重。

### 输入输出
```
输入: 27张同一风格的贴纸图像（不同动物）
↓
微调过程
↓
输出: LoRA权重文件（10-50MB）
├── lora_final/ # 最终权重
├── lora_step_200/ # 中间checkpoint
└── lora_step_400/
...
```

---

## 🔬 技术原理

### 1. 为什么需要微调？
预训练的Stable Diffusion模型能生成通用图像，但**不懂特定风格**。微调的目的是让模型学会特定的贴纸风格。
### 2. DreamBooth原理

DreamBooth通过给模型引入一个**稀有token**（如"sks"）来学习新概念：

```python
# 训练时的prompt格式
prompt = f"a {style_token} {animal} {style_description}"
# 例如: "a sks cat sticker style"

# 使用时的prompt格式（其他模块用）
prompt = f"a sks {animal} sticker style"
# 例如: "a sks dog sticker style"
```

### 3. LoRA原理
LoRA（Low-Rank Adaptation）通过插入小矩阵来微调，只训练1-3%的参数：

传统微调: 更新全部参数 → 文件大(5GB)、训练慢
LoRA微调: 只更新小矩阵 → 文件小(10-50MB)、训练快 ✅

## 📁 文件结构
```python
lora_finetune/  
├── train_lora_colab.py # 主训练脚本    
├── data/ # 训练数据
│ └── my_sticker_style/  
│ ├── cat_001.png  
│ ├── cat_002.png  
│ ├── dog_001.png  
│ └── …  
├── output/ # 训练输出 
│ ├── lora_step_200/ # 200步checkpoint  
│ ├── lora_step_400/ # 400步checkpoint  
│ ├── lora_step_600/    
│ ├── lora_step_800/    
│ ├── lora_step_1000/   
│ └── lora_final/ # 最终LoRA权重 ⭐  
├── validation_samples/ # 训练中生成的验证图 
└── augmented_data/ # 数据增强后的图片（临时）  
```

## 🚀 使用方法
### 环境准备
```python
pip install torch torchvision torchaudio
pip install diffusers accelerate transformers peft
pip install pillow tqdm
```
### 数据准备
**关键要求：训练图片必须是同一风格的贴纸，文件名包含动物英文名。**

```python
# ✅ 正确的文件命名
data/my_sticker_style/
├── cat_001.png      
├── cat_002.png
├── dog_001.png      
├── rabbit_001.png   
├── bear_001.png     
└── fox_001.png 
...
```
### 开始训练
```python
# 完整训练（1200步，约20-25分钟）
python train_lora_colab.py --train

# 快速测试
python train_lora_colab.py --test
```

### 训练参数说明
| **参数**                      | **默认值** |      **说明**       |
|:---------------------------:|:-------:|:-----------------:|
| max_train_steps             | 1200    | 训练步数，越多效果越好但可能过拟合 |
| learning_rate               | 5e-5    |    学习率，越小训练越稳定    |
| lora_rank                   | 8       |  LoRA秩，越大学习能力越强   |
| train_batch_size            | 1       |   批次大小，显存不足时减小    |
| gradient_accumulation_steps | 4       |  梯度累积，模拟更大batch   |

## 📤 输出说明
### 1. LoRA权重文件
训练完成后，output/lora_final/目录包含：
```
lora_final/
├── adapter_config.json   # LoRA配置
├── adapter_model.safetensors    # LoRA权重（核心文件）
└── README.md             # 说明文件
```
### 2. 如何使用LoRA
```python
from diffusers import StableDiffusionPipeline
from peft import PeftModel

# 加载基础模型
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
).to("cuda")

# 加载LoRA权重
pipe.unet = PeftModel.from_pretrained(pipe.unet, "path/to/lora_final")

# 生成贴纸
prompt = "a sks cat sticker style"  # 注意：必须用"sks"token
image = pipe(prompt).images[0]
```
### 3. 训练checkpoint
训练过程中每200步保存一次checkpoint，按时间顺序：

| **Checkpoint** |    **说明**    |
|:--------------:|:------------:|
| lora_step_200  | 风格初现，可能不够稳定  |
| lora_step_400  |    细节开始丰富    |
| lora_step_600  |    风格基本成型    |
| lora_step_800  |   效果最佳（通常）   |
| lora_step_1000 |   可能开始过拟合    |
| lora_final     | 最终版本（自动选择最佳） |

## 🔗 与其他模块的接口
```
# VLM组：
# 1. 风格token是 "sks"
# 2. 生成prompt的格式: f"a sks {animal} sticker style"

# 图像生成组：
# 1. LoRA权重路径: "output/lora_final/"
# 2. 加载方法见上方代码示例

# 评估组：
# 1. 不同checkpoint的路径
# 2. 训练过程中的验证图路径: "validation_samples/"
```