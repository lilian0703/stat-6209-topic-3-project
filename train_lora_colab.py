"""
LoRA + DreamBooth Train Scripts
"""

import os
import torch
import argparse
from PIL import Image
from diffusers import StableDiffusionPipeline, DDPMScheduler
from diffusers.optimization import get_scheduler
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from tqdm import tqdm
import numpy as np
from accelerate import Accelerator
from pathlib import Path
import shutil
import time
from diffusers.utils.import_utils import is_peft_available
if is_peft_available():
    from peft import LoraConfig, get_peft_model


class Config:
    # path
    drive_path = "/content/drive/MyDrive/sticker_project"
    data_dir = os.path.join(drive_path, "data/my_sticker_style")
    augmented_dir = "/content/augmented_data"
    output_dir = "/content/lora_output"
    drive_output_dir = os.path.join(drive_path, "lora_weights")
    validation_dir = "/content/validation_samples"

    # Train
    pretrained_model_name = "runwayml/stable-diffusion-v1-5"
    resolution = 512
    train_batch_size = 1
    gradient_accumulation_steps = 4
    learning_rate = 5e-5
    lr_scheduler = "constant"
    lr_warmup_steps = 50

    # LoRA
    lora_rank = 8
    lora_alpha = 16
    lora_dropout = 0.1

    # Train Step
    max_train_steps = 1200
    checkpointing_steps = 200

    # style prompt
    style_token = "sks"
    style_description = "sticker style"

    # validation prompts
    validation_prompts = [
        "a sks cat sticker style",
        "a sks dog sticker style",
        "a sks rabbit sticker style",
    ]
    validation_steps = 200

    # over_fit test
    early_stop_threshold = 3

    # data augmentation
    do_augmentation = True
    augmentation_multiplier = 4  #total: 27*5=135

    mixed_precision = "fp16"

    def __init__(self):
        os.makedirs(self.drive_output_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)


class DataAugmentor:
    def __init__(self, resolution=512):
        self.resolution = resolution
        self.augmentations = transforms.Compose([
            # 1. Random horizontal flip: 50% probability to flip the image horizontally
            transforms.RandomHorizontalFlip(p=0.5),
            # 2. Random rotation: Rotate randomly within ±5 degrees
            transforms.RandomRotation(degrees=5),
            # 3. Random crop and resize
            transforms.RandomResizedCrop(
                size=resolution,
                scale=(0.9, 1.0),
                ratio=(1.0, 1.0)
            ),
            # 4. Color jitter: Slightly adjust image color properties
            transforms.ColorJitter(
                brightness=0.1,
                contrast=0.1,
                saturation=0.1,
                hue=0.05
            ),
        ])

    def augment_dataset(self, input_dir, output_dir, multiplier=4):
        os.makedirs(output_dir, exist_ok=True)

        image_files = [f for f in os.listdir(input_dir)
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        print(f"Found {len(image_files)} original images")
        print(f"Generating {multiplier} augmented versions per image....")

        for img_file in tqdm(image_files, desc="Data Augmentation"):
            img_path = os.path.join(input_dir, img_file)
            img = Image.open(img_path).convert("RGB")
            img = img.resize((self.resolution, self.resolution), Image.LANCZOS)

            name, ext = os.path.splitext(img_file)
            img.save(os.path.join(output_dir, f"{name}_orig{ext}"))

            for i in range(multiplier):
                augmented = self.augmentations(img)
                augmented.save(os.path.join(output_dir, f"{name}_aug{i}{ext}"))

        total = len(image_files) * (multiplier + 1)
        print(f"✅ Augmentation complete! Total {total} images")


class StickerDataset(Dataset):
    def __init__(self, data_dir, tokenizer, style_token="sks", style_desc="sticker style", size=512):
        self.data_dir = data_dir
        self.tokenizer = tokenizer
        self.style_token = style_token
        self.style_desc = style_desc
        self.size = size

        self.image_paths = []
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            self.image_paths.extend(Path(data_dir).glob(ext))

        self.animal_names = self._extract_animal_names()

        self.transform = transforms.Compose([
            transforms.Resize(size, interpolation=transforms.InterpolationMode.BILINEAR),
            transforms.CenterCrop(size),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5]),
        ])

    def _extract_animal_names(self):
        animal_names = []
        common_animals = ['cat', 'dog', 'rabbit', 'bear', 'fox', 'panda', 'lion',
                         'tiger', 'elephant', 'giraffe', 'monkey', 'bird', 'fish']

        for path in self.image_paths:
            filename = path.stem.lower()
            found = False
            for animal in common_animals:
                if animal in filename:
                    animal_names.append(animal)
                    found = True
                    break
            if not found:
                animal_names.append("animal")

        return animal_names

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        image_path = self.image_paths[idx]
        image = Image.open(image_path).convert("RGB")
        image = self.transform(image)

        animal = self.animal_names[idx]
        prompt = f"a {self.style_token} {animal} {self.style_desc}"

        return {
            "pixel_values": image,
            "prompt": prompt,
            "animal": animal,
        }


