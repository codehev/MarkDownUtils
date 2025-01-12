
import os
import re
import requests
from urllib.parse import urlparse
from tqdm import tqdm  # 导入 tqdm 库

def download_image(url, folder):
    """下载图片并保存到指定文件夹"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # 提取文件名
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = "image_" + str(hash(url)) + ".png"  # 如果 URL 中没有文件名，生成一个唯一文件名
            filepath = os.path.join(folder, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)
            return filepath
    except Exception as e:
        print(f"下载失败: {url}, 错误: {e}")
    return None

def replace_image_links(md_content, folder, md_file):
    """替换 Markdown 内容中的在线图片链接为本地路径"""
    # 正则表达式匹配 Markdown 图片链接
    pattern = r"!\[.*?\]\((.*?)\)"
    matches = list(re.finditer(pattern, md_content))  # 找到所有匹配的图片链接
    new_content = md_content
    success_count = 0  # 成功下载的图片数
    fail_count = 0  # 下载失败的图片数

    # 使用 tqdm 添加进度条
    for match in tqdm(matches, desc="下载图片并替换链接", unit="图片"):
        url = match.group(1)
        if url.startswith(("http://", "https://")):
            local_path = download_image(url, folder)
            if local_path:
                # 替换为相对路径
                relative_path = os.path.relpath(local_path, os.path.dirname(md_file))
                new_content = new_content.replace(match.group(0), match.group(0).replace(url, relative_path))
                success_count += 1
                print(f"下载成功: {url} -> {relative_path}")
            else:
                fail_count += 1
                print(f"下载失败: {url}")
        else:
            print(f"跳过非在线图片: {url}")

    # 打印统计信息
    print(f"\n图片处理完成！")
    print(f"总图片数: {len(matches)}")
    print(f"成功下载: {success_count}")
    print(f"下载失败: {fail_count}")

    return new_content


"""
单文件下载图片，添加进度条
"""
if __name__ == "__main__":
    # 设置 Markdown 文件路径和图片保存文件夹
    md_file = "C:\\Users\\codeh\\Desktop\\CSNote\\Project\\api.md"  # 替换为你的 Markdown 文件路径
    image_folder = "C:\\Users\\codeh\\Desktop\\CSNote\\Project\\image\\api"   # 图片保存文件夹

    # 创建图片保存文件夹
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)

    # 读取 Markdown 文件
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 替换在线图片链接为本地相对路径,这个相对路径是相对于 Markdown 文件所在目录的路径。
    new_content = replace_image_links(content, image_folder, md_file)

    # 保存修改后的 Markdown 文件
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("Markdown 文件已更新！")