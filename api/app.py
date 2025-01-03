from gc import enable
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
from urllib.parse import quote, urlparse, unquote
import json
import re
import os
import sys
import subprocess
import tempfile
import shutil
import tempfile
from datetime import datetime, timedelta
config_expiry_time = None
config_file_path = ""

app = Flask(__name__, template_folder='../templates')
app.secret_key = 'sing-box'
data_json = {}
os.environ['TEMP_JSON_DATA'] = '{"subscribes":[{"url":"URL","tag":"tag_1","enabled":true,"emoji":1,"subgroup":"","prefix":"","User-Agent":"v2rayng"},{"url":"URL","tag":"tag_2","enabled":false,"emoji":0,"subgroup":"命名/named","prefix":"❤️","User-Agent":"clashmeta"}],"auto_set_outbounds_dns":{"proxy":"","direct":""},"save_config_path":"./config.json","auto_backup":false,"exclude_protocol":"ssr","config_template":"","Only-nodes":false}'
data_json['TEMP_JSON_DATA'] = '{"subscribes":[{"url":"URL","tag":"tag_1","enabled":true,"emoji":1,"subgroup":"","prefix":"","User-Agent":"v2rayng"},{"url":"URL","tag":"tag_2","enabled":false,"emoji":0,"subgroup":"命名/named","prefix":"❤️","User-Agent":"clashmeta"}],"auto_set_outbounds_dns":{"proxy":"","direct":""},"save_config_path":"./config.json","auto_backup":false,"exclude_protocol":"ssr","config_template":"","Only-nodes":false}'

TEMP_DIR = tempfile.gettempdir()

def cleanup_temp_config():
    global config_expiry_time, config_file_path
    if config_expiry_time and datetime.now() > config_expiry_time:
        shutil.rmtree(os.path.dirname(config_file_path), ignore_errors=True)
        config_expiry_time = None
        config_file_path = None

def get_temp_json_data():
    temp_json_data = os.environ.get('TEMP_JSON_DATA')
    if temp_json_data:
        return json.loads(temp_json_data)
    return {}

def get_template_list():
    template_list = []
    config_template_dir = 'config_template'
    template_files = os.listdir(config_template_dir)
    template_list = [os.path.splitext(file)[0] for file in template_files if file.endswith('.json')]
    template_list.sort()
    return template_list

def read_providers_json():
    temp_json_data = get_temp_json_data()
    if temp_json_data :
        return temp_json_data
    with open('providers.json', 'r', encoding='utf-8') as json_file:
        providers_data = json.load(json_file)
    return providers_data

def write_providers_json(data):
    temp_json_data = get_temp_json_data()
    if not temp_json_data:
        with open('providers.json', 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)

@app.route('/')
def index():
    template_list = get_template_list()
    template_options = [f"{index + 1}、{template}" for index, template in enumerate(template_list)]
    providers_data = read_providers_json()
    temp_json_data = get_temp_json_data()
    return render_template('index.html', template_options=template_options, providers_data=json.dumps(providers_data, indent=4, ensure_ascii=False), temp_json_data=json.dumps(temp_json_data, indent=4, ensure_ascii=False))

@app.route('/update_providers', methods=['POST'])
def update_providers():
    try:
        providers_data = request.form.get('providers_data', '')
        new_providers_data = json.loads(providers_data if providers_data else '{}')
        write_providers_json(new_providers_data)
        flash('Providers.json文件已更新', 'success')
        flash('File Providers.json đã được cập nhật', 'Thành công^^')
    except Exception as e:
        flash(f'更新Providers.json文件时出错；{str(e)}', 'error')
        flash(f'Có lỗi khi cập nhật file Providers.json; {str(e)}', 'Lỗi!!!')
    return redirect(url_for('index'))

