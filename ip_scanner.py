import requests
import argparse
import concurrent.futures
import time
import sys
import os
from urllib3.exceptions import InsecureRequestWarning
from datetime import datetime

# 禁用不安全请求的警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def visit_ip(ip_port, protocol="http", timeout=5, path="/", method="GET", headers=None, verbose=False):
    """访问单个IP地址（支持IP:PORT格式）"""
    if not ip_port.strip():
        return None
    
    # 解析IP:PORT格式
    if ":" in ip_port:
        ip, port = ip_port.rsplit(":", 1)
        try:
            port = int(port)
        except ValueError:
            if verbose:
                print(f"[!] 警告: 无效的端口格式 '{port}'，将使用默认端口")
            port = 80
    else:
        ip = ip_port
        port = 80
    
    # 格式化URL
    url = f"{protocol}://{ip.strip()}"
    if port:
        url = f"{url}:{port}"
    url = f"{url}{path}"
    
    if verbose:
        print(f"[*] 正在访问: {url}")
    
    result = {
        "url": url,
        "ip_port": ip_port,
        "status": "失败",
        "status_code": None,
        "response_size": 0,
        "time": 0,
        "error": None,
        "title": None,  # 添加页面标题字段
        "content_type": None  # 添加内容类型字段
    }
    
    try:
        start_time = time.time()
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout, verify=False, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=timeout, verify=False, headers=headers)
        elif method.upper() == "HEAD":
            response = requests.head(url, timeout=timeout, verify=False, headers=headers)
        else:
            response = requests.get(url, timeout=timeout, verify=False, headers=headers)
        
        end_time = time.time()
        result["status"] = "成功"
        result["status_code"] = response.status_code
        result["response_size"] = len(response.content)
        result["time"] = round((end_time - start_time) * 1000)  # 毫秒
        
        # 尝试获取页面标题
        if method.upper() != "HEAD" and 'text/html' in response.headers.get('Content-Type', '').lower():
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    result["title"] = title_tag.text.strip()
            except:
                pass
        
        # 记录内容类型
        result["content_type"] = response.headers.get('Content-Type', 'unknown')
        
        if verbose:
            title_info = f", 标题: {result['title']}" if result["title"] else ""
            print(f"[+] 成功: {url} - 状态码: {response.status_code}, 大小: {len(response.content)} 字节, 耗时: {result['time']}ms{title_info}")
    
    except requests.exceptions.ConnectTimeout:
        result["error"] = "连接超时"
        if verbose:
            print(f"[-] 失败: {url} - 连接超时")
    
    except requests.exceptions.ReadTimeout:
        result["error"] = "读取超时"
        if verbose:
            print(f"[-] 失败: {url} - 读取超时")
    
    except requests.exceptions.ConnectionError:
        result["error"] = "连接错误"
        if verbose:
            print(f"[-] 失败: {url} - 连接错误")
    
    except Exception as e:
        result["error"] = str(e)
        if verbose:
            print(f"[-] 失败: {url} - {str(e)}")
    
    return result

