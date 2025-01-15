import os
import re
import urllib.parse
from tqdm import tqdm  # 导入 tqdm 库

def contains_url_encoding(path):
    """检查路径中是否包含合法的 URL 编码"""
    # URL 编码的格式是 % 后跟两个十六进制字符
    url_encoding_pattern = r"%[0-9A-Fa-f]{2}"
    # re.search执行正则搜索的工具方法
    # 不去手动对匹配到得部分分别进行解码，而是只要包含，说明就是URL编码了，返回true，就给解码的工具类去进行解码就行
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

def delete_unused_images(md_files):
    """删除未使用的图片"""
    total_unused_count = 0  # 总未使用图片数量

    # 遍历所有 Markdown 文件
    for md_file in tqdm(md_files, desc="处理 Markdown 文件", unit="文件"):
        # 动态确定图片文件夹
        md_filename = os.path.splitext(os.path.basename(md_file))[0]  # 获取 Markdown 文件名（不含扩展名）
        image_folder = os.path.join(os.path.dirname(md_file), "image", md_filename)  # 图片文件夹路径

        if not os.path.exists(image_folder):
            print(f"\n图片文件夹不存在: {image_folder}，跳过处理文件: {md_file}")
            continue

        # 提取当前 Markdown 文件中使用的图片路径
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        used_images = extract_used_images(content, md_file)

        # 获取图片文件夹中的所有文件
        all_images = set()
        for root, _, files in os.walk(image_folder):
            for file in files:
                file_path = os.path.normpath(os.path.join(root, file))
                print(f"图片文件夹中的文件: {file_path}")
                all_images.add(file_path)

        # 找到未使用的图片
        unused_images = all_images - used_images
        total_unused_count += len(unused_images)

        # 删除未使用的图片
        if unused_images:
            print(f"\n正在处理文件: {md_file}")
            print(f"图片文件夹: {image_folder}")
            print(f"未使用的图片数量: {len(unused_images)}")
            for image in tqdm(unused_images, desc="删除未使用的图片", unit="图片"):
                try:
                    os.remove(image)
                    print(f"删除成功: {image}")
                except Exception as e:
                    print(f"删除失败: {image}, 错误: {e}")
        else:
            print(f"\n文件 {md_file} 没有未使用的图片。")

    print(f"\n所有文件处理完成！")
    print(f"总未使用的图片数量: {total_unused_count}")

def find_markdown_files(folder):
    """递归查找指定文件夹及其子文件夹中的所有 Markdown 文件"""
    md_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))
    return md_files
"""
Typora支持插入时自动转义图片URL，有些特殊字符（含中文）会被转义，所以得先解码URL再去找图片
目前我是开启了转义功能

add: 支持解码URL
URL 不一定被转义，直接对所有路径进行 URL 解码可能会导致问题。


URL 编码的格式是 % 后跟两个十六进制字符（如 %20、%E6）。
如果 % 后不是两个十六进制字符，则认为它是普通字符，不需要解码。


urllib.parse.unquote 函数对未编码的 URL 进行解码时，
不会产生任何错误或副作用，只是原样返回输入。因此，我们完全可以直接对所有 URL 进行解码，而无需先判断是否编码。
暂时没去掉判断是否编码，但也不影响

"""
if __name__ == "__main__":
    # 设置 Markdown 文件所在文件夹
    md_folder = "C:\\Users\\codeh\\Desktop\\CSNote"  # 替换为你的 Markdown 文件所在文件夹

    # 递归查找所有 Markdown 文件
    md_files = find_markdown_files(md_folder)
    print(f"找到 {len(md_files)} 个 Markdown 文件")

    # 删除未使用的图片
    delete_unused_images(md_files)