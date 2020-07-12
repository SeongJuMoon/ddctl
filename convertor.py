import argparse
import yaml
import os
import json
import sys

DEBUG = os.environ.get('DEBUG')
TARGET = '.json'

# loader class로 빼야함
def file_read_by_encoding(filename, encoding):
    with open(filename, 'r', encoding=encoding) as f:
        return f.read()

def load_external_elements(filename, driver, encoding='UTF_8'):
    """
    외부의 있는 yaml과 json을 읽어서 처리할 수 있게하는 로더
    """
    source = file_read_by_encoding(filename, encoding)
    if len(source) <= 0:
        raise Exception('empty file')
    else:
        if driver.__name__ == 'yaml':
            return driver.load(source, Loader=yaml.BaseLoader)
        else:
            return driver.loads(source)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="tf input dir")
    parser.add_argument("-o", "--output", type=str, help="tf output dir")
    parser.add_argument("-c", "--config", type=str, help="convert config")
    args = parser.parse_args()

    if args.config is None or len(args.config) <= 0:
        print("please check your releationship config")
        sys.exit(255)

    # catch
    relation = load_external_elements(args.config, yaml)
    output_dir = args.output if args.output is not None else './output'
    
    try:
        for (prefix_path, _, filenames) in os.walk(args.input):
            if len(filenames) > 0: # 파일이 없으면 무시하고 넘김
                for filename in filenames:
                    name, ext = os.path.splitext(filename)
                    if ext == TARGET: # check has source_json
                        data_source = load_external_elements(f'{prefix_path}\{filename}', json)
                        result = render(relation, data_source)
                    
                    write_output_dir(output_dir, f'{name}.tf', result)
        print("Done convert!")
    except Exception as e:
        print(e)

    # print(result)

def write_output_dir(output_dir, filename, result):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    with open(f'{output_dir}/{filename}','w', encoding='UTF-8') as f:
        f.write(result)

def traveling(node, data_source):
    """
    """
    temp = ''
    for k, v in node.items():
        if not isinstance(v, dict):
            check = data_source.get(k)
            if check is not None:
                temp += f'\n{k} = {data_source[k]}'
        else:
            temp +=f'\n{k} = {{'

    if isinstance(v, dict):
        return temp + traveling(v, data_source[k]) + '\n}'
    else:
        return temp 

def mapping(metadata: list, data_source: dict):
    """
    list<renderItem>
    data_source <--> 
    """
    check_point = ''
    for item in metadata:
        if 'name' in item and 'format' in item: # is metadata?
            name = item.get('name')
            render_shape = item.get('format')
            if len(render_shape) == 0:
                try:
                    check_point += f'{name} = {string_wrapper(data_source[name])}\n'
                except KeyError as e:
                    pass
            else:
                traveling(render_shape, data_source)
        else:
            print('metadata is broken')
    return check_point

def string_wrapper(target):
    if isinstance(target ,str):
        return f'"{target}"'
    else:
        return target
        
def render(declare, data_source):
    resource = declare['resource']
    rendered = f"""resource {declare.get('resource').get('name')}.test {{""" + '\n'
    rendered += mapping(resource['required'], data_source)
    rendered += mapping(resource['optional'], data_source['options'])
    rendered += '}'

    return rendered

if __name__ == "__main__":
    main()