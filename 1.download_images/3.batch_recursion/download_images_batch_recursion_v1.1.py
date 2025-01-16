import os
import re
import requests
from urllib.parse import urlparse
from tqdm import tqdm  # 导入 tqdm 库

def download_image(url, folder):
    """
    下载图片并保存到指定文件夹
    :param url: 图片的 URL
    :param folder: 图片保存文件夹
    :return: 本地图片路径（如果下载成功），否则返回 None
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        # 提取文件名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:  # 如果 URL 中没有文件名，生成一个唯一文件名
            filename = f"image_{hash(url)}.png"
        filepath = os.path.join(folder, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)
        return filepath
    except Exception as e:
        print(f"下载失败: {url}, 错误: {e}")
    return None

def replace_image_links(md_content, folder, md_file):
    """
    替换 Markdown 内容中的在线图片链接为本地路径
    :param md_content: Markdown 文件内容
    :param folder: 图片保存文件夹
    :param md_file: Markdown 文件路径
    :return: 替换后的 Markdown 内容
    """
    # 正则表达式匹配多种图片引用格式
    patterns = [
        r"!\[(.*?)\]\((.*?)(?:\s+\"(.*?)\")?\)",  # Markdown 格式：![alt](url "title")
        r"<img\s+[^>]*src=[\"'](.*?)[\"'][^>]*>",  # HTML 格式：<img src="url" alt="alt">
    ]
    success_count = 0  # 成功下载的图片数
    fail_count = 0  # 下载失败的图片数

    def replace_match(match):
        nonlocal success_count, fail_count
        url = match.group(2) if match.re.pattern == patterns[0] else match.group(1)
        if url.startswith(("http://", "https://")):
            local_path = download_image(url, folder)
            if local_path:
                # 替换为相对路径
                relative_path = os.path.relpath(local_path, os.path.dirname(md_file))
                success_count += 1
                print(f"下载成功: {url} -> {relative_path}")
                if match.re.pattern == patterns[0]:  # Markdown 格式
                    alt = match.group(1)
                    title = match.group(3) if match.group(3) else ""
                    return f'![{alt}]({relative_path} "{title}")' if title else f'![{alt}]({relative_path})'
                else:  # HTML 格式
                    return match.group(0).replace(url, relative_path)
            else:
                fail_count += 1
                print(f"下载失败: {url}")
        else:
            print(f"跳过非在线图片: {url}")
        return match.group(0)  # 返回原始内容

    # 使用 tqdm 添加进度条
    new_content = md_content
    for pattern in patterns:
        matches = list(re.finditer(pattern, new_content))
        for match in tqdm(matches, desc=f"处理 {pattern} 格式", unit="图片"):
            new_content = new_content.replace(match.group(0), replace_match(match))

    # 打印统计信息
    print(f"\n图片处理完成！")
    print(f"成功下载: {success_count}")
    print(f"下载失败: {fail_count}")

    return new_content

def process_markdown_file(md_file, image_folder=None):
    """
    处理单个 Markdown 文件，下载在线图片并替换链接
    :param md_file: Markdown 文件路径
    :param image_folder: 图片保存文件夹（可选，默认为 ./image/markdown文件名）
    """
    # 获取 Markdown 文件名（不含扩展名）
    md_filename = os.path.splitext(os.path.basename(md_file))[0]

    # 如果未提供 image_folder，则设置为默认路径
    if image_folder is None:
        image_folder = os.path.join(os.path.dirname(md_file), "image", md_filename)
    else:
        # 将 image_folder 转换为相对于当前 Markdown 文件的绝对路径，并拼接 Markdown 文件名
        image_folder = os.path.join(os.path.dirname(md_file), image_folder, md_filename)

    # 创建图片保存文件夹
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)

    # 读取 Markdown 文件
    try:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件 {md_file} 失败: {e}")
        return

    # 替换在线图片链接为本地相对路径
    new_content = replace_image_links(content, image_folder, md_file)

    # 保存修改后的 Markdown 文件
    try:
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Markdown 文件已更新: {md_file}")
    except Exception as e:
        print(f"保存文件 {md_file} 失败: {e}")

def find_markdown_files(folder):
    """
    递归查找指定文件夹下的所有 Markdown 文件
    :param folder: 目标文件夹
    :return: 所有 Markdown 文件的路径列表
    """
    md_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))
    return md_files

def process_markdown_folder(folder, image_folder=None):
    """
    处理指定文件夹及其子文件夹下的所有 Markdown 文件
    :param folder: Markdown 文件所在文件夹
    :param image_folder: 图片保存文件夹（可选，默认为 ./image/markdown文件名）
    """
    # 递归查找所有 Markdown 文件
    md_files = find_markdown_files(folder)
    print(f"找到 {len(md_files)} 个 Markdown 文件")

    # 处理每个 Markdown 文件
    for md_file in tqdm(md_files, desc="处理 Markdown 文件", unit="文件"):
        process_markdown_file(md_file, image_folder)

def main(input_path, image_folder=None):
    """
    主函数，根据输入路径是文件还是文件夹进行处理
    :param input_path: 输入的 Markdown 文件或文件夹路径
    :param image_folder: 图片保存文件夹（可选，默认为 ./image/markdown文件名）
    """
    if os.path.isfile(input_path) and input_path.endswith(".md"):
        # 如果是单个 Markdown 文件
        process_markdown_file(input_path, image_folder)
    elif os.path.isdir(input_path):
        # 如果是文件夹
        process_markdown_folder(input_path, image_folder)
    else:
        print(f"输入路径无效: {input_path}")

"""
优化后的代码支持以下功能：
1. 单文件处理：如果输入是单个 Markdown 文件，直接下载图片并替换链接。
2. 目录递归处理：如果输入是目录，递归查找所有 Markdown 文件并处理。
3. 图片保存路径优化：图片默认保存在 ./image/markdown文件名 目录下，支持自定义相对路径。
4. 即使指定了自定义路径，也会在其后拼接 Markdown 文件名作为子目录。
5. 增强错误处理：确保程序在文件读取、网络请求和文件保存时的健壮性。
6. 进度条和日志输出：使用 tqdm 显示进度条，并提供详细的日志信息。
"""
if __name__ == "__main__":
    # 设置输入路径（可以是单个 Markdown 文件或文件夹）
    input_path = "C:\\Users\\codeh\\Desktop\\CSNote"  # 替换为你的 Markdown 文件或文件夹路径

    # 设置图片保存路径（可选，默认为 ./image/markdown文件名）
    image_folder = "./custom_image_folder"  # 替换为你的自定义相对路径（[image_folder]/markdown文件名），或设置为 None 使用默认路径

    # 处理输入路径
    main(input_path, image_folder)