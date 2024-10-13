import subprocess
import os
import sys
import tempfile
import yaml

def create_dockerfile(temp_dir):
    dockerfile_content = """
FROM ubuntu:18.04

USER root

# 更新软件包索引并安装必要的工具
RUN apt-get update && \\
    apt-get install -y apt-utils python3 python3-pip wget

# 安装 Python 依赖
RUN pip3 install --upgrade pip

# 设置工作目录
WORKDIR /app

# 复制 Python 脚本和启动脚本
# COPY download_debs.py /app/download_debs.py
# COPY run.sh /app/run.sh

# 设置启动脚本为可执行
# RUN chmod +x /app/run.sh

# 指定默认命令
CMD ["/app/run.sh"]
"""
    with open(os.path.join(temp_dir, 'Dockerfile'), 'w') as f:
        f.write(dockerfile_content)

def create_run_script(temp_dir):
    run_script_content = """#!/bin/bash

# 检查参数数量
if [ "$#" -lt 2 ]; then
    echo "Usage: /app/run.sh <output_dir> <package1> <package2> ..."
    exit 1
fi

# 更新软件包索引
apt-get update

# 调用 Python 脚本
python3 /app/mount_scripts/download_debs.py "$@"
"""
    with open(os.path.join(temp_dir, 'run.sh'), 'w') as f:
        f.write(run_script_content)
    os.chmod(os.path.join(temp_dir, 'run.sh'), 0o755)

def create_container_script(temp_dir):
    container_script_content = """#!/usr/bin/env python3

import subprocess
import os
import sys

def get_dependencies(package_name):
    result = subprocess.run(
        ['apt-cache', 'depends', '--recurse', '--no-recommends', '--no-suggests', '--no-conflicts', '--no-breaks', '--no-replaces', '--no-enhances', package_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    if result.returncode != 0:
        print(f"Error getting dependencies for {package_name}: {result.stderr}")
        return []
    dependencies = result.stdout.splitlines()
    print(f"Get dependencies for {package_name}, output: {dependencies}")
    dependencies = [dep.strip() for dep in dependencies if dep.strip().startswith('Depends:')]
    print(f"dependencies1: {dependencies}")
    dependencies = [dep.split()[1] for dep in dependencies]
    print(f"dependencies2: {dependencies}")
    # remove repeated packages
    dependencies = list(set(dependencies))
    dependencies = [dep for dep in dependencies if not dep.strip().startswith('<')]
    return dependencies

def download_packages(packages, output_dir):
    os.system("ls")
    os.chdir(output_dir)
    for package in packages:
        subprocess.run(['apt', 'download', package], check=True)

def generate_install_script(packages, output_dir):
    with open(os.path.join(output_dir, 'install.sh'), 'w') as f:
        f.write('#!/bin/bash\\n')
        for package in packages:
            f.write(f'dpkg -i {package}.deb\\n')
    os.chmod(os.path.join(output_dir, 'install.sh'), 0o755)

def main():
    print("Enter Container Script")
    if len(sys.argv) < 3:
        print("Usage: python3 download_debs.py <output_dir> <package1> <package2> ...")
        sys.exit(1)

    import os, pwd

    os.setuid(0)
    os.setgid(0)

    output_dir = "/app/output"
    os.chdir(output_dir)
    
    packages = sys.argv[2:]
    print("Packages to download:", packages)

    # if not os.path.exists(output_dir):
    try:
        print(f"Output directory does not exist, creating... {output_dir}")
        os.makedirs(output_dir)
    except:
        pass

    all_packages = set()
    for package in packages:
        dependencies = get_dependencies(package)
        print(f"Getting dependencies for {package} with {dependencies}")
        all_packages.update(dependencies)
        all_packages.add(package)

    all_packages = sorted(all_packages)
    download_packages(all_packages, output_dir)
    generate_install_script(all_packages, output_dir)

if __name__ == "__main__":
    main()
"""
    with open(os.path.join(temp_dir, 'download_debs.py'), 'w') as f:
        f.write(container_script_content)

def build_and_run_docker(output_dir, packages):
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建 Dockerfile
        create_dockerfile(temp_dir)
        
        # 创建 run.sh
        create_run_script(temp_dir)
        
        # 创建容器中的 Python 脚本
        create_container_script(temp_dir)
        
        # 构建 Docker 镜像
        image_tag = 'download-debs:18.04'
        subprocess.run(['docker', 'build', '-t', image_tag, temp_dir], check=True)
        
        # 运行 Docker 容器
        print(f"bind output dir: {os.path.abspath(output_dir)} to /app/output")
        command = ['docker', 'run', 
                    '-v', f'{os.path.abspath(output_dir)}:/app/output',
                    '-v', f'{temp_dir}:/app/mount_scripts',
                    '--entrypoint=/app/mount_scripts/run.sh',
                    image_tag, '/app/output'] + packages
        subprocess.run(command, check=True)

def deb_one_pack(packname,sub_packs):
    # if len(sys.argv) < 3:
    #     print("Usage: python3 download_debs.py <package1> <package2> ...")
    #     sys.exit(1)

    output_dir = "releases/"+packname
    # packages = sys.argv[2:]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    os.system(f"chmod 777 {output_dir}")

    build_and_run_docker(output_dir, sub_packs)

def main():
    os.system("docker login")
    ymls=[f for f in os.listdir("./") if f.endswith(".yml")]
    for yml in ymls:
        with open(yml) as f:
            conf=yaml.safe_load(f)
        for key in conf:
            if key=='apt':
                deb_one_pack(yml.split(".yml")[0],conf['apt'])
            else:
                print("unsupported conf key: {key}")


if __name__ == "__main__":
    main()