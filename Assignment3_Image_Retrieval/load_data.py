import os
import csv
import uuid
import clip
import torch
from PIL import Image
from upstash_vector import Index

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
upstash_index = Index(
    url=os.getenv("UPSTASH_VECTOR_URL"),
    token=os.getenv("UPSTASH_VECTOR_TOKEN")
)

# 文本编码函数
def encode_text(text, context_length=77):
    text_segments = []
    while text:
        segment = text[:context_length]
        text_segments.append(segment)
        text = text[context_length:]
    encoded_segments = []
    for segment in text_segments:
        text_tokens = clip.tokenize(segment).to(device)
        with torch.no_grad():
            text_features = model.encode_text(text_tokens)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        encoded_segments.append(text_features)
    return encoded_segments, text_segments

def store_vectors():
    dataset_dir = "./dataset"
    csv_path = "./dataset/classes.csv"
    txt_files = ["val.txt", "train.txt"]
    upstash_index.reset()

    # # 读取 classes.csv 文件并构建类别映射
    class_info = {}
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            class_name = row['Class Name (str)']
            class_id = row['Class ID (int)']
            coarse_class_name = row['Coarse Class Name (str)']
            coarse_class_id = row['Coarse Class ID (int)']
            text_path = row['Product Description Path (str)'][1:]  # 移除前导斜杠
            image_path = row['Iconic Image Path (str)'][1:]  # 移除前导斜杠
            class_info[class_id] = {
                'class_name': class_name,
                'coarse_class_name': coarse_class_name,
                'coarse_class_id': coarse_class_id,
                'text_path': os.path.join(dataset_dir, text_path),
                'iconic_image_path': os.path.join(dataset_dir, image_path)
            }
    print("class_info", class_info)

    # 处理多个txt文件
    for txt_file in txt_files:
        val_path = os.path.join(dataset_dir, txt_file)  # 拼接完整路径
        print(f"\n正在处理文件：{val_path}")
        
        try:
            with open(val_path, 'r', encoding='utf-8') as valfile:
                for line in valfile:
                    image_path, class_id, coarse_class_id = line.strip().split(', ')
                    print("原始image_path:", image_path)
                    print("class_id:", class_id)
                    print("coarse_class_id:", coarse_class_id)
                    
                    # 拼接图像完整路径
                    full_image_path = os.path.join(dataset_dir, image_path)
                    print("完整image_path:", full_image_path)
                    
                    if class_id in class_info:
                        class_name = class_info[class_id]['class_name']
                        coarse_class_name = class_info[class_id]['coarse_class_name']
                        text_path = class_info[class_id]['text_path']
                        try:
                            # ... 原有图像编码、上传逻辑（保持不变）...
                            image = Image.open(full_image_path).convert("RGB")
                            image_tensor = preprocess(image).unsqueeze(0).to(device)
                            with torch.no_grad():
                                features = model.encode_image(image_tensor)
                            features = features / features.norm(dim=-1, keepdim=True)
                            vector_id = str(uuid.uuid4())
                            upstash_index.upsert(
                                vectors=[{
                                    "id": vector_id,
                                    "vector": features.cpu().numpy().flatten().tolist(),
                                    "metadata": {
                                        "type": "image",
                                        "image_path": full_image_path,
                                        "text_path": text_path,
                                        "class_name": class_name,
                                        "class_id": class_id,
                                        "coarse_class_name": coarse_class_name,
                                        "coarse_class_id": coarse_class_id
                                    }
                                }]
                            )
                            print(f"Uploaded validation image {full_image_path}")
                        except Exception as e:
                            print(f"处理图像 {full_image_path} 失败: {e}")
        except FileNotFoundError:
            print(f"警告：文件 {val_path} 不存在，跳过处理。")
        except Exception as e:
            print(f"处理文件 {val_path} 时发生错误: {e}")

    print("\n所有txt文件处理完成。")

if __name__ == "__main__":
    store_vectors()
    