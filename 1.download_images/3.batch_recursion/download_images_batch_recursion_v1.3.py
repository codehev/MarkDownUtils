import os
import re
import requests
from urllib.parse import urlparse, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import logging
from typing import Dict, Tuple, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 缓存已下载的图片
image_cache: Dict[str, str] = {}

def download_image(url: str, folder: str) -> Optional[str]:
    """
    下载图片并保存到指定文件夹
    :param url: 图片的 URL
    :param folder: 图片保存文件夹
    :return: 本地图片路径（如果下载成功），否则返回 None
    """
    if url in image_cache:
        return image_cache[url]

    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        response.raise_for_status()  # 检查请求是否成功

        # 提取文件名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:  # 如果 URL 中没有文件名，生成一个唯一文件名
            filename = f"image_{hash(url)}.png"
        filepath = os.path.join(folder, filename)

        # 保存图片
        with open(filepath, "wb") as f:
            f.write(response.content)

        image_cache[url] = filepath
        return filepath
    except Exception as e:
        logger.error(f"下载失败: {url}, 错误: {e}")
    return None

def replace_image_links(md_content: str, folder: str, md_file: str) -> str:
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
        r"!\[(.*?)\]\[(.*?)\]",  # Markdown 引用链接格式：![alt][ref]
        r"\[(.*?)\]:\s*(.*?)(?:\s+\"(.*?)\")?",  # Markdown 引用链接定义：[ref]: url "title"
    ]
    success_count = 0  # 成功下载的图片数
    fail_count = 0  # 下载失败的图片数

    # 提取所有引用链接定义
    ref_links = {}
    for match in re.finditer(patterns[3], md_content):
        ref_key = match.group(1).strip().lower()
        ref_url = match.group(2).strip()
        ref_title = match.group(3) if match.group(3) else ""
        ref_links[ref_key] = (ref_url, ref_title)

    def replace_match(match):
        nonlocal success_count, fail_count
        url = None
        alt = ""
        title = ""

        if match.re.pattern == patterns[0]:  # Markdown 格式：![alt](url "title")
            alt = match.group(1)
            url = match.group(2)
            title = match.group(3) if match.group(3) else ""
        elif match.re.pattern == patterns[1]:  # HTML 格式：<img src="url" alt="alt">
            url = match.group(1)
            # 从 HTML 标签中提取 alt 和 title
            alt_match = re.search(r'alt=[\"\'](.*?)[\"\']', match.group(0))
            title_match = re.search(r'title=[\"\'](.*?)[\"\']', match.group(0))
            alt = alt_match.group(1) if alt_match else ""
            title = title_match.group(1) if title_match else ""
        elif match.re.pattern == patterns[2]:  # Markdown 引用链接格式：![alt][ref]
            ref_key = match.group(2).strip().lower()
            if ref_key in ref_links:
                url, title = ref_links[ref_key]
                alt = match.group(1)

        if url:
            if url.startswith(("http://", "https://")):  # 在线图片
                local_path = download_image(url, folder)
                if local_path:
                    # 替换为相对路径
                    relative_path = os.path.relpath(local_path, os.path.dirname(md_file))
                    success_count += 1
                    logger.info(f"下载成功: {url} -> {relative_path}")
                    if match.re.pattern == patterns[0] or match.re.pattern == patterns[2]:  # Markdown 格式
                        return f'![{alt}]({relative_path} "{title}")' if title else f'![{alt}]({relative_path})'
                    else:  # HTML 格式
                        return match.group(0).replace(url, relative_path)
                else:
                    fail_count += 1
                    logger.error(f"下载失败: {url}")
            elif os.path.isabs(url) or url.startswith(("./", "../")):  # 相对路径图片
                # 直接复制图片到目标文件夹
                src_path = os.path.join(os.path.dirname(md_file), url)
                if os.path.exists(src_path):
                    filename = os.path.basename(src_path)
                    dest_path = os.path.join(folder, filename)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    with open(src_path, "rb") as src, open(dest_path, "wb") as dest:
                        dest.write(src.read())
                    relative_path = os.path.relpath(dest_path, os.path.dirname(md_file))
                    success_count += 1
                    logger.info(f"复制成功: {src_path} -> {relative_path}")
                    if match.re.pattern == patterns[0] or match.re.pattern == patterns[2]:  # Markdown 格式
                        return f'![{alt}]({relative_path} "{title}")' if title else f'![{alt}]({relative_path})'
                    else:  # HTML 格式
                        return match.group(0).replace(url, relative_path)
                else:
                    fail_count += 1
                    logger.error(f"图片不存在: {src_path}")
        else:
            logger.warning(f"跳过非在线图片: {url}")
        return match.group(0)  # 返回原始内容

    # 使用 tqdm 添加进度条
    new_content = md_content
    for pattern in patterns[:3]:  # 只处理前三种格式，引用链接定义不需要替换
        matches = list(re.finditer(pattern, new_content))
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(replace_match, match): match for match in matches}
            for future in tqdm(as_completed(futures), total=len(futures), desc=f"处理 {pattern} 格式", unit="图片"):
                match = futures[future]
                new_content = new_content.replace(match.group(0), future.result())

    # 打印统计信息
    logger.info(f"\n图片处理完成！")
    logger.info(f"成功下载: {success_count}")
    logger.info(f"下载失败: {fail_count}")

    return new_content

def process_markdown_file(md_file: str, image_folder: Optional[str] = None):
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
    os.makedirs(image_folder, exist_ok=True)

    # 读取 Markdown 文件
    try:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"读取文件 {md_file} 失败: {e}")
        return

    # 替换在线图片链接为本地相对路径
    new_content = replace_image_links(content, image_folder, md_file)

    # 保存修改后的 Markdown 文件
    try:
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        logger.info(f"Markdown 文件已更新: {md_file}")
    except Exception as e:
        logger.error(f"保存文件 {md_file} 失败: {e}")

def find_markdown_files(folder: str) -> list:
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

def process_markdown_folder(folder: str, image_folder: Optional[str] = None):
    """
    处理指定文件夹及其子文件夹下的所有 Markdown 文件
    :param folder: Markdown 文件所在文件夹
    :param image_folder: 图片保存文件夹（可选，默认为 ./image/markdown文件名）
    """
    # 递归查找所有 Markdown 文件
    md_files = find_markdown_files(folder)
    logger.info(f"找到 {len(md_files)} 个 Markdown 文件")

    # 处理每个 Markdown 文件
    for md_file in tqdm(md_files, desc="处理 Markdown 文件", unit="文件"):
        process_markdown_file(md_file, image_folder)

def main(input_path: str, image_folder: Optional[str] = None):
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
        logger.error(f"输入路径无效: {input_path}")

"""
主要优化点：
1. 并发下载图片：使用 ThreadPoolExecutor 实现多线程下载。
2. 缓存已下载的图片：避免重复下载。
3. 日志系统：使用 logging 模块记录日志。
4. 支持相对路径的图片：检测并处理相对路径的图片。
5. 支持多种图片格式：包括在线图片和本地图片。
6. 动态图片保存路径：支持自定义路径，并在其后拼接 Markdown 文件名。

"""

if __name__ == "__main__":
    # 设置输入路径（可以是单个 Markdown 文件或文件夹）
    input_path = "C:\\Users\\codeh\\Desktop\\CSNote\\Project"  # 替换为你的 Markdown 文件或文件夹路径

    # 设置图片保存路径（可选，默认为 ./image/markdown文件名）
    image_folder = "./image"  # 替换为你的自定义相对路径，或设置为 None 使用默认路径

    # 处理输入路径
    main(input_path, image_folder)