import json
import os

def save_settings(settings, filename='settings.json'):
    """将用户设置保存到JSON文件"""
    with open(filename, 'w') as f:
        json.dump(settings, f)

def load_settings():
    settings_path = 'settings.json'  # 你的设置文件路径
    if not os.path.exists(settings_path) or os.path.getsize(settings_path) == 0:
        # 文件不存在或文件为空，返回默认设置
        return {
            'rope3d_path': '',
            'image_folder': '',
            'last_file_name': ''
        }
    else:
        with open(settings_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # 处理JSON解析错误，返回默认设置
                return {
                    'rope3d_path': '',
                    'image_folder': '',
                    'last_file_name': ''
                }
