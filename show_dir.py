import os
from tqdm import tqdm

def show_folder_structure(root_dir, max_depth=None):
    """
    打印文件夹结构，带进度条。
    参数:
        root_dir (str): 根目录路径
        max_depth (int): 最大显示层级（可选）
    """
    if not os.path.exists(root_dir):
        print(f"❌ 路径不存在: {root_dir}")
        return

    # 收集所有路径
    all_paths = []
    for current_path, dirs, files in os.walk(root_dir):
        depth = current_path[len(root_dir):].count(os.sep)
        if max_depth is not None and depth > max_depth:
            continue
        all_paths.append((current_path, dirs, files))

    print(f"\n📁 文件夹结构（共 {len(all_paths)} 个层级节点）：\n")

    # 带进度条显示
    for current_path, dirs, files in tqdm(all_paths, desc="扫描目录中", ncols=80):
        depth = current_path[len(root_dir):].count(os.sep)
        indent = "│   " * depth
        folder_name = os.path.basename(current_path) if current_path != root_dir else current_path
        print(f"{indent}📂 {folder_name}")
        sub_indent = "│   " * (depth + 1)
        for f in files:
            print(f"{sub_indent}📄 {f}")

if __name__ == "__main__":
    # 让用户输入路径
    folder_path = r"D:\code\View_Blueprint"
    show_folder_structure(folder_path)
