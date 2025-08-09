# =========================================================
#  THIS IS THE COMPLETE AND FINAL VERSION OF app.py
# =========================================================
import os
from ruamel.yaml import YAML
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import docker
import requests

# --- 初始化 Flask 应用 ---
app = Flask(__name__)
app.secret_key = 'super_secret_key_for_flask_flash_messages'

# --- 全局常量和配置 ---
CONFIG_DIR = '/config'
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR, 'config.yaml')

# 前端显示的中文翻译映射
HIDE_OPTIONS_MAP = {
    'music': '音乐',
    'tvshows': '电视剧',
    'movies': '电影',
    'boxsets': '影盒',
    'playlists': '播放列表'
}
RESOURCE_TYPE_MAP = {
    'collection': '合集',
    'tag': '标签',
    'genre': '类型',
    'studio': '工作室',
    'person': '个人'
}

# 初始化 ruamel.yaml 并设置完美的缩进格式
yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)

# --- 新增：用于缓存 Emby 数据的全局变量 ---
EMBY_DATA_CACHE = {}

# --- 核心功能函数 ---

def to_int_if_possible(value):
    """
    一个辅助函数，如果一个字符串是纯数字，就把它转换成整数，否则原样返回。
    """
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value

def restart_emby_virtual_lib():
    """
    使用 Docker SDK 重启 emby-virtual-lib 容器。
    """
    try:
        client = docker.from_env()
        container = client.containers.get('emby-virtual-lib')
        container.restart()
        flash("已成功触发 emby-virtual-lib 容器重启，新配置将在稍后生效。", "success")
        return True
    except docker.errors.NotFound:
        flash("重启失败：未找到名为 'emby-virtual-lib' 的容器。", "error")
    except docker.errors.DockerException as e:
        flash(f"重启时发生 Docker 错误: {e}", "error")
    except Exception as e:
        flash(f"触发重启时发生未知错误: {e}", "error")
    return False

def load_config():
    """加载YAML配置文件"""
    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            return yaml.load(f)
    except FileNotFoundError:
        return {
            'emby_server': '',
            'emby_api_key': '',
            'log_level': 'info',
            'hide': [],
            'library': []
        }
    except Exception as e:
        flash(f"加载配置文件时出错: {e}", "error")
        return {}


def save_config(config_data):
    """将Python字典保存为YAML文件"""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f)
    except Exception as e:
        flash(f"保存配置文件时出错: {e}", "error")
        return False
    return True


