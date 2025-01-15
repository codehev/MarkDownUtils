import os
import re
import csv

def find_images_in_markdown(file_path):
    """
    查找 Markdown 文件中的图片，并分类统计。
    返回一个字典，包含每种图片引入方式的数量。
    """
    # 匹配 Base64 图片
    base64_pattern = re.compile(r'!\[.*?\]\(data:image\/(png|jpeg|gif|webp|svg\+xml);base64,[^\s]+\)')
    # 匹配本地图片
    local_pattern = re.compile(r'!\[.*?\]\((?!http|data:)(.*?)\)')
    # 匹配网络图片
    network_pattern = re.compile(r'!\[.*?\]\((http[s]?://.*?)\)')
    # 匹配 HTML 标签图片
    html_pattern = re.compile(r'<img.*?src=["\'](.*?)["\'].*?>')

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # 查找所有匹配的图片
            base64_images = base64_pattern.findall(content)
            local_images = local_pattern.findall(content)
            network_images = network_pattern.findall(content)
            html_images = html_pattern.findall(content)

            # 返回每种图片引入方式的数量
            return {
                "base64": len(base64_images),
                "local": len(local_images),
                "network": len(network_images),
                "html": len(html_images),
            }
    except Exception as e:
        print(f"无法读取文件 {file_path}: {e}")
        return {
            "base64": 0,
            "local": 0,
            "network": 0,
            "html": 0,
        }

def traverse_directory(directory):
    """
    递归遍历目录下的所有 Markdown 文件。
    返回一个字典，键为文件路径，值为每种图片引入方式的数量。
    """
    results = {}
    total_files = sum(1 for _, _, files in os.walk(directory) for f in files if f.endswith('.md'))
    processed_files = 0

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                image_stats = find_images_in_markdown(file_path)
                results[file_path] = image_stats

                # 显示进度
                processed_files += 1
                print(f"已处理 {processed_files}/{total_files} 个文件: {file_path}")

    return results

def save_results_to_csv(results, output_file):
    """
    将结果保存到 CSV 文件中。
    """
    try:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:  # 使用 utf-8-sig 编码
            fieldnames = ["文件路径", "Base64 图片", "本地图片", "网络图片", "HTML 图片"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # 写入表头
            writer.writeheader()
            # 写入数据
            for file_path, stats in results.items():
                writer.writerow({
                    "文件路径": file_path,
                    "Base64 图片": stats["base64"],
                    "本地图片": stats["local"],
                    "网络图片": stats["network"],
                    "HTML 图片": stats["html"],
                })
        print(f"结果已保存到 {output_file}")
    except Exception as e:
        print(f"无法保存结果到 CSV 文件: {e}")

if __name__ == "__main__":
    # 直接在代码中设置文件夹路径和输出文件路径
    directory = "C:\\Users\\codeh\\Desktop\\CSNote"  # 修改为你的目标文件夹路径
    output_file = "images_stats_report.csv"  # 结果输出文件路径

    # 遍历目录并查找图片
    results = traverse_directory(directory)

    # 输出结果到控制台和文件
    if results:
        print("以下 Markdown 文件包含图片的详细统计:")
        print("文件路径, Base64 图片, 本地图片, 网络图片, HTML 图片")
        for file_path, stats in results.items():
            print(
                f"{file_path}, {stats['base64']}, {stats['local']}, "
                f"{stats['network']}, {stats['html']}"
            )
    else:
        print("没有找到包含图片的 Markdown 文件。")

    # 将结果保存到 CSV 文件
    save_results_to_csv(results, output_file)