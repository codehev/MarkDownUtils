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

def delete_unused_images(md_files):
    """删除未使用的图片"""
    total_unused_count = 0  # 总未使用图片数量

    # 遍历所有 Markdown 文件
    for md_file in tqdm(md_files, desc="处理 Markdown 文件", unit="文件"):
        # 动态确定图片文件夹
        md_filename = os.path.splitext(os.path.basename(md_file))[0]  # 获取 Markdown 文件名（不含扩展名）
        image_folder = os.path.join(os.path.dirname(md_file), "image", md_filename)  # 图片文件夹路径

        if not os.path.exists(image_folder):
            print(f"\n图片文件夹不存在: {image_folder}，跳过处理文件: {md_file}")
            continue

        # 提取当前 Markdown 文件中使用的图片路径
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        used_images = extract_used_images(content)

        # 获取图片文件夹中的所有文件
        all_images = set()
        for root, _, files in os.walk(image_folder):
            for file in files:
                file_path = os.path.relpath(os.path.join(root, file), os.path.dirname(md_file))  # 相对于 Markdown 文件的路径
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

def find_markdown_files(folder):
    """递归查找指定文件夹及其子文件夹中的所有 Markdown 文件"""
    md_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))
    return md_files
# 递归清理指定文件夹下的markdown文件未使用的图片（就是能递归处理子文件夹下的markdown文件）
# 图片路径已经固定为 ./image/markdown文件名

"""
改进点说明
支持带标题的 Markdown 图片：
正则表达式 r"!\[.*?\]\((.*?)(?:\s+\".*?\")?\)" 支持匹配带标题的图片。

支持带属性和样式的 HTML 图片：
正则表达式 r"<img.*?src=[\"'](.*?)[\"'].*?>" 支持匹配带属性和样式的图片。

支持 Markdown 引用格式的图片：
正则表达式 r"\[.*?\]\[(.*?)\]" 和 r"\[(.*?)\]:\s*(.*?)(?:\s+\".*?\")?\s*$" 支持匹配引用格式的图片。

忽略 Base64 图片：
脚本会忽略以 data:image 开头的 Base64 图片。

"""
if __name__ == "__main__":
    # 设置 Markdown 文件所在文件夹
    md_folder = "C:\\Users\\codeh\\Desktop\\CSNote\\Project"  # 替换为你的 Markdown 文件所在文件夹

    # 递归查找所有 Markdown 文件
    md_files = find_markdown_files(md_folder)
    print(f"找到 {len(md_files)} 个 Markdown 文件")

    # 删除未使用的图片
    delete_unused_images(md_files)