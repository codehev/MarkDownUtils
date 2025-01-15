import os
import re
from tqdm import tqdm  # 导入 tqdm 库

def extract_used_images(md_content):
    """从 Markdown 内容中提取所有使用的图片路径"""
    used_images = set()

    # 正则表达式匹配 Markdown 图片链接
    md_pattern = r"!\[.*?\]\((.*?)(?:\s+\".*?\")?\)"  # 支持带标题的图片
    for match in re.findall(md_pattern, md_content):
        if not match.startswith(("http://", "https://", "data:image")):
            used_images.add(os.path.normpath(match))  # 规范化路径

    # 正则表达式匹配 HTML <img> 标签中的图片链接
    html_pattern = r"<img.*?src=[\"'](.*?)[\"'].*?>"  # 支持带属性和样式的图片
    for match in re.findall(html_pattern, md_content):
        if not match.startswith(("http://", "https://", "data:image")):
            used_images.add(os.path.normpath(match))  # 规范化路径

    # 正则表达式匹配 Markdown 引用格式的图片链接
    ref_pattern = r"\[.*?\]\[(.*?)\]"  # 匹配引用标识
    ref_link_pattern = r"\[(.*?)\]:\s*(.*?)(?:\s+\".*?\")?\s*$"  # 匹配引用定义
    ref_links = dict(re.findall(ref_link_pattern, md_content, re.MULTILINE))
    for match in re.findall(ref_pattern, md_content):
        if match in ref_links and not ref_links[match].startswith(("http://", "https://", "data:image")):
            used_images.add(os.path.normpath(ref_links[match]))  # 规范化路径

    return used_images

def delete_unused_images(md_file):
    """删除未使用的图片"""
    # 动态确定图片文件夹
    md_filename = os.path.splitext(os.path.basename(md_file))[0]  # 获取 Markdown 文件名（不含扩展名）
    image_folder = os.path.join(os.path.dirname(md_file), "image", md_filename)  # 图片文件夹路径

    if not os.path.exists(image_folder):
        print(f"\n图片文件夹不存在: {image_folder}，跳过处理文件: {md_file}")
        return

    # 读取 Markdown 文件
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取使用的图片路径
    used_images = extract_used_images(content)
    print(f"\nMarkdown 文件中使用的图片数量: {len(used_images)}")

    # 获取图片文件夹中的所有文件
    all_images = set()
    for root, _, files in os.walk(image_folder):
        for file in files:
            file_path = os.path.relpath(os.path.join(root, file), os.path.dirname(md_file))  # 相对于 Markdown 文件的路径
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

改进点说明
动态生成图片文件夹路径：
根据 Markdown 文件的路径动态生成图片文件夹路径。例如：
Markdown 文件：C:\\Users\\codeh\\Desktop\\CSNote\\Project\\api.md
图片文件夹：C:\\Users\\codeh\\Desktop\\CSNote\\Project\\image\\api

支持多种图片引用格式：
支持 Markdown 标准格式、HTML <img> 标签、带标题的图片、带尺寸的图片、带样式的图片、引用格式的图片等。

更详细的日志信息：
显示使用的图片数量、图片文件夹中的图片数量、未使用的图片数量、删除结果等。

进度条：
使用 tqdm 显示删除进度。
"""
if __name__ == "__main__":
    # 设置 Markdown 文件路径
    md_file = "C:\\Users\\codeh\\Desktop\\CSNote\\Project\\bi.md"  # 替换为你的 Markdown 文件路径

    # 删除未使用的图片
    delete_unused_images(md_file)