def train():
    config = Config()

    torch.cuda.empty_cache()

    # Initial accelerator
    accelerator = Accelerator(
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        mixed_precision=config.mixed_precision,
    )

    # create output dir
    os.makedirs(config.output_dir, exist_ok=True)
    os.makedirs(config.validation_dir, exist_ok=True)

    # 1. Data Augmentation
    if config.do_augmentation:
        print("\n=== Step 1: Data Augmentation ===")
        augmentor = DataAugmentor(resolution=config.resolution)
        augmentor.augment_dataset(
            config.data_dir,
            config.augmented_dir,
            multiplier=config.augmentation_multiplier
        )
        train_data_dir = config.augmented_dir
    else:
        train_data_dir = config.data_dir

    # 2. Load Model
    print("\n=== Step 2: Load Pretrained model ===")
    pipe = StableDiffusionPipeline.from_pretrained(
        config.pretrained_model_name,
        # torch_dtype=torch.float16,
        safety_checker=None,
        requires_safety_checker=False,
    ).to("cuda")
    
    pipe.enable_attention_slicing()

    # Freeze parameters
    pipe.vae.requires_grad_(False)
    pipe.text_encoder.requires_grad_(False)
    pipe.unet.requires_grad_(False)

    # 3. Configure LoRA
    print("\n=== Step 3: Configure LoRA ===")
    if is_peft_available():
        lora_config = LoraConfig(
            r=config.lora_rank,
            lora_alpha=config.lora_alpha,
            target_modules=["to_q", "to_k", "to_v", "to_out.0"],
            lora_dropout=config.lora_dropout,
            bias="none",
        )

        pipe.unet = get_peft_model(pipe.unet, lora_config)
        pipe.unet.print_trainable_parameters()

    # 4. Prepare the data
    print("\n=== Step 4: Prepare the data ===")
    from transformers import CLIPTokenizer
    tokenizer = CLIPTokenizer.from_pretrained(
        config.pretrained_model_name,
        subfolder="tokenizer"
    )

    train_dataset = StickerDataset(
        train_data_dir,
        tokenizer=tokenizer,
        style_token=config.style_token,
        style_desc=config.style_description,
        size=config.resolution,
    )

    print("📝 Prompt example：")
    for i in range(min(3, len(train_dataset))):
        print(f"  {train_dataset[i]['prompt']}")

    train_dataloader = DataLoader(
        train_dataset,
        batch_size=config.train_batch_size,
        shuffle=True,
        num_workers=2,
    )

    # 5. Optimizer
    print("\n=== Step 5: Optimizer ===")
    optimizer = torch.optim.AdamW(
        pipe.unet.parameters(),
        lr=config.learning_rate,
        betas=(0.9, 0.999),
        weight_decay=1e-2,
        eps=1e-08,
    )

    # 6. lr
    lr_scheduler = get_scheduler(
        config.lr_scheduler,
        optimizer=optimizer,
        num_warmup_steps=config.lr_warmup_steps * accelerator.num_processes,
        num_training_steps=config.max_train_steps * accelerator.num_processes,
    )

    # 7. accelerator
    pipe.unet, optimizer, train_dataloader, lr_scheduler = accelerator.prepare(
        pipe.unet, optimizer, train_dataloader, lr_scheduler
    )

    # 8. Training
    print("\n=== Step 6: Start Training ===")
    print(f"device: {accelerator.device}")
    print(f"steps: {config.max_train_steps}")

    global_step = 0
    progress_bar = tqdm(range(config.max_train_steps), desc="Training progress")

    start_time = time.time()

    for epoch in range(config.max_train_steps // len(train_dataloader) + 1):
        pipe.unet.train()

        for step, batch in enumerate(train_dataloader):
            with accelerator.accumulate(pipe.unet):
                # Forward
                latents = pipe.vae.encode(
                    batch["pixel_values"].to(accelerator.device)
                ).latent_dist.sample()
                latents = latents * pipe.vae.config.scaling_factor

                noise = torch.randn_like(latents)
                timesteps = torch.randint(
                    0, pipe.scheduler.config.num_train_timesteps,
                    (latents.shape[0],), device=latents.device
                ).long()
                noisy_latents = pipe.scheduler.add_noise(latents, noise, timesteps)

                text_inputs = tokenizer(
                    batch["prompt"],
                    padding="max_length",
                    max_length=tokenizer.model_max_length,
                    truncation=True,
                    return_tensors="pt",
                )
                text_embeddings = pipe.text_encoder(
                    text_inputs.input_ids.to(accelerator.device)
                )[0]

                noise_pred = pipe.unet(noisy_latents, timesteps, text_embeddings).sample
                loss = torch.nn.functional.mse_loss(noise_pred, noise)

                accelerator.backward(loss)
                optimizer.step()
                lr_scheduler.step()
                optimizer.zero_grad()

            progress_bar.update(1)
            global_step += 1

            # Save checkpoint
            if global_step % config.checkpointing_steps == 0:
                elapsed = time.time() - start_time
                print(f"\n⏱️ Trained {global_step} steps，Time taken {elapsed/60:.1f} minutes")
                print(f"💾 Save checkpoint...")

                accelerator.wait_for_everyone()
                if accelerator.is_main_process:
                    unwrapped_unet = accelerator.unwrap_model(pipe.unet)
                    lora_path = os.path.join(config.output_dir, f"lora_step_{global_step}")
                    os.makedirs(lora_path, exist_ok=True)
                    unwrapped_unet.save_pretrained(lora_path)

                    drive_lora_path = os.path.join(
                        config.drive_output_dir,
                        f"lora_step_{global_step}"
                    )
                    shutil.copytree(lora_path, drive_lora_path, dirs_exist_ok=True)
                    print(f"✅ Backed up to Drive: {drive_lora_path}")

            # Validation
            if global_step % config.validation_steps == 0:
                print(f"\n=== Generate verification samples ===")

                pipe.unet.eval()
                for prompt in config.validation_prompts:
                    with torch.no_grad():
                        images = pipe(
                            prompt,
                            num_inference_steps=20,
                            guidance_scale=7.5,
                            num_images_per_prompt=1,
                        ).images

                        for i, img in enumerate(images):
                            animal = prompt.split()[2]
                            img_path = os.path.join(
                                config.validation_dir,
                                f"step_{global_step}_{animal}.png"
                            )
                            img.save(img_path)

                pipe.unet.train()

            if global_step >= config.max_train_steps:
                break

        if global_step >= config.max_train_steps:
            break

    # 9. Save final LoRA
    print("\n=== Save final LoRA ===")
    accelerator.wait_for_everyone()
    if accelerator.is_main_process:
        unwrapped_unet = accelerator.unwrap_model(pipe.unet)
        final_lora_path = os.path.join(config.output_dir, "lora_final")
        os.makedirs(final_lora_path, exist_ok=True)
        unwrapped_unet.save_pretrained(final_lora_path)

        # Save to Drive
        drive_final_path = os.path.join(config.drive_output_dir, "lora_final")
        shutil.copytree(final_lora_path, drive_final_path, dirs_exist_ok=True)

        # Save pt
        from peft import get_peft_model_state_dict
        state_dict = get_peft_model_state_dict(unwrapped_unet)
        torch.save(state_dict, os.path.join(config.drive_output_dir, "lora_final.pt"))

        total_time = time.time() - start_time
        print(f"\n🎉 Train finished! Total_time {total_time/60:.1f} minutues")
        print(f"✅ LoRA has been saved to Drive: {config.drive_output_dir}")


def test():
    config = Config()

    # Find final LoRA
    lora_path = os.path.join(config.drive_output_dir, "lora_final")
    if not os.path.exists(lora_path):
        print("❌ No LoRA found")
        return

    print(f"Load LoRA: {lora_path}")

    # Load Model
    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        # torch_dtype=torch.float16,
        safety_checker=None,
    ).to("cuda")

    pipe.enable_attention_slicing()

    # Load LoRA
    from peft import PeftModel
    pipe.unet = PeftModel.from_pretrained(pipe.unet, lora_path)

    # Test different animals
    animals = ['cat', 'dog', 'fish', 'rabbit', 'bear', 'fox', 'wolf', 'deer', 'koala']
    os.makedirs("/content/test_output", exist_ok=True)

    for animal in animals:
        prompt = f"a sks {animal} sticker style"
        print(f"Generate: {prompt}")

        images = pipe(
            prompt,
            num_inference_steps=25,
            guidance_scale=7.5,
            num_images_per_prompt=2,
        ).images

        for i, img in enumerate(images):
            img.save(f"/content/test_output/{animal}_sticker_{i}.png")

    print(f"✅ Generation complete! Images have been saved to /content/test_output/")

    # Download the package
    import shutil
    shutil.make_archive("/content/test_output", 'zip', "/content/test_output")
    print("📦 Already for downloading /content/test_output.zip")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--train":
        train()
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        test()
    else:
        print("Type in correct method:")
        print("  python train.py --train  # 训练")
        print("  python train.py --test   # 测试")