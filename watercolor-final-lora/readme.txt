Lilian0703/sticker-lora-watercolor
https://huggingface.co/Lilian0703/sticker-lora-watercolor
final-1200步
Python引用代码：

from huggingface_hub import login, upload_folder

# (optional) Login with your Hugging Face credentials
login()

# Push your model files
upload_folder(folder_path=".", repo_id="Lilian0703/sticker-lora-watercolor", repo_type="model")
