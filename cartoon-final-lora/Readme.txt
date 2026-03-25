Lilian0703/sticker-lora-cartoon
https://huggingface.co/Lilian0703/sticker-lora-cartoon


Python引用：

from huggingface_hub import login, upload_folder

# (optional) Login with your Hugging Face credentials
login()

# Push your model files
upload_folder(folder_path=".", repo_id="Lilian0703/sticker-lora-cartoon", repo_type="model")