@app.route('/edit_temp_json', methods=['GET', 'POST'])
def edit_temp_json():
    if request.method == 'POST':
        try:
            new_temp_json_data = request.form.get('temp_json_data')
            if new_temp_json_data:
                temp_json_data = json.loads(new_temp_json_data)
                os.environ['TEMP_JSON_DATA'] = json.dumps(temp_json_data, indent=4, ensure_ascii=False)
                return jsonify({'status': 'success'})
            return jsonify({'status': 'error', 'message': 'TEMP_JSON_DATA cannot be empty'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    return jsonify({'status': 'error', 'message': 'Invalid method'})  # Handle GET requests

@app.route('/config/<path:url>', methods=['GET'])
def config(url):
    encoded_url = unquote(url)
    file_pattern = r'&?file=([0-9]+|http://[^\s&]+|https://[^\s&]+)'
    file_match = re.search(file_pattern, encoded_url)
    if file_match:
        file = file_match.group(1)
        encoded_url = re.sub(file_pattern, '', encoded_url)

    temp_json_data = json.loads('{"subscribes":[],"auto_set_outbounds_dns":{"proxy":"","direct":""},"save_config_path":"./config.json","auto_backup":false,"exclude_protocol":"ssr","config_template":"","Only-nodes":false}')
  

    subs = encoded_url.split('||||')
    print(subs)

    for sub in subs:
        subscribe = {}

        param = urlparse(sub.split('&', 1)[-1])
        args_dict = dict(item.split('=') for item in param.path.split('&'))

        emoji_param = args_dict.get('emoji', '')
        file_param = args_dict.get('file', '')
        tag_param = args_dict.get('tag', '')
        ua_param = args_dict.get('ua', '')
        pre_param = args_dict.get('prefix', '')
        eps_param = args_dict.get('eps', '')
        enn_param = args_dict.get('enn', '')
        subgroup_param = args_dict.get('subgroup', '')
        enable_param = args_dict.get('enable', '')

        params_to_remove = [
            f'&prefix={pre_param}',
            f'&ua={ua_param}',
            f'&file={file_param}',
            f'&emoji={emoji_param}',
            f'&tag={tag_param}',
            f'&eps={eps_param}',
            f'&enn={enn_param}',
            f'&subgroup={subgroup_param}',
            f'&enable={enable_param}'
        ]
        sub_copy = sub
        for param in params_to_remove:
            sub_copy = sub_copy.replace(param, '')
        subscribe['url'] = sub_copy
        subscribe['emoji'] = 1 if len(emoji_param) == 0 else int(emoji_param)
        subscribe['enabled'] = True if len(enable_param) == 0 else enable_param.lower() == 'true'
        subscribe["tag"] = tag_param    
        subscribe['subgroup'] = subgroup_param
        subscribe['prefix'] = pre_param
        subscribe['ex-node-name'] = enn_param  # 设置节点名称
        subscribe['User-Agent'] = ua_param if ua_param else 'clashmeta'  # 设置UA
        temp_json_data['subscribes'].append(subscribe)

    # 设置全局配置参数
    temp_json_data['exclude_protocol'] = eps_param if eps_param else temp_json_data.get('exclude_protocol', '')
    temp_json_data['config_template'] = unquote(file_param) if file_param else temp_json_data.get('config_template', '')
    try:
        selected_template_index = '0'
        if file.isdigit():
            temp_json_data['config_template'] = ''
            selected_template_index = str(int(file) - 1)
        temp_json_data = json.dumps(json.dumps(temp_json_data, indent=4, ensure_ascii=False), indent=4, ensure_ascii=False)
        subprocess.check_call([sys.executable, 'main.py', '--template_index', selected_template_index, '--temp_json_data', temp_json_data])
        CONFIG_FILE_NAME = json.loads(os.environ['TEMP_JSON_DATA']).get("save_config_path", "config.json")
        if CONFIG_FILE_NAME.startswith("./"):
            CONFIG_FILE_NAME = CONFIG_FILE_NAME[2:]
        config_file_path = os.path.join('/tmp/', CONFIG_FILE_NAME) 
        if not os.path.exists(config_file_path):
            config_file_path = CONFIG_FILE_NAME
        os.environ['TEMP_JSON_DATA'] = json.dumps(json.loads(data_json['TEMP_JSON_DATA']), indent=4, ensure_ascii=False)
        with open(config_file_path, 'r', encoding='utf-8') as config_file:
            config_content = config_file.read()
            if config_content:
                flash('配置文件生成成功', 'success')
                flash('Tạo file cấu hình thành công', 'Thành công^^')
        config_data = json.loads(config_content)
        return Response(config_content, content_type='text/plain; charset=utf-8')
    except subprocess.CalledProcessError as e:
        os.environ['TEMP_JSON_DATA'] = json.dumps(json.loads(data_json['TEMP_JSON_DATA']), indent=4, ensure_ascii=False)
        return Response(json.dumps({'status': 'error'}, indent=4,ensure_ascii=False), content_type='application/json; charset=utf-8', status=500)
    except Exception as e:
        return Response(json.dumps({'status': 'error', 'message_CN': '认真看刚刚的网页说明、github写的reademe文件;', 'message_VN': 'Quá thời gian phân tích đăng ký: Vui lòng kiểm tra xem liên kết đăng ký có chính xác không hoặc vui lòng chuyển sang "nogroupstemplate" và thử lại; Vui lòng không chỉnh sửa giá trị "tag", trừ khi bạn hiểu nó làm gì;', 'message_EN': 'Subscription parsing timeout: Please check if the subscription link is correct or please change to "no_groups_template" and try again; Please do not modify the "tag" value unless you understand what it does;'}, indent=4,ensure_ascii=False), content_type='application/json; charset=utf-8', status=500)

@app.route('/generate_config', methods=['POST'])
def generate_config():
    try:
        selected_template_index = request.form.get('template_index')
        if not selected_template_index:
            flash('请选择一个配置模板', 'error')
            flash('Vui lòng chọn một mẫu cấu hình', 'Lỗi!!!')
            return redirect(url_for('index'))
        temp_json_data = json.dumps(os.environ['TEMP_JSON_DATA'], indent=4, ensure_ascii=False)
        subprocess.check_call([sys.executable, 'main.py', '--template_index', selected_template_index, '--temp_json_data', temp_json_data])
        CONFIG_FILE_NAME = json.loads(os.environ['TEMP_JSON_DATA']).get("save_config_path", "config.json")
        if CONFIG_FILE_NAME.startswith("./"):
            CONFIG_FILE_NAME = CONFIG_FILE_NAME[2:]
        config_file_path = os.path.join('/tmp/', CONFIG_FILE_NAME) 
        if not os.path.exists(config_file_path):
            config_file_path = CONFIG_FILE_NAME
        os.environ['TEMP_JSON_DATA'] = json.dumps(json.loads(data_json['TEMP_JSON_DATA']), indent=4, ensure_ascii=False)
        with open(config_file_path, 'r', encoding='utf-8') as config_file:
            config_content = config_file.read()
            if config_content:
                flash('配置文件生成成功', 'success')
                flash('Tạo file cấu hình thành công', 'Thành công^^')
        config_data = json.loads(config_content)
        return Response(config_content, content_type='text/plain; charset=utf-8')
    except subprocess.CalledProcessError as e:
        os.environ['TEMP_JSON_DATA'] = json.dumps(json.loads(data_json['TEMP_JSON_DATA']), indent=4, ensure_ascii=False)
        return Response(json.dumps({'status': 'error'}, indent=4,ensure_ascii=False), content_type='application/json; charset=utf-8', status=500)
    except Exception as e:
        return Response(json.dumps({'status': 'error', 'message_CN': '认真看刚刚的网页说明、github写的reademe文件;', 'message_VN': 'Quá thời gian phân tích đăng ký: Vui lòng kiểm tra xem liên kết đăng ký có chính xác không hoặc vui lòng chuyển sang "nogroupstemplate" và thử lại; Vui lòng không chỉnh sửa giá trị "tag", trừ khi bạn hiểu nó làm gì;', 'message_EN': 'Subscription parsing timeout: Please check if the subscription link is correct or please change to "no_groups_template" and try again; Please do not modify the "tag" value unless you understand what it does;'}, indent=4,ensure_ascii=False), content_type='application/json; charset=utf-8', status=500)

@app.route('/clear_temp_json_data', methods=['POST'])
def clear_temp_json_data():
    try:
        os.environ['TEMP_JSON_DATA'] = json.dumps({}, indent=4, ensure_ascii=False)
        flash('TEMP_JSON_DATA 已清空', 'success')
        flash('TEMP_JSON_DATA đã được làm trống', 'Thành công^^')
    except Exception as e:
        flash(f'清空 TEMP_JSON_DATA 时出错：{str(e)}', 'error')
        flash(f'Có lỗi khi làm trống TEMP_JSON_DATA: {str(e)}', 'Lỗi!!!')
    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