def generate_html_report(results, output_file, scan_info=None):
    """生成HTML报告"""
    
    # 计算统计信息
    total = len(results)
    success = sum(1 for r in results if r["status"] == "成功")
    failed = total - success
    
    # 按状态码分组
    status_groups = {}
    for result in results:
        if result["status_code"]:
            group = f"{result['status_code']} ({result['status_code']//100}xx)"
            if group not in status_groups:
                status_groups[group] = 0
            status_groups[group] += 1
    
    # 生成状态码统计HTML
    status_stats = ""
    for group, count in sorted(status_groups.items()):
        status_stats += f"<span class='stat-item'>{group}: {count}</span> "
    
    # 当前时间
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # HTML模板 - 使用三重引号和替换变量
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IP访问结果报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        .summary {{
            background-color: #e1f5fe;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        .stats {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 15px;
        }}
        .stat-box {{
            background-color: #f8f9fa;
            border-radius: 6px;
            padding: 10px 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            min-width: 120px;
        }}
        .stat-item {{
            background-color: #e9ecef;
            padding: 4px 8px;
            border-radius: 4px;
            margin-right: 5px;
            display: inline-block;
            margin-bottom: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
            position: sticky;
            top: 0;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .success {{
            background-color: #e8f5e9;
        }}
        .fail {{
            background-color: #ffebee;
        }}
        .status-200 {{ background-color: #e8f5e9; }}
        .status-300 {{ background-color: #e1f5fe; }}
        .status-400 {{ background-color: #fff8e1; }}
        .status-500 {{ background-color: #ffebee; }}
        .search-box {{
            padding: 10px 0;
            margin-bottom: 20px;
        }}
        #search {{
            padding: 8px 12px;
            width: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .url {{
            word-break: break-all;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            font-size: 12px;
            color: #777;
        }}
        @media print {{
            body {{
                padding: 0;
                background-color: white;
            }}
            .container {{
                box-shadow: none;
                padding: 0;
            }}
            .no-print {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>IP访问结果报告</h1>
        
        <div class="summary">
            <h3>扫描信息</h3>
            <p><strong>扫描时间:</strong> {current_time}</p>
            {f'<p><strong>扫描参数:</strong> {scan_info}</p>' if scan_info else ''}
        </div>
        
        <div class="stats">
            <div class="stat-box">
                <h3>总体统计</h3>
                <p>总URL数: <strong>{total}</strong></p>
                <p>成功: <strong>{success}</strong></p>
                <p>失败: <strong>{failed}</strong></p>
            </div>
            
            <div class="stat-box">
                <h3>状态码分布</h3>
                <div>
                    {status_stats}
                </div>
            </div>
        </div>
        
        <div class="search-box no-print">
            <input type="text" id="search" placeholder="搜索URL、状态码或IP...">
        </div>
        
        <table id="results-table">
            <thead>
                <tr>
                    <th>序号</th>
                    <th>URL</th>
                    <th>IP:端口</th>
                    <th>状态码</th>
                    <th>响应大小</th>
                    <th>响应时间</th>
                    <th>页面标题</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # 添加表格行
    for i, result in enumerate(results, 1):
        status_class = ""
        if result["status_code"]:
            status_class = f"status-{result['status_code'] // 100}00"
        elif result["status"] == "失败":
            status_class = "fail"
        
        title = result.get("title", "") or ""
        title = title.replace('"', '&quot;')
        
        html_template += f"""                <tr class="{status_class}">
                    <td>{i}</td>
                    <td class="url"><a href="{result['url']}" target="_blank">{result['url']}</a></td>
                    <td>{result['ip_port']}</td>
                    <td>{result['status_code'] or '连接失败'}</td>
                    <td>{result['response_size']} 字节</td>
                    <td>{result['time']} ms</td>
                    <td title="{title}">{title[:50]}{('...' if len(title) > 50 else '')}</td>
                </tr>
"""
    
    # 结束HTML
    html_template += """            </tbody>
        </table>
        
        <div class="footer">
            <p>生成于 """ + current_time + """ | 使用IP批量访问脚本</p>
        </div>
    </div>
    
    <script>
        document.getElementById('search').addEventListener('keyup', function() {
            const value = this.value.toLowerCase();
            const rows = document.querySelectorAll('#results-table tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(value) ? '' : 'none';
            });
        });
    </script>
</body>
</html>
"""
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    return True

def get_script_dir():
    """获取脚本所在的目录"""
    return os.path.dirname(os.path.abspath(__file__))

def create_ip_folder(ip_ports):
    """根据IP:PORT列表创建文件夹
    如果所有记录都是同一个IP（不同端口），使用完整IP命名
    如果是多个不同IP，使用共同前缀加点命名（例如：1.1.1.）
    """
    if not ip_ports:
        return os.path.join(get_script_dir(), "ip_scan_results")
    
    # 提取所有唯一的IP地址（不包括端口）
    unique_ips = set()
    for ip_port in ip_ports:
        ip = ip_port.split(":")[0] if ":" in ip_port else ip_port
        unique_ips.add(ip)
    
    # 如果只有一个唯一的IP地址，使用完整IP
    if len(unique_ips) == 1:
        folder_name = next(iter(unique_ips))  # 获取集合中唯一的元素
    else:
        # 多个不同IP的情况，取第一个IP的前三段加点
        first_ip = ip_ports[0].split(":")[0] if ":" in ip_ports[0] else ip_ports[0]
        ip_parts = first_ip.split('.')
        if len(ip_parts) >= 3:  # 至少要有3段
            folder_name = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}."
        else:
            folder_name = 'ip_scan_results'
    
    # 创建文件夹
    script_dir = get_script_dir()
    folder_path = os.path.join(script_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    return folder_path

def main():
    parser = argparse.ArgumentParser(description="批量访问IP地址脚本 - 支持IP:PORT格式和状态码过滤")
    parser.add_argument("-i", "--ip", help="单个IP地址或IP:PORT格式")
    parser.add_argument("-f", "--file", help="包含IP地址的文件，每行一个IP或IP:PORT")
    parser.add_argument("-P", "--protocol", default="http", choices=["http", "https"], help="协议，默认http")
    parser.add_argument("-t", "--timeout", type=int, default=5, help="超时时间(秒)，默认5秒")
    parser.add_argument("-m", "--method", default="GET", choices=["GET", "POST", "HEAD"], help="HTTP方法，默认GET")
    parser.add_argument("-u", "--url-path", default="/", help="URL路径，默认/")
    parser.add_argument("-c", "--concurrent", type=int, default=10, help="并发数量，默认10")
    parser.add_argument("-o", "--output", help="结果输出文件(.csv格式)")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    parser.add_argument("-a", "--user-agent", default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36", help="自定义User-Agent")
    parser.add_argument("-s", "--status-code", type=int, help="只显示指定状态码的结果")
    parser.add_argument("--status-range", help="状态码范围 (例如: 200-299 表示2xx状态码)")
    parser.add_argument("--html", help="生成HTML报告文件")
    # 新增参数: 导出状态码为200的URL
    parser.add_argument("--export-200", help="导出状态码为200的URL到指定文件")
    
    args = parser.parse_args()
    
    # 检查是否提供了IP或文件
    if not args.ip and not args.file:
        parser.print_help()
        print("\n错误: 必须提供IP地址(-i)或IP地址文件(-f)")
        sys.exit(1)
    
    # 获取IP列表
    ip_list = []
    if args.ip:
        ip_list.append(args.ip)
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"错误: 文件不存在 - {args.file}")
            sys.exit(1)
        with open(args.file, 'r') as f:
            ip_list.extend([line.strip() for line in f if line.strip()])
    
    if not ip_list:
        print("错误: 没有找到有效的IP地址")
        sys.exit(1)
    
    # 解析状态码范围
    status_min = None
    status_max = None
    if args.status_range:
        try:
            parts = args.status_range.split('-')
            if len(parts) == 2:
                status_min = int(parts[0])
                status_max = int(parts[1])
            else:
                print("警告: 状态码范围格式不正确，应为 'min-max'")
        except ValueError:
            print("警告: 状态码范围必须是数字")
    
    # 设置请求头
    headers = {
        "User-Agent": args.user_agent
    }
    
    print(f"[*] 开始批量访问 {len(ip_list)} 个IP地址，并发数: {args.concurrent}")
    results = []
    
    # 使用线程池并发访问
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrent) as executor:
        future_to_ip = {
            executor.submit(
                visit_ip, 
                ip_port, 
                args.protocol, 
                args.timeout, 
                args.url_path, 
                args.method, 
                headers, 
                args.verbose
            ): ip_port for ip_port in ip_list
        }
        
        completed = 0
        for future in concurrent.futures.as_completed(future_to_ip):
            result = future.result()
            if result:
                results.append(result)
            
            completed += 1
            if not args.verbose:
                # 显示进度
                sys.stdout.write(f"\r[*] 进度: {completed}/{len(ip_list)} ({int(completed/len(ip_list)*100)}%)")
                sys.stdout.flush()
    
    if not args.verbose:
        print()  # 换行
    
    # 过滤结果
    filtered_results = []
    for result in results:
        # 如果指定了单个状态码
        if args.status_code is not None:
            if result["status_code"] == args.status_code:
                filtered_results.append(result)
        # 如果指定了状态码范围
        elif status_min is not None and status_max is not None:
            if result["status_code"] is not None and status_min <= result["status_code"] <= status_max:
                filtered_results.append(result)
        # 没有过滤条件，保留所有结果
        else:
            filtered_results.append(result)
    
    # 汇总结果
    success_count = sum(1 for r in filtered_results if r["status"] == "成功")
    
    # 如果有过滤条件，显示过滤信息
    if args.status_code is not None:
        print(f"\n[*] 过滤状态码: {args.status_code}")
        print(f"[*] 过滤后结果数: {len(filtered_results)}/{len(results)}")
    elif status_min is not None and status_max is not None:
        print(f"\n[*] 过滤状态码范围: {status_min}-{status_max}")
        print(f"[*] 过滤后结果数: {len(filtered_results)}/{len(results)}")
    else:
        print(f"\n[*] 访问完成，总计: {len(results)}，成功: {success_count}，失败: {len(results) - success_count}")
    
    # 创建IP命名的文件夹
    ip_folder = create_ip_folder([r["ip_port"] for r in filtered_results])
    print(f"[*] 创建结果文件夹: {ip_folder}")
    
    # 只有当明确指定了--output参数时才生成CSV文件
    if args.output:
        # 将输出文件保存到IP文件夹中
        csv_path = os.path.join(ip_folder, os.path.basename(args.output))
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write("URL,原始IP:端口,状态,状态码,响应大小(字节),耗时(ms),页面标题,错误\n")
            for result in filtered_results:
                title = result.get("title", "").replace(",", " ").replace('"', '""') if result.get("title") else ""
                f.write(f'"{result["url"]}",{result["ip_port"]},{result["status"]},{result["status_code"] or "N/A"},{result["response_size"]},{result["time"]},"{title}",{result["error"] or "N/A"}\n')
        print(f"[+] 结果已保存到CSV: {csv_path}")

    # 只有当明确指定了--html参数时才生成HTML报告
    if args.html:
        # 将HTML文件路径转换为绝对路径，确保保存在IP文件夹中
        html_path = os.path.join(ip_folder, os.path.basename(args.html))
        
        scan_info = f"协议:{args.protocol}, 路径:{args.url_path}, 方法:{args.method}"
        if args.status_code:
            scan_info += f", 状态码过滤:{args.status_code}"
        elif status_min and status_max:
            scan_info += f", 状态码范围:{status_min}-{status_max}"
            
        if generate_html_report(filtered_results, html_path, scan_info):
            print(f"[+] HTML报告已保存到: {html_path}")
        else:
            print(f"[-] HTML报告生成失败")

    # 导出状态码为200的URL到指定文件
    if args.export_200:
        # 将导出文件路径转换为绝对路径，确保保存在IP文件夹中
        export_path = os.path.join(ip_folder, os.path.basename(args.export_200))
        
        status_200_results = [r for r in results if r["status_code"] == 200]
        with open(export_path, 'w', encoding='utf-8') as f:
            for result in status_200_results:
                f.write(f"{result['url']}\n")
        print(f"[+] 状态码为200的URL已导出到: {export_path} (共 {len(status_200_results)} 个)")

    # 打印过滤后的可访问URL
    if filtered_results:
        print("\n符合条件的URL:")
        for result in filtered_results:
            status_info = f"状态码: {result['status_code']}" if result["status_code"] else "连接失败"
            title_info = f", 标题: {result['title']}" if result.get("title") else ""
            print(f"{result['url']} - {status_info}, 大小: {result['response_size']}字节{title_info}")
    else:
        print("\n没有符合条件的URL")

if __name__ == "__main__": 
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] 操作被用户中断")
        sys.exit(0)