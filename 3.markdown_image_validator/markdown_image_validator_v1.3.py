import re
import requests
from pathlib import Path
from urllib.parse import urlparse, unquote
import base64
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from rich.console import Console
from rich.table import Table

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# 初始化 Rich 控制台
console = Console()


def extract_image_links(markdown_content):
    """提取 Markdown 内容中的图片链接，支持带标题的形式"""
    pattern = r'!\[.*?\]\((.*?)(?:\s*".*?")?\)'
    return re.findall(pattern, markdown_content)


@lru_cache(maxsize=1000)
def check_image_url(url, proxies=None):
    """检查在线图片链接是否有效"""
    try:
        response = requests.head(url, timeout=5, proxies=proxies)
        return response.status_code == 200
    except requests.RequestException:
        return False


@lru_cache(maxsize=1000)
def check_local_image(path, markdown_file_path):
    """检查本地图片是否存在"""
    if not Path(path).is_absolute():
        markdown_dir = Path(markdown_file_path).parent
        absolute_path = (markdown_dir / path).resolve()
        return absolute_path.exists()
    else:
        return Path(path).exists()


def is_base64_image(link):
    """判断链接是否为 Base64 图片"""
    return link.startswith('data:image')


def validate_base64_image(link):
    """验证 Base64 图片是否有效"""
    try:
        base64_data = link.split('base64,')[-1]
        base64.b64decode(base64_data, validate=True)
        return True
    except (IndexError, ValueError, base64.binascii.Error):
        return False


def check_image(link, file_path, proxies=None):
    """检查单个图片链接是否有效"""
    decoded_link = unquote(link)
    if is_base64_image(decoded_link):
        return validate_base64_image(decoded_link)
    else:
        parsed_url = urlparse(decoded_link)
        if parsed_url.scheme in ('http', 'https'):
            return check_image_url(decoded_link, proxies=proxies)
        else:
            return check_local_image(decoded_link, file_path)


def check_images_in_markdown(file_path, invalid_images_dict, proxies=None):
    """检测单个 Markdown 文件中的图片是否有效"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        logger.error(f"读取文件 {file_path} 时出错: {e}")
        return

    image_links = extract_image_links(content)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(check_image, link, file_path, proxies): link
            for link in image_links
        }
        for future in as_completed(futures):
            link = futures[future]
            try:
                if not future.result():
                    invalid_images_dict.setdefault(file_path, []).append(link)
            except Exception as e:
                logger.error(f"检查图片 {link} 时出错: {e}")
                invalid_images_dict.setdefault(file_path, []).append(link)


def find_markdown_files(directory):
    """递归查找目录中的所有 Markdown 文件"""
    return list(Path(directory).rglob('*.md'))


def print_invalid_images(invalid_images_dict):
    """打印无效图片"""
    console = Console(width=150)  # 设置控制台宽度
    table = Table(title="无效图片汇总", width=150)  # 设置表格宽度
    table.add_column("文件", style="dim", width=80, no_wrap=False)  # 允许换行
    table.add_column("无效图片", style="red", width=60, overflow="ellipsis")  # 用省略号截断

    for file_path, invalid_images in invalid_images_dict.items():
        for image in invalid_images:
            table.add_row(str(file_path), image)

    console.print(table)


def check_images_in_directory(directory, proxies=None):
    """递归检查目录中的所有 Markdown 文件"""
    invalid_images_dict = {}
    markdown_files = find_markdown_files(directory)
    for file_path in markdown_files:
        logger.info(f"🔍 检查文件: {file_path}")
        check_images_in_markdown(file_path, invalid_images_dict, proxies=proxies)

    if invalid_images_dict:
        print_invalid_images(invalid_images_dict)
    else:
        logger.info("🎉 所有图片均有效！")


def main(target_path, proxies=None):
    """
    主函数，用于执行图片检测逻辑

    :param target_path: 目标路径（Markdown 文件或目录）
    :param proxies: 代理配置，格式为 {'http': 'http://proxy_url', 'https': 'https://proxy_url'}
    """
    if Path(target_path).is_dir():
        check_images_in_directory(target_path, proxies=proxies)
    elif Path(target_path).is_file() and target_path.endswith('.md'):
        invalid_images_dict = {}
        check_images_in_markdown(target_path, invalid_images_dict, proxies=proxies)
        if invalid_images_dict:
            print_invalid_images(invalid_images_dict)
        else:
            logger.info("🎉 所有图片均有效！")
    else:
        logger.error("❌ 无效路径，请输入一个 Markdown 文件或目录。")


"""
代理支持
"""
if __name__ == "__main__":
    # 设置代理（可选），如果不需要代理，可以将 proxies 设置为 None
    proxies = {
        "http": "http://127.0.0.1:7890",  # 替换为你的 HTTP 代理地址
        "https": "http://127.0.0.1:7890",  # 替换为你的 HTTPS 代理地址
    }

    # 目标路径
    target_path = "C:\\Users\\codeh\\Desktop\\output"  # 替换为你的目录或文件路径

    # 调用主函数
    main(target_path, proxies=proxies)
