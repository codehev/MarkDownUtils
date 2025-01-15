import re
import requests
from pathlib import Path
from urllib.parse import urlparse, unquote
import base64

def extract_image_links(markdown_content):
    """提取 Markdown 内容中的图片链接"""
    # 匹配 Markdown 图片语法：![alt text](url)
    pattern = r'!\[.*?\]\((.*?)\)'
    return re.findall(pattern, markdown_content)

def check_image_url(url):
    """检查在线图片链接是否有效"""
    try:
        response = requests.head(url, timeout=5)
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.RequestException:
        return False

def check_local_image(path, markdown_file_path):
    """检查本地图片是否存在"""
    # 将相对路径转换为绝对路径
    if not Path(path).is_absolute():
        # 获取 Markdown 文件所在目录
        markdown_dir = Path(markdown_file_path).parent
        # 拼接为绝对路径
        absolute_path = markdown_dir / path
        return absolute_path.exists()
    else:
        return Path(path).exists()

def is_base64_image(link):
    """判断链接是否为 Base64 图片"""
    return link.startswith('data:image')

def validate_base64_image(link):
    """验证 Base64 图片是否有效"""
    try:
        # 提取 Base64 部分
        base64_data = link.split('base64,')[-1]
        # 尝试解码
        base64.b64decode(base64_data)
        return True
    except (IndexError, ValueError, base64.binascii.Error):
        return False

def check_images_in_markdown(file_path, invalid_images_dict):
    """检测单个 Markdown 文件中的图片是否有效"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    image_links = extract_image_links(content)
    for link in image_links:
        # 直接对 URL 进行解码（无论是否编码）
        decoded_link = unquote(link)

        if is_base64_image(decoded_link):
            # Base64 图片
            if not validate_base64_image(decoded_link):
                invalid_images_dict.setdefault(file_path, []).append(decoded_link)
        else:
            # 判断是本地图片还是在线图片
            parsed_url = urlparse(decoded_link)
            if parsed_url.scheme in ('http', 'https'):
                # 在线图片
                if not check_image_url(decoded_link):
                    invalid_images_dict.setdefault(file_path, []).append(decoded_link)
            else:
                # 本地图片
                if not check_local_image(decoded_link, file_path):
                    invalid_images_dict.setdefault(file_path, []).append(decoded_link)

def find_markdown_files(directory):
    """递归查找目录中的所有 Markdown 文件"""
    markdown_files = []
    for path in Path(directory).rglob('*.md'):
        markdown_files.append(path)
    return markdown_files

def check_images_in_directory(directory):
    """递归检查目录中的所有 Markdown 文件"""
    invalid_images_dict = {}  # 存储无效图片的字典
    markdown_files = find_markdown_files(directory)
    for file_path in markdown_files:
        print(f"🔍 检查文件: {file_path}")
        check_images_in_markdown(file_path, invalid_images_dict)

    # 按文件分类打印无效图片
    print("\n📂 无效图片汇总:")
    for file_path, invalid_images in invalid_images_dict.items():
        print(f"\n📄 文件: {file_path}")
        for image in invalid_images:
            print(f"❌ 无效图片: {image}")

if __name__ == "__main__":
    # 使用示例
    target_path = "C:\\Users\\codeh\\Desktop\\CSNote\\Project"  # 替换为你的目录或文件路径
    if Path(target_path).is_dir():
        # 如果是目录，递归检查
        check_images_in_directory(target_path)
    elif Path(target_path).is_file() and target_path.endswith('.md'):
        # 如果是单个 Markdown 文件，直接检查
        invalid_images_dict = {}
        check_images_in_markdown(target_path, invalid_images_dict)
        # 打印无效图片
        print("\n📂 无效图片汇总:")
        for file_path, invalid_images in invalid_images_dict.items():
            print(f"\n📄 文件: {file_path}")
            for image in invalid_images:
                print(f"❌ 无效图片: {image}")
    else:
        print("❌ 无效路径，请输入一个 Markdown 文件或目录。")