# --- Flask 路由处理 ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 1. 从表单收集所有原始数据
        form_data = {
            'emby_server': request.form.get('emby_server', '').strip(),
            'emby_api_key': request.form.get('emby_api_key', '').strip(),
            'log_level': request.form.get('log_level'),
            'hide': request.form.getlist('hide'),
            'library': []
        }
        
        lib_names = request.form.getlist('lib_name')
        # lib_resource_id 现在可能来自下拉选择框
        lib_resource_ids = request.form.getlist('lib_resource_id')
        lib_resource_types = request.form.getlist('lib_resource_type')
        lib_images = request.form.getlist('lib_image')

        is_image_missing = False
        for i in range(len(lib_names)):
            if lib_names[i]:
                image_path = lib_images[i].strip()
                if not image_path:
                    is_image_missing = True
                
                form_data['library'].append({
                    'name': lib_names[i],
                    'resource_id': lib_resource_ids[i],
                    'resource_type': lib_resource_types[i],
                    'image': image_path
                })
        
        # 2. 校验逻辑
        if is_image_missing and not form_data['emby_api_key']:
            flash('校验失败：当虚拟媒体库的“图片路径”为空时，“Emby API Key”为必填项。', 'error')
            # 校验失败时，也传入缓存数据，以保持下拉框状态
            return render_template('index.html', config=form_data, hide_options=HIDE_OPTIONS_MAP, resource_types=RESOURCE_TYPE_MAP, emby_data=EMBY_DATA_CACHE)

        # 3. 准备最终要保存的数据
        data_to_save = {}
        
        if form_data['emby_server']:
            data_to_save['emby_server'] = to_int_if_possible(form_data['emby_server'])

        data_to_save['log_level'] = form_data['log_level']

        if form_data['emby_api_key']:
            data_to_save['emby_api_key'] = to_int_if_possible(form_data['emby_api_key'])

        if form_data['hide']:
            data_to_save['hide'] = form_data['hide']
            
        final_libraries = []
        for lib in form_data['library']:
            lib_item = {
                'name': to_int_if_possible(lib['name']),
                'resource_id': to_int_if_possible(lib['resource_id']),
                'resource_type': lib['resource_type']
            }
            if lib['image']:
                lib_item['image'] = lib['image']
            
            final_libraries.append(lib_item)
        
        if final_libraries:
            data_to_save['library'] = final_libraries

        # 4. 保存文件并触发重启
        if save_config(data_to_save):
            flash("配置已成功保存！", "success")
            restart_emby_virtual_lib()

        return redirect(url_for('index'))

    # GET请求：加载并显示页面，并传入缓存数据
    config = load_config()
    config.setdefault('hide', [])
    config.setdefault('library', [])
    
    return render_template(
        'index.html', 
        config=config, 
        hide_options=HIDE_OPTIONS_MAP,
        resource_types=RESOURCE_TYPE_MAP,
        emby_data=EMBY_DATA_CACHE # 传入缓存数据
    )


# --- 新增：用于从 Emby 获取数据的 API 路由 ---
def _fetch_emby_items(base_url, api_key, endpoint, name_for_log):
    """辅助函数，用于请求 Emby API 并处理通用逻辑"""
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    
    headers = {'X-Emby-Token': api_key, 'Accept': 'application/json'}
    url = f"{base_url}/emby{endpoint}"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        if "Items" in data and data["Items"]:
            return [{'Id': item.get('Id'), 'Name': item.get('Name')} for item in data['Items']]
        return []
    except requests.exceptions.RequestException as e:
        flash(f"获取 {name_for_log} 时出错: {e}", "error")
    except Exception as e:
        flash(f"处理 {name_for_log} 数据时发生未知错误: {e}", "error")
    return None

@app.route('/api/fetch_emby_data', methods=['POST'])
def fetch_emby_data_api():
    """
    从 Emby 服务器获取所有需要的数据并进行缓存。
    """
    global EMBY_DATA_CACHE
    
    data = request.json
    server_url = data.get('emby_server')
    api_key = data.get('emby_api_key')

    if not server_url or not api_key:
        return jsonify({'error': '服务器地址和 API 密钥不能为空。'}), 400

    fetched_data = {}
    
    # 定义要获取的资源
    endpoints = {
        'collection': ('/Items?IncludeItemTypes=BoxSet&Recursive=true', '合集'),
        'genre': ('/Genres', '类型'),
        'tag': ('/Tags', '标签'),
        'studio': ('/Studios', '工作室')
    }

    success = True
    for key, (endpoint, name) in endpoints.items():
        items = _fetch_emby_items(server_url, api_key, endpoint, name)
        if items is not None:
            fetched_data[key] = items
        else:
            success = False # 标记有错误发生

    if success and any(fetched_data.values()):
        EMBY_DATA_CACHE = fetched_data # 更新缓存
        flash("已成功从 Emby 获取并缓存数据！", "success")
        return jsonify(EMBY_DATA_CACHE)
    elif success:
        flash("从 Emby 获取数据成功，但所有项目均为空。", "warn")
        return jsonify({})
    else:
        # 如果有错误，返回错误信息，但不清空旧缓存
        return jsonify({'error': '获取部分或全部数据失败，请检查上方的错误提示。'}), 500

# --- 启动入口 ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)