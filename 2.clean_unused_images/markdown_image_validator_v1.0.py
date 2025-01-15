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

def check_images_in_markdown(file_path):
    """检测 Markdown 文件中的图片是否有效"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    image_links = extract_image_links(content)
    for link in image_links:
        # 对 URL 进行解码
        # urllib.parse.unquote 函数对未编码的 URL 进行解码时，
        # 不会产生任何错误或副作用，只是原样返回输入。因此，我们完全可以直接对所有 URL 进行解码，而无需先判断是否编码。
        decoded_link = unquote(link)

        if is_base64_image(decoded_link):
            # Base64 图片
            if validate_base64_image(decoded_link):
                print(f"✅ Base64 图片有效: {decoded_link[:50]}...")  # 只显示前50个字符
            else:
                print(f"❌ Base64 图片无效: {decoded_link[:50]}...")
        else:
            # 判断是本地图片还是在线图片
            parsed_url = urlparse(decoded_link)
            if parsed_url.scheme in ('http', 'https'):
                # 在线图片
                if check_image_url(decoded_link):
                    print(f"✅ 在线图片链接有效: {decoded_link}")
                else:
                    print(f"❌ 在线图片链接无效: {decoded_link}")
            else:
                # 本地图片
                if check_local_image(decoded_link, file_path):
                    print(f"✅ 本地图片存在: {decoded_link}")
                else:
                    print(f"❌ 本地图片不存在: {decoded_link}")

"""
可用来图片清理后，进行检测，以防删错
"""
if __name__ == "__main__":
    # 使用示例
    markdown_file = "C:\\Users\\codeh\\Desktop\\CSNote\\Project\\bi.md"  # 替换为你的 Markdown 文件路径
    check_images_in_markdown(markdown_file)