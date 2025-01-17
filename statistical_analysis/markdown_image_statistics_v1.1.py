import os
import re
import pandas as pd

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

def save_results_to_excel(results, output_file):
    """
    将结果保存到 Excel 文件中，包含两个 Sheet：
    - Sheet1: 按文件路径统计
    - Sheet2: 按目录结构分类统计
    """
    try:
        # 创建按文件路径统计的 DataFrame
        file_stats = []
        for file_path, stats in results.items():
            file_stats.append({
                "文件路径": file_path,
                "Base64 图片": stats["base64"],
                "本地图片": stats["local"],
                "网络图片": stats["network"],
                "HTML 图片": stats["html"],
            })
        df_file_stats = pd.DataFrame(file_stats)

        # 创建按目录结构分类统计的 DataFrame
        dir_stats = {}
        for file_path, stats in results.items():
            dir_path = os.path.dirname(file_path)
            if dir_path not in dir_stats:
                dir_stats[dir_path] = {
                    "Base64 图片": 0,
                    "本地图片": 0,
                    "网络图片": 0,
                    "HTML 图片": 0,
                }
            dir_stats[dir_path]["Base64 图片"] += stats["base64"]
            dir_stats[dir_path]["本地图片"] += stats["local"]
            dir_stats[dir_path]["网络图片"] += stats["network"]
            dir_stats[dir_path]["HTML 图片"] += stats["html"]
        df_dir_stats = pd.DataFrame([
            {"目录路径": dir_path, **stats} for dir_path, stats in dir_stats.items()
        ])

        # 将两个 DataFrame 写入同一个 Excel 文件的不同 Sheet
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df_file_stats.to_excel(writer, sheet_name="按文件路径统计", index=False)
            df_dir_stats.to_excel(writer, sheet_name="按目录结构统计", index=False)

        print(f"结果已保存到 {output_file}")
    except Exception as e:
        print(f"无法保存结果到 Excel 文件: {e}")
"""
主要目的是为了。复制过来是，有没有无效的base64图片

保持按文件路径统计的同时
add: 新增一个Sheet按目录结构分类统计
"""
if __name__ == "__main__":
    # 直接在代码中设置文件夹路径和输出文件路径
    directory = "C:\\Users\\codeh\\Desktop\\CSNote"  # 修改为你的目标文件夹路径
    output_file = "images_stats_report.xlsx"  # 结果输出文件路径

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

    # 将结果保存到 Excel 文件
    save_results_to_excel(results, output_file)