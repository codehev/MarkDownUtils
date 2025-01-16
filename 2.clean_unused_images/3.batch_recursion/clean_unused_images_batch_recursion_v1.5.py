import os
import re
import urllib.parse
from tqdm import tqdm  # 导入 tqdm 库
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from logging.handlers import RotatingFileHandler

# 创建日志处理器，指定文件编码为 utf-8
handler = RotatingFileHandler(
    'clean_unused_images.log',
    encoding='utf-8',  # 指定文件编码
    maxBytes=5*1024*1024,  # 日志文件最大 5MB
    backupCount=3  # 保留 3 个备份文件
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[handler]  # 使用自定义的处理器
)

# 定义图标
ICON_INFO = "ℹ️"  # 提示信息
ICON_WARNING = "⚠️"  # 警告信息
ICON_ERROR = "❌"  # 错误信息
ICON_SUCCESS = "✅"  # 成功信息
ICON_FILE = "📄"  # 文件信息
ICON_FOLDER = "📁"  # 文件夹信息
ICON_IMAGE = "🖼️"  # 图片信息

def contains_url_encoding(path):
    """检查路径中是否包含合法的 URL 编码"""
    url_encoding_pattern = r"%[0-9A-Fa-f]{2}"
    return re.search(url_encoding_pattern, path) is not None

def decode_path_if_encoded(path):
    """如果路径包含合法的 URL 编码，则进行解码，否则返回原始路径"""
    if contains_url_encoding(path):
        try:
            return urllib.parse.unquote(path)
        except Exception as e:
            logging.error(f"解码路径失败: {path}, 错误: {e}")
            return path
    return path

def normalize_path(path, md_file):
    """统一路径格式"""
    # 解码 URL 编码
    decoded_path = decode_path_if_encoded(path)
    # 转换为绝对路径
    abs_path = os.path.abspath(os.path.join(os.path.dirname(md_file), decoded_path))
    # 规范化路径（统一路径分隔符）
    abs_path = os.path.normpath(abs_path)
    return abs_path

def extract_used_images(md_content, md_file):
    """从 Markdown 内容中提取所有使用的图片路径"""
    used_images = set()

    # 正则表达式匹配 Markdown 图片链接
    md_pattern = r"!\[.*?\]\((.*?)(?:\s+\".*?\")?\)"  # 支持带标题的图片
    for match in re.findall(md_pattern, md_content):
        if not match.startswith(("http://", "https://", "data:image")):
            # 对路径进行解码和规范化
            abs_path = normalize_path(match, md_file)
            logging.info(f"提取的图片路径 (Markdown): {match} -> {abs_path}")
            used_images.add(abs_path)

    # 正则表达式匹配 HTML <img> 标签中的图片链接
    html_pattern = r"<img.*?src=[\"'](.*?)[\"'].*?>"  # 支持带属性和样式的图片
    for match in re.findall(html_pattern, md_content):
        if not match.startswith(("http://", "https://", "data:image")):
            # 对路径进行解码和规范化
            abs_path = normalize_path(match, md_file)
            logging.info(f"提取的图片路径 (HTML): {match} -> {abs_path}")
            used_images.add(abs_path)

    # 正则表达式匹配 Markdown 引用格式的图片链接
    ref_pattern = r"\[.*?\]\[(.*?)\]"  # 匹配引用标识
    ref_link_pattern = r"\[(.*?)\]:\s*(.*?)(?:\s+\".*?\")?\s*$"  # 匹配引用定义
    ref_links = dict(re.findall(ref_link_pattern, md_content, re.MULTILINE))
    for match in re.findall(ref_pattern, md_content):
        if match in ref_links and not ref_links[match].startswith(("http://", "https://", "data:image")):
            # 对路径进行解码和规范化
            abs_path = normalize_path(ref_links[match], md_file)
            logging.info(f"提取的图片路径 (引用): {ref_links[match]} -> {abs_path}")
            used_images.add(abs_path)

    return used_images

