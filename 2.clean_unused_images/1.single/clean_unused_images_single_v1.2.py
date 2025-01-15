import os
import re
import urllib.parse
from tqdm import tqdm  # 导入 tqdm 库

def contains_url_encoding(path):
    """检查路径中是否包含合法的 URL 编码"""
    # URL 编码的格式是 % 后跟两个十六进制字符
    url_encoding_pattern = r"%[0-9A-Fa-f]{2}"
    return re.search(url_encoding_pattern, path) is not None

def decode_path_if_encoded(path):
    """如果路径包含合法的 URL 编码，则进行解码，否则返回原始路径"""
    if contains_url_encoding(path):
        try:
            # urllib.parse.unquote 函数对未编码的 URL 进行解码时，
            # 不会产生任何错误或副作用，只是原样返回输入。因此，我们完全可以直接对所有 URL 进行解码，而无需先判断是否编码。
            return urllib.parse.unquote(path)
        except Exception as e:
            print(f"解码路径失败: {path}, 错误: {e}")
            return path
    return path

def extract_used_images(md_content, md_file):
    """从 Markdown 内容中提取所有使用的图片路径"""
    used_images = set()

    # 正则表达式匹配 Markdown 图片链接
    md_pattern = r"!\[.*?\]\((.*?)(?:\s+\".*?\")?\)"  # 支持带标题的图片
    for match in re.findall(md_pattern, md_content):
        if not match.startswith(("http://", "https://", "data:image")):
            # 对路径进行解码（如果需要）
            decoded_path = decode_path_if_encoded(match)
            # 将路径转换为绝对路径
            abs_path = os.path.normpath(os.path.join(os.path.dirname(md_file), decoded_path))
            print(f"提取的图片路径 (Markdown): {match} -> {abs_path}")
            used_images.add(abs_path)

    # 正则表达式匹配 HTML <img> 标签中的图片链接
    html_pattern = r"<img.*?src=[\"'](.*?)[\"'].*?>"  # 支持带属性和样式的图片
    for match in re.findall(html_pattern, md_content):
        if not match.startswith(("http://", "https://", "data:image")):
            # 对路径进行解码（如果需要）
            decoded_path = decode_path_if_encoded(match)
            # 将路径转换为绝对路径
            abs_path = os.path.normpath(os.path.join(os.path.dirname(md_file), decoded_path))
            print(f"提取的图片路径 (HTML): {match} -> {abs_path}")
            used_images.add(abs_path)

    # 正则表达式匹配 Markdown 引用格式的图片链接
    ref_pattern = r"\[.*?\]\[(.*?)\]"  # 匹配引用标识
    ref_link_pattern = r"\[(.*?)\]:\s*(.*?)(?:\s+\".*?\")?\s*$"  # 匹配引用定义
    ref_links = dict(re.findall(ref_link_pattern, md_content, re.MULTILINE))
    for match in re.findall(ref_pattern, md_content):
        if match in ref_links and not ref_links[match].startswith(("http://", "https://", "data:image")):
            # 对路径进行解码（如果需要）
            decoded_path = decode_path_if_encoded(ref_links[match])
            # 将路径转换为绝对路径
            abs_path = os.path.normpath(os.path.join(os.path.dirname(md_file), decoded_path))
            print(f"提取的图片路径 (引用): {ref_links[match]} -> {abs_path}")
            used_images.add(abs_path)

    return used_images

def delete_unused_images(md_file):
    """删除未使用的图片"""
    # 动态确定图片文件夹
    md_filename = os.path.splitext(os.path.basename(md_file))[0]  # 获取 Markdown 文件名（不含扩展名）
    image_folder = os.path.join(os.path.dirname(md_file), "image", md_filename)  # 图片文件夹路径

    if not os.path.exists(image_folder):
        print(f"\n图片文件夹不存在: {image_folder}，跳过处理文件: {md_file}")
        return

    # 读取 Markdown 文件
    try:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"\n读取文件 {md_file} 失败: {e}")
        return

    # 提取使用的图片路径
    used_images = extract_used_images(content, md_file)
    print(f"\nMarkdown 文件中使用的图片数量: {len(used_images)}")

    # 获取图片文件夹中的所有文件
    all_images = set()
    for root, _, files in os.walk(image_folder):
        for file in files:
            file_path = os.path.normpath(os.path.join(root, file))
            print(f"图片文件夹中的文件: {file_path}")
            all_images.add(file_path)

    print(f"图片文件夹中的图片数量: {len(all_images)}")

    # 找到未使用的图片
    unused_images = all_images - used_images
    print(f"未使用的图片数量: {len(unused_images)}")

    # 删除未使用的图片
    if unused_images:
        print("\n开始删除未使用的图片...")
        for image in tqdm(unused_images, desc="删除未使用的图片", unit="图片"):
            try:
                os.remove(image)
                print(f"删除成功: {image}")
            except Exception as e:
                print(f"删除失败: {image}, 错误: {e}")
    else:
        print("\n没有未使用的图片需要删除。")

"""
1. 支持 URL 解码：
新增 decode_path_if_encoded 函数，用于解码包含 URL 编码的图片路径
（如 %E6%8E%A5%E5%8F%A3%E9%9A%94%E7%A6%BB%E5%8E%9F%E5%88%991.png）。
2. 增强路径处理：使用 os.path.normpath 和 os.path.relpath 规范化路径，确保路径格式一致。
3. 增强错误处理：在读取文件和删除文件时增加 try-except 块，避免程序因异常中断。
4. 增强调试信息：增加详细的日志输出，方便排查问题。

urllib.parse.unquote 函数对未编码的 URL 进行解码时，
不会产生任何错误或副作用，只是原样返回输入。因此，我们完全可以直接对所有 URL 进行解码，而无需先判断是否编码。
暂时没去掉判断是否编码，但也不影响

"""
if __name__ == "__main__":
    # 设置 Markdown 文件路径
    md_file = "C:\\Users\\codeh\\Desktop\\CSNote\\Project\\bi.md"  # 替换为你的 Markdown 文件路径

    # 删除未使用的图片
    delete_unused_images(md_file)