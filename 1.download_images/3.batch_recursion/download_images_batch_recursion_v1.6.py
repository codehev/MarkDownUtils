import os
import re
import requests
from urllib.parse import urlparse, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from typing import Dict, Tuple, Optional


# 配置日志
def setup_logger(log_file: str):
    """
    配置日志系统，将日志写入文件，并在控制台显示提示信息
    :param log_file: 日志文件路径
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # 文件日志处理器
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)

    # 控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# 初始化日志
log_file = os.path.join(os.getcwd(), "markdown_image_downloader.log")
logger = setup_logger(log_file)

# 缓存已下载的图片
image_cache: Dict[str, str] = {}


def download_image(url: str, folder: str, proxies: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    下载图片并保存到指定文件夹
    :param url: 图片的 URL
    :param folder: 图片保存文件夹
    :param proxies: 代理配置，例如 {"http": "http://proxy-server:port", "https": "http://proxy-server:port"}
    :return: 本地图片路径（如果下载成功），否则返回 None
    """
    if url in image_cache:
        return image_cache[url]

    try:
        response = requests.get(url, timeout=10, allow_redirects=True, proxies=proxies)
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


def replace_image_links(md_content: str, folder: str, md_file: str, proxies: Optional[Dict[str, str]] = None) -> str:
    """
    替换 Markdown 内容中的在线图片链接为本地路径
    :param md_content: Markdown 文件内容
    :param folder: 图片保存文件夹
    :param md_file: Markdown 文件路径
    :param proxies: 代理配置
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
                local_path = download_image(url, folder, proxies=proxies)
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

    # 处理图片链接
    new_content = md_content
    for pattern in patterns[:3]:  # 只处理前三种格式，引用链接定义不需要替换
        matches = list(re.finditer(pattern, new_content))
        logger.info(f"正在处理 {len(matches)} 个图片链接（格式: {pattern}）")
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(replace_match, match): match for match in matches}
            for future in as_completed(futures):
                match = futures[future]
                new_content = new_content.replace(match.group(0), future.result())

    # 打印统计信息
    logger.info("图片处理完成！")
    logger.info(f"成功下载: {success_count}")
    logger.info(f"下载失败: {fail_count}")

    return new_content


def process_markdown_file(md_file: str, image_folder: Optional[str] = None, proxies: Optional[Dict[str, str]] = None):
    """
    处理单个 Markdown 文件，下载在线图片并替换链接
    :param md_file: Markdown 文件路径
    :param image_folder: 图片保存文件夹（可选，默认为 ./image/markdown文件名）
    :param proxies: 代理配置
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
    new_content = replace_image_links(content, image_folder, md_file, proxies=proxies)

    # 保存修改后的 Markdown 文件
    try:
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        logger.info(f"Markdown 文件已更新: {md_file}")
    except Exception as e:
        logger.error(f"保存文件 {md_file} 失败: {e}")

    # 在每个文件处理完成后打印空行
    logger.info("")


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


def process_markdown_folder(folder: str, image_folder: Optional[str] = None, proxies: Optional[Dict[str, str]] = None):
    """
    处理指定文件夹及其子文件夹下的所有 Markdown 文件
    :param folder: Markdown 文件所在文件夹
    :param image_folder: 图片保存文件夹（可选，默认为 ./image/markdown文件名）
    :param proxies: 代理配置
    """
    # 递归查找所有 Markdown 文件
    md_files = find_markdown_files(folder)
    logger.info(f"找到 {len(md_files)} 个 Markdown 文件")

    # 处理每个 Markdown 文件
    for md_file in md_files:
        logger.info(f"=== 处理文件: {md_file} ===")
        process_markdown_file(md_file, image_folder, proxies=proxies)


def main(input_path: str, image_folder: Optional[str] = None, proxies: Optional[Dict[str, str]] = None):
    """
    主函数，根据输入路径是文件还是文件夹进行处理
    :param input_path: 输入的 Markdown 文件或文件夹路径
    :param image_folder: 图片保存文件夹（可选，默认为 ./image/markdown文件名）
    :param proxies: 代理配置
    """
    if os.path.isfile(input_path) and input_path.endswith(".md"):
        # 如果是单个 Markdown 文件
        logger.info(f"=== 处理文件: {input_path} ===")
        process_markdown_file(input_path, image_folder, proxies=proxies)
    elif os.path.isdir(input_path):
        # 如果是文件夹
        process_markdown_folder(input_path, image_folder, proxies=proxies)
    else:
        logger.error(f"输入路径无效: {input_path}")


"""
新增代理参数
"""
if __name__ == "__main__":
    # 设置输入路径（可以是单个 Markdown 文件或文件夹）
    input_path = "C:\\Users\\codeh\\Desktop\\SoftwareTesting.md"  # 替换为你的 Markdown 文件或文件夹路径

    # 设置图片保存路径（可选，默认为 ./image/markdown文件名）
    image_folder = "./image"  # 替换为你的自定义相对路径，或设置为 None 使用默认路径

    # 设置代理（可选），如果不需要代理，可以将 proxies 设置为 None
    proxies = {
        "http": "http://127.0.0.1:7890",  # 替换为你的 HTTP 代理地址
        "https": "https://127.0.0.1:7890",  # 替换为你的 HTTPS 代理地址
    }

    # 处理输入路径
    main(input_path, image_folder, proxies=proxies)