def delete_unused_images(md_files, image_folder="image", backup_folder="backup"):
    """删除未使用的图片"""
    total_unused_count = 0  # 总未使用图片数量

    # 创建备份文件夹
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
        logging.info(f"创建备份文件夹: {backup_folder}")

    # 使用多线程处理 Markdown 文件
    with ThreadPoolExecutor() as executor:
        futures = []
        for md_file in md_files:
            futures.append(executor.submit(process_markdown_file, md_file, image_folder, backup_folder))

        for future in tqdm(as_completed(futures), total=len(futures), desc="处理 Markdown 文件", unit="文件"):
            unused_count = future.result()
            total_unused_count += unused_count

    logging.info(f"所有文件处理完成！")
    logging.info(f"总未使用的图片数量: {total_unused_count}")

def process_markdown_file(md_file, image_folder, backup_folder):
    """处理单个 Markdown 文件"""
    unused_count = 0

    # 动态确定图片文件夹
    md_filename = os.path.splitext(os.path.basename(md_file))[0]  # 获取 Markdown 文件名（不含扩展名）
    image_folder_path = os.path.join(os.path.dirname(md_file), image_folder, md_filename)  # 图片文件夹路径

    if not os.path.exists(image_folder_path):
        logging.warning(f"图片文件夹不存在: {image_folder_path}，跳过处理文件: {md_file}")
        return unused_count

    # 提取当前 Markdown 文件中使用的图片路径
    try:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        used_images = extract_used_images(content, md_file)
    except Exception as e:
        logging.error(f"读取文件 {md_file} 失败: {e}")
        return unused_count

    # 获取图片文件夹中的所有文件
    all_images = set()
    for root, _, files in os.walk(image_folder_path):
        for file in files:
            file_path = os.path.abspath(os.path.join(root, file))
            file_path = os.path.normpath(file_path)
            logging.info(f"图片文件夹中的文件: {file_path}")
            all_images.add(file_path)

    # 找到未使用的图片
    unused_images = all_images - used_images
    unused_count = len(unused_images)

    # 删除未使用的图片
    if unused_images:
        logging.info(f"正在处理文件: {md_file}")
        logging.info(f"图片文件夹: {image_folder_path}")
        logging.warning(f"未使用的图片数量: {unused_count}")
        for image in unused_images:
            try:
                # 备份未使用的图片
                backup_path = os.path.join(backup_folder, os.path.basename(image))
                shutil.move(image, backup_path)
                logging.info(f"备份成功: {image} -> {backup_path}")
            except Exception as e:
                logging.error(f"备份失败: {image}, 错误: {e}")
    else:
        logging.info(f"文件 {md_file} 没有未使用的图片。")

    return unused_count

def find_markdown_files(path):
    """查找指定路径中的所有 Markdown 文件（如果是目录则递归查找）"""
    md_files = []
    if os.path.isfile(path) and path.endswith(".md"):
        # 如果是单个 Markdown 文件
        md_files.append(path)
    elif os.path.isdir(path):
        # 如果是目录，递归查找所有 Markdown 文件
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".md"):
                    md_files.append(os.path.join(root, file))
    else:
        logging.error(f"路径 {path} 不是有效的 Markdown 文件或目录。")
    return md_files
"""
优化点
备份功能：
在删除未使用的图片之前，先将其备份到 backup 文件夹中，防止误删。

日志记录：
使用 logging 模块记录脚本的运行日志，方便后续查看和分析。

多线程支持：
使用 ThreadPoolExecutor 实现多线程处理，加速 Markdown 文件的处理。

路径规范化：
使用 os.path.abspath 和 os.path.normpath 统一路径格式，确保路径在集合中完全一致。

错误处理：
增加更多的异常处理逻辑，确保脚本的健壮性。
"""
if __name__ == "__main__":
    # 设置 Markdown 文件或目录路径
    path = "C:\\Users\\codeh\\Desktop\\CSNote"  # 替换为你的 Markdown 文件或目录路径

    # 设置图片保存路径（相对于当前处理的 Markdown 文件的相对路径）
    image_folder = "image"

    # 设置备份文件夹（绝对路径）
    backup_folder = "backup"

    # 查找所有 Markdown 文件
    md_files = find_markdown_files(path)
    logging.info(f"找到 {len(md_files)} 个 Markdown 文件")

    # 删除未使用的图片
    delete_unused_images(md_files, image_folder, backup_folder)