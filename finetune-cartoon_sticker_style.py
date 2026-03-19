# Step 1: Install the environment
!nvidia-smi
!pip install --upgrade protobuf==5.29.1
!pip install numpy==1.26.0
!pip install wandb==0.16.3
!pip install --upgrade accelerate diffusers[training]
!pip install -q transformers datasets peft bitsandbytes xformers huggingface_hub

# Step 2: Upload and check the training data
import os
image_dir = "/content/sticker_images"
os.makedirs(image_dir, exist_ok=True)
images = os.listdir(image_dir)
print(f"find {len(images)} picturs：{images[:]}")
if len(images) == 0:
    raise Exception("upload /content/sticker_images first！")

# Diffusers
import os
os.environ["WANDB_DISABLED"] = "true"
!git clone https://github.com/huggingface/diffusers.git
%cd /content/diffusers

%cd /content/diffusers
!pip install -e ".[torch]"
import diffusers

# Step 4: Training Lora
%cd /content/diffusers
!python examples/dreambooth/train_dreambooth_lora.py \
  --pretrained_model_name_or_path="runwayml/stable-diffusion-v1-5" \
  --instance_data_dir="/content/sticker_images" \
  --output_dir="/content/lora_sticker_model" \
  --instance_prompt="a sticker in <sticker-style> style" \
  --resolution=512 \
  --train_batch_size=1 \
  --gradient_accumulation_steps=4 \
  --learning_rate=1e-4 \
  --lr_scheduler="constant" \
  --lr_warmup_steps=0 \
  --max_train_steps=800 \
  --mixed_precision="fp16" \
  --use_8bit_adam
import os
model_dir = "/content/lora_sticker_model"
print("exist?", os.path.exists(model_dir))

# Step 5：Testing
from diffusers import StableDiffusionPipeline
import torch
# loading models
pipe=StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda")
pipe.unet.load_attn_procs("/content/lora_sticker_model")

# generating pictures
prompt="a cute cat, <sticker-style> style, vibrant colors, sticker design, white background"
image=pipe(prompt, num_inference_steps=50).images[0]
print(image)

# Step 6: Save the model to the Hugging face
import os
model_dir = "/content/lora_sticker_model"
print("exsit？", os.path.exists(model_dir))
if os.path.exists(model_dir):
    print("list：", os.listdir(model_dir))

import json
import os

model_dir = "/content/lora_sticker_model"
config = {
    "base_model_name_or_path": "runwayml/stable-diffusion-v1-5",
    "revision": None,
    "rank": 8,
    "alpha": 16,
    "dropout": 0.1,
    "target_modules": ["to_q", "to_k", "to_v", "to_out.0"]
}
with open(os.path.join(model_dir, "adapter_config.json"), "w") as f:
    json.dump(config, f, indent=2)

print("adapter_config.json existed", model_dir)

from google.colab import files

files.download(os.path.join(model_dir, "pytorch_lora_weights.safetensors"))
files.download(os.path.join(model_dir, "adapter_config.json"))

from diffusers import StableDiffusionPipeline
pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16).to("cuda")
pipe.unet.load_attn_procs("Lilian0703/sticker-lora-cartoon")
image = pipe("a cute cat, <sticker-style> style").images[0]
print(image)
