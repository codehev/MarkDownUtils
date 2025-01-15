import os
import re
from tqdm import tqdm  # 导入 tqdm 库

def extract_used_images(md_content):
    """从 Markdown 内容中提取所有使用的图片路径"""
    # 正则表达式匹配 Markdown 图片链接
    pattern = r"!\[.*?\]\((.*?)\)"
    matches = re.findall(pattern, md_content)
    used_images = set()

    for match in matches:
        # 如果路径是相对路径，转换为绝对路径
        if not match.startswith(("http://", "https://")):
            used_images.add(os.path.normpath(match))  # 规范化路径
    return used_images

def delete_unused_images(md_file, image_folder):
    """删除未使用的图片"""
    # 读取 Markdown 文件
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取使用的图片路径
    used_images = extract_used_images(content)
    print(f"Markdown 文件中使用的图片数量: {len(used_images)}")

    # 获取图片文件夹中的所有文件
    all_images = set()
    for root, _, files in os.walk(image_folder):
        for file in files:
            file_path = os.path.relpath(os.path.join(root, file), os.path.dirname(md_file))
            all_images.add(os.path.normpath(file_path))  # 规范化路径

    print(f"图片文件夹中的图片数量: {len(all_images)}")

    # 找到未使用的图片
    unused_images = all_images - used_images
    print(f"未使用的图片数量: {len(unused_images)}")

    # 删除未使用的图片
    if unused_images:
        print("\n开始删除未使用的图片...")
        for image in tqdm(unused_images, desc="删除未使用的图片", unit="图片"):
            try:
                os.remove(os.path.join(os.path.dirname(md_file), image))
                print(f"删除成功: {image}")
            except Exception as e:
                print(f"删除失败: {image}, 错误: {e}")
    else:
        print("\n没有未使用的图片需要删除。")


"""
指定markdown文件清理未使用的图片

"""
if __name__ == "__main__":
    # 设置 Markdown 文件路径和图片保存文件夹
    md_file = "C:\\Users\\codeh\\Desktop\\CSNote\\Project\\api.md"  # 替换为你的 Markdown 文件路径
    image_folder = "C:\\Users\\codeh\\Desktop\\CSNote\\Project\\image\\api"   # 图片保存文件夹

    # 删除未使用的图片
    delete_unused_images(md_file, image_folder)