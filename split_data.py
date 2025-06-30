import os
import shutil
import random

def split_data(source_dir, train_dir, val_dir, val_ratio=0.2, seed=42):
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(val_dir, exist_ok=True)

    all_files = [f for f in os.listdir(source_dir) if f.endswith('.png')]
    random.seed(seed)
    random.shuffle(all_files)

    val_size = int(len(all_files) * val_ratio)
    val_files = all_files[:val_size]
    train_files = all_files[val_size:]

    for f in train_files:
        shutil.copy(os.path.join(source_dir, f), os.path.join(train_dir, f))

    for f in val_files:
        shutil.copy(os.path.join(source_dir, f), os.path.join(val_dir, f))

    print(f"✅ {len(train_files)} ảnh train, {len(val_files)} ảnh val cho {os.path.basename(source_dir)}")

# Đường dẫn thư mục ảnh gốc (chưa chia)
#split_data(f"earthquake", "data/train/earthquake", "data/val/earthquake")
#split_data(f"noise", "data/train/noise", "data/val/noise")

def create_test_set(source_dir, test_dir, num_test=368, seed=42):
    os.makedirs(test_dir, exist_ok=True)

    all_files = [f for f in os.listdir(source_dir) if f.endswith('.png')]
    random.seed(seed)
    random.shuffle(all_files)

    test_files = all_files[:num_test]

    for f in test_files:
        src = os.path.join(source_dir, f)
        dst = os.path.join(test_dir, f)
        shutil.copy(src, dst)

    print(f"✅ Đã tạo {len(test_files)} ảnh test cho {os.path.basename(source_dir)}")

# Dùng cho 2 lớp
create_test_set("earthquake", "data/test/earthquake")
create_test_set("noise", "data/test/noise")
