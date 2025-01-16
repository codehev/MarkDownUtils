import re
import os
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


if __name__ == "__main__":
    # 配置
    markdown_file = 'C:\\Users\\codeh\\Desktop\\CSNote\\Project\\oj.md'  # 你的Markdown文件路径
    zoom_factor = 67  # 缩放比例（例如50表示缩小到50%）
    output_file = "C:\\Users\\codeh\\Desktop\\oj.md"  # 可选参数，不填写则覆盖原文件

    # 处理Markdown文件中的图片
    logger = setup_logger()
    logger.info("开始处理 Markdown 文件...")
    try:
        process_markdown_images(markdown_file, zoom_factor, output_file)
        logger.info("处理完成！")
    except Exception as e:
        logger.error(f"处理失败: {e}")