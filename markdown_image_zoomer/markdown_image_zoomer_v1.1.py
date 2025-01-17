import re
import os
import shutil
import logging


def setup_logger():
    """配置日志记录器"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    return logging.getLogger()


def process_markdown_images(markdown_file, zoom_factor=67, output_file=None):
    """
    处理 Markdown 文件中的图片引用，将其转换为 Typora 风格的 <img> 标签，并添加缩放效果。

    :param markdown_file: 输入的 Markdown 文件路径
    :param zoom_factor: 缩放比例（例如50表示缩小到50%）
    :param output_file: 输出的 Markdown 文件路径（可选，默认为None，表示覆盖原文件）
    :return: 更新后的内容
    """
    logger = setup_logger()

    # 检查输入文件是否存在
    if not os.path.exists(markdown_file):
        logger.error(f"输入文件不存在: {markdown_file}")
        raise FileNotFoundError(f"输入文件不存在: {markdown_file}")

    # 读取Markdown文件
    with open(markdown_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # 正则表达式匹配Markdown中的图片链接
    markdown_image_pattern = re.compile(r'!\[(.*?)\]\((.*?)(?:\s+"(.*?)")?\)')  # 匹配 ![alt](url "title")
    html_image_pattern = re.compile(r'<img\s+[^>]*src="(.*?)"[^>]*>')  # 匹配 <img src="url">

    # 替换函数：将Markdown图片语法转换为Typora风格的<img>标签
    def replace_markdown_image(match):
        alt_text = match.group(1)  # 获取alt文本
        image_url = match.group(2)  # 获取图片URL
        title = match.group(3)  # 获取title（可选）
        # 构建Typora风格的<img>标签
        if title:
            img_tag = f'<img src="{image_url}" alt="{alt_text}" title="{title}" style="zoom:{zoom_factor}%;">'
        else:
            img_tag = f'<img src="{image_url}" alt="{alt_text}" style="zoom:{zoom_factor}%;">'
        return img_tag

    # 替换函数：将HTML <img>标签中的图片添加Typora风格的缩放，并移除width和height属性
    def replace_html_image(match):
        img_tag = match.group(0)  # 获取完整的<img>标签
        # 移除width和height属性
        img_tag = re.sub(r'\s(width|height)=".*?"', '', img_tag)
        # 检查是否已经存在zoom属性
        if 'zoom:' in img_tag:
            # 如果已有zoom属性，替换为新的zoom值
            img_tag = re.sub(r'zoom:\s*\d+%;', f'zoom:{zoom_factor}%;', img_tag)
        else:
            # 如果没有zoom属性，添加zoom属性
            if 'style=' in img_tag:
                # 如果已有style属性，追加zoom
                img_tag = re.sub(r'style="(.*?)"', lambda m: f'style="{m.group(1)} zoom:{zoom_factor}%;"', img_tag)
            else:
                # 如果没有style属性，添加style属性
                img_tag = img_tag.replace('>', f' style="zoom:{zoom_factor}%;">')
        return img_tag

    # 替换所有Markdown图片语法
    logger.info("正在处理 Markdown 图片语法...")
    markdown_images = markdown_image_pattern.findall(content)
    if markdown_images:
        logger.info(f"找到 {len(markdown_images)} 张 Markdown 图片。")
        content = markdown_image_pattern.sub(replace_markdown_image, content)
    else:
        logger.info("未找到 Markdown 图片语法。")

    # 替换所有HTML <img>标签
    logger.info("正在处理 HTML <img> 标签...")
    html_images = html_image_pattern.findall(content)
    if html_images:
        logger.info(f"找到 {len(html_images)} 个 HTML <img> 标签。")
        content = html_image_pattern.sub(replace_html_image, content)
    else:
        logger.info("未找到 HTML <img> 标签。")

    # 决定输出文件路径
    if output_file is None:
        output_file = markdown_file  # 覆盖原文件
        logger.info(f'Markdown文件已更新: {output_file}')
    else:
        # 检查输出目录是否存在，如果不存在则创建
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        logger.info(f'Markdown文件已保存到: {output_file}')

    # 将更新后的内容写入输出文件
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(content)

    return content


def copy_local_images(markdown_file, content, output_dir):
    """
    复制 Markdown 文件中引用的本地图片到输出目录。

    :param markdown_file: 输入的 Markdown 文件路径
    :param content: Markdown 文件内容
    :param output_dir: 输出的目录路径
    """
    logger = setup_logger()
    markdown_dir = os.path.dirname(markdown_file)

    # 正则表达式匹配Markdown中的图片链接
    markdown_image_pattern = re.compile(r'!\[.*?\]\((.*?)\)')  # 匹配 ![alt](url)
    html_image_pattern = re.compile(r'<img\s+[^>]*src="(.*?)"[^>]*>')  # 匹配 <img src="url">

    # 获取所有图片链接
    image_urls = markdown_image_pattern.findall(content) + html_image_pattern.findall(content)

    # 复制本地图片
    for image_url in image_urls:
        if not image_url.startswith(('http://', 'https://')):  # 本地图片
            image_path = os.path.join(markdown_dir, image_url)
            if os.path.exists(image_path):
                # 构建输出图片路径
                output_image_path = os.path.join(output_dir, image_url)
                output_image_dir = os.path.dirname(output_image_path)
                if not os.path.exists(output_image_dir):
                    os.makedirs(output_image_dir)
                # 复制图片
                shutil.copy(image_path, output_image_path)
                logger.info(f"已复制图片: {image_path} -> {output_image_path}")
            else:
                logger.warning(f"图片不存在: {image_path}")


def process_directory(input_dir, zoom_factor=67, output_dir=None):
    """
    递归处理目录下的所有 Markdown 文件。

    :param input_dir: 输入的目录路径
    :param zoom_factor: 缩放比例（例如50表示缩小到50%）
    :param output_dir: 输出的目录路径（可选，默认为None，表示覆盖原文件）
    """
    logger = setup_logger()
    logger.info(f"开始处理目录: {input_dir}")

    # 遍历目录下的所有文件
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith('.md'):
                markdown_file = os.path.join(root, file)
                if output_dir:
                    # 构建输出文件路径
                    relative_path = os.path.relpath(root, input_dir)
                    new_output_dir = os.path.join(output_dir, relative_path)
                    os.makedirs(new_output_dir, exist_ok=True)
                    output_file = os.path.join(new_output_dir, file)
                else:
                    output_file = None  # 覆盖原文件

                try:
                    logger.info(f"正在处理文件: {markdown_file}")
                    content = process_markdown_images(markdown_file, zoom_factor, output_file)
                    if output_dir:
                        # 复制本地图片
                        copy_local_images(markdown_file, content, output_dir)
                except Exception as e:
                    logger.error(f"处理文件 {markdown_file} 失败: {e}")

    logger.info("目录处理完成！")


def process_file(input_file, zoom_factor=67, output_dir=None):
    """
    处理单个 Markdown 文件。

    :param input_file: 输入的 Markdown 文件路径
    :param zoom_factor: 缩放比例（例如50表示缩小到50%）
    :param output_dir: 输出的目录路径（可选，默认为None，表示覆盖原文件）
    """
    logger = setup_logger()
    logger.info(f"开始处理文件: {input_file}")

    if output_dir:
        # 构建输出文件路径
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, os.path.basename(input_file))
    else:
        output_file = None  # 覆盖原文件

    try:
        content = process_markdown_images(input_file, zoom_factor, output_file)
        if output_dir:
            # 复制本地图片
            copy_local_images(input_file, content, output_dir)
    except Exception as e:
        logger.error(f"处理文件 {input_file} 失败: {e}")

    logger.info("文件处理完成！")
"""
优化点说明
1. 支持目录递归
2. 支持单文件处理
3. 日志信息优化
"""

if __name__ == "__main__":
    # 配置
    input_path = 'C:\\Users\\codeh\\Desktop\\backup'  # 输入路径（文件或目录）
    zoom_factor = 67  # 缩放比例（例如50表示缩小到50%）
    # output_path = "C:\\Users\\codeh\\Desktop\\output"  # 可选参数，输出目录（可按原文件结构把文件图片复制过来），为None则覆盖原文件图片不做处理
    output_path = None

    # 处理Markdown文件或目录
    logger = setup_logger()
    logger.info("开始处理...")
    try:
        if os.path.isdir(input_path):
            # 如果是目录，递归处理
            process_directory(input_path, zoom_factor, output_path)
        elif os.path.isfile(input_path) and input_path.endswith('.md'):
            # 如果是单个文件，直接处理
            process_file(input_path, zoom_factor, output_path)
        else:
            logger.error("输入路径必须是 Markdown 文件或目录！")
    except Exception as e:
        logger.error(f"处理失败: {e}")
    logger.info("处理完成！")