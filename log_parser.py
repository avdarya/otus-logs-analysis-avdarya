import json
import os
import re
import argparse
from collections import Counter
import heapq


LOG_RE = re.compile(
    r'^(?P<ip>\d{1,3}(?:\.\d{1,3}){3}) .* '
    r'\[(?P<datetime>[^\]]+)\] '
    r'"(?P<method>[A-Z]+) (?P<url>[^ ]+) HTTP/[0-9.]+" '
    r'\d+ \d+ "[^"]*" "[^"]*" (?P<duration>\d+)$'
)

def get_files(path):
    files = []
    if os.path.isfile(path):
        files.append(path)
    elif os.path.isdir(path):
        for f in os.listdir(path):
            full_path = os.path.join(path, f)
            if os.path.isfile(full_path) and f.endswith('.log'):
                files.append(full_path)
    else:
        raise FileNotFoundError(f'Указанный путь не найден: {path}')
    return files

def generate_report(file, top_ips, top_durations, method_counts, total_requests):
    base_name = os.path.basename(file)
    result_name = f'{base_name}.json'
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
    os.makedirs(results_dir, exist_ok=True)
    result_path = os.path.join(results_dir, result_name)
    with open(result_path, 'w', encoding='utf-8') as result_file:
        result = {
            'top_ips': dict(top_ips),
            'top_longest': top_durations,
            'total_stat': dict(method_counts),
            'total_requests': total_requests
        }
        json.dump(result, result_file, ensure_ascii=False, indent=4)

def print_report(file, top_count, total_requests,  method_counts, top_ips, top_durations):
    print('=' * 60)
    print(f'Отчет для файла: {file}')
    print('=' * 60)
    print(f'Общее количество выполненных запросов: {total_requests}')
    print('Количество запросов по HTTP-методам:')
    for method, count in method_counts.items():
        print(f'{method} - {count}')
    print(f'Топ {top_count} IP адресов:')
    for ip, count in top_ips:
        print(f'{count}: {ip}')
    print(f'Топ {top_count} самых долгих запроса:')
    for req in top_durations:
        print(
            f"{req['date']} {req['ip']} {req['method']} {req['url']} "
            f"длительность={req['duration']} мс"
        )
    print('=' * 60)
    print('Отчет завершен')
    print('=' * 60)

def parse_log():
    cli_parser = argparse.ArgumentParser(description='Парсер логов')
    cli_parser.add_argument(
        '-p',
        '--path',
        type=str,
        required=True,
        help='Путь к директории с лог-файлами или к лог-файлу'
    )
    cli_parser.add_argument(
        '-c',
        '--top_count',
        type=int,
        required=True,
        help='Количество топ-записей в отчете'
    )
    args = cli_parser.parse_args()
    path = args.path
    top_count = args.top_count
    files = get_files(path)

    for file in files:
        total_requests = 0
        method_counts = Counter()
        ip_counts = Counter()
        all_durations = []

        with open(file, "rt", encoding="utf-8", errors="ignore") as f:
            for line in f:
                total_requests += 1

                match = LOG_RE.search(line)
                if match:
                    method_counts[match.group('method')] += 1
                    ip_counts[match.group('ip')] += 1
                    data = {
                        'ip': match.group('ip'),
                        'date': match.group('datetime'),
                        'method': match.group('method'),
                        'url': match.group('url'),
                        'duration': int(match.group('duration'))
                    }
                    all_durations.append(data)
            top_ips = ip_counts.most_common(top_count)
            top_durations = heapq.nlargest(top_count, all_durations, key=lambda x: x['duration'])

        generate_report(file, top_ips, top_durations, method_counts, total_requests)
        print_report(file, top_count, total_requests,  method_counts, top_ips, top_durations)

if __name__ == '__main__':
    parse_log()