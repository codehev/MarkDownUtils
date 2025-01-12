import os
import re
from tqdm import tqdm  # 导入 tqdm 库

def extract_used_images(md_content):
    """从 Markdown 内容中提取所有使用的图片路径"""
    pattern = r"!\[.*?\]\((.*?)\)"  # 正则表达式匹配 Markdown 图片链接
    matches = re.findall(pattern, md_content)
    used_images = set()

    for match in matches:
        if not match.startswith(("http://", "https://")):  # 忽略网络图片
            used_images.add(os.path.normpath(match))  # 规范化路径
    return used_images

def delete_unused_images(md_files):
    """删除未使用的图片"""
    total_unused_count = 0  # 总未使用图片数量

    for md_file in tqdm(md_files, desc="处理 Markdown 文件", unit="文件"):
        # 动态确定图片文件夹
        md_filename = os.path.splitext(os.path.basename(md_file))[0]  # 获取 Markdown 文件名（不含扩展名）
        image_folder = os.path.join(os.path.dirname(md_file), "image", md_filename)  # 图片文件夹路径

        if not os.path.exists(image_folder):
            print(f"\n图片文件夹不存在: {image_folder}，跳过处理文件: {md_file}")
            continue

        # 提取当前 Markdown 文件中使用的图片路径
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            used_images = extract_used_images(content)
        except Exception as e:
            print(f"\n读取文件 {md_file} 失败: {e}")
            continue

        # 获取图片文件夹中的所有文件
        all_images = set()
        for file in os.listdir(image_folder):
            file_path = os.path.relpath(os.path.join(image_folder, file), os.path.dirname(md_file))  # 相对于 Markdown 文件的路径
            all_images.add(os.path.normpath(file_path))  # 规范化路径

        # 找到未使用的图片
        unused_images = all_images - used_images
        total_unused_count += len(unused_images)

        # 删除未使用的图片
        if unused_images:
            print(f"\n正在处理文件: {md_file}")
            print(f"图片文件夹: {image_folder}")
            print(f"未使用的图片数量: {len(unused_images)}")
            for image in tqdm(unused_images, desc="删除未使用的图片", unit="图片"):
                try:
                    os.remove(os.path.join(os.path.dirname(md_file), image))
                    print(f"删除成功: {image}")
                except Exception as e:
                    print(f"删除失败: {image}, 错误: {e}")
        else:
            print(f"\n文件 {md_file} 没有未使用的图片。")

    print(f"\n所有文件处理完成！")
    print(f"总未使用的图片数量: {total_unused_count}")

"""
非递归,清理指定文件夹下的所有markdown文件未使用的图片（就是不能递归处理子文件夹下的markdown文件）
图片路径已经固定为 ./image/markdown文件名

改进点说明：
非递归处理：
使用 os.listdir 获取指定文件夹下的文件列表，不递归处理子文件夹。
确保只处理当前文件夹下的 .md 文件。

路径处理优化：
使用 os.path.normpath 和 os.path.relpath 规范化路径，避免路径格式问题。

错误处理增强：
在读取文件和删除文件时增加 try-except 块，避免程序因异常中断。

代码简化：
移除冗余代码，提升可读性。
使用 tqdm 提供进度条，增强用户体验。
"""
if __name__ == "__main__":
    # 设置 Markdown 文件所在文件夹
    md_folder = "C:\\Users\\codeh\\Desktop\\CSNote\\Project"  # 替换为你的 Markdown 文件所在文件夹

    # 获取所有 Markdown 文件（非递归）
    md_files = [os.path.join(md_folder, f) for f in os.listdir(md_folder) if f.endswith(".md")]
    print(f"找到 {len(md_files)} 个 Markdown 文件")

    # 删除未使用的图片
    delete_unused_images(md_files)