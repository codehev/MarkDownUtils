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
    # 如果未提供 image_folder，则设置为默认路径
    if image_folder is None:
        md_file_name = os.path.splitext(os.path.basename(md_file))[0]
        image_folder = os.path.join(os.path.dirname(md_file), "image", md_file_name)

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
        print("Markdown 文件已更新！")
    except Exception as e:
        print(f"保存文件 {md_file} 失败: {e}")

"""
优化后的代码在以下方面有明显改进：
功能增强：支持多种图片引用格式。
健壮性提升：增强错误处理，避免程序因异常中断。
性能优化：减少不必要的字符串操作，提升效率。
可读性和可维护性：代码结构更清晰，便于扩展和维护。
用户体验：提供更详细的日志信息和进度条，方便跟踪处理进度。

add: 将 image_folder 设置为可选参数，并默认将其保存在 Markdown 文件所在目录的 ./image/markdown文件名 目录下。

注意：可能复制粘贴时，图片出现问题，变成base64无法显示，需要手动修复，ctrl+f，搜索data:image/png;
"""
if __name__ == "__main__":
    # 设置 Markdown 文件路径
    md_file = "C:\\Users\\codeh\\Desktop\\CSNote\\Project\\api.md"  # 替换为你的 Markdown 文件路径
    # md_file = "C:\\Users\\codeh\\Desktop\\CSNote\\Backend\\SSM\\SpringBoot.md"  # 替换为你的 Markdown 文件路径
    image_folder = None # 可选参数，图片保存目录，设置为 None 表示使用默认路径：./image/markdown文件名

    # 处理 Markdown 文件，image_folder 为可选参数
    process_markdown_file(md_file, image_folder)