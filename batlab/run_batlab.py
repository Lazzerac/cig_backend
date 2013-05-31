#!/usr/bin/env python

from __future__ import print_function
import sys
sys.path.append("..")
from cig_codes import code_db

import tempfile
import shutil
import subprocess

# The base directory where build scripts, support files, etc are located
BASE_DIR="/home/eheien/cig_backend/batlab"
# Email address to use for notifications
NOTIFY_EMAIL="emheien@geodynamics.org"

# Create a test setup and submit to BaTLab for the specified revision of the specifiec code
def test_code(cig_code, revision):
    use_repo = True

    tmp_dir = tempfile.mkdtemp()

    # Create the input source specification
    src_input_file_name = tmp_dir+"/source_input_desc"
    src_input_desc = open(src_input_file_name, 'w')
    if use_repo:
        if code_db.repo_type[cig_code] is "svn":
            print("method = svn", file=src_input_desc)
            code_url = code_db.repo_url[cig_code]
            if revision: code_url += " -r "+revision
            print("url =", code_url, cig_code, file=src_input_desc)
        elif code_db.repo_type[cig_code] is "hg":
            print("method = hg", file=src_input_desc)
            code_url = code_db.repo_url[cig_code]
            if revision: code_url += "#"+revision
            print("url =", code_url, file=src_input_desc)
            print("path =", cig_code, file=src_input_desc)
        elif code_db.repo_type[cig_code] is "git":
            print("method = git", file=src_input_desc)
            print("git_repo =", code_db.repo_url[cig_code], file=src_input_desc)
            # TODO: specify revision for Git
        else:
            print("Error: unknown repository type", code_db.repo_type[cig_code])
            exit(1)
        print(file=src_input_desc)
    else:
        print("method = url", file=src_input_desc)
        print("url =", code_db.release_src[cig_code], file=src_input_desc)
        print("untar = true", file=src_input_desc)
        print(file=src_input_desc)
    src_input_desc.close()

    # Create the support library input specifications
    for i, support_file in enumerate(code_db.batlab_support_libs[cig_code]):
        support_lib_input_file_name = tmp_dir+"/"+support_file+".scp"
        support_lib_desc = open(support_lib_input_file_name, 'w')
        print("method = scp", file=support_lib_desc)
        if code_db.support_libs[support_file][0] != "":
            tarball_file = BASE_DIR+"/support/"+code_db.support_libs[support_file][0]
        else:
            tarball_file = ""
        if code_db.support_libs[support_file][1] != "":
            build_script_file = BASE_DIR+"/support/"+code_db.support_libs[support_file][1]
        else:
            build_script_file = ""
        print("scp_file =", build_script_file, tarball_file, file=support_lib_desc)
        print("untar = true", file=support_lib_desc)
        support_lib_desc.close()

    # Create the input build files specification
    build_input_file_name = tmp_dir+"/build_input_desc"
    build_input_desc = open(build_input_file_name, 'w')
    print("method = scp", file=build_input_desc)
    local_build_files = BASE_DIR+"/"+cig_code+"/build.sh"
    for extra_file in code_db.batlab_extra_files[cig_code]:
        local_build_files += " "+BASE_DIR+"/"+cig_code+"/"+extra_file
    print("scp_file =", local_build_files, file=build_input_desc)
    build_input_desc.close()

    # Create the run specification
    run_spec_file_name = tmp_dir+"/run_spec"
    run_spec = open(run_spec_file_name, 'w')
    print("project = CIG", file=run_spec)
    print("component =", cig_code, file=run_spec)
    print("component_version =", revision, file=run_spec)
    if use_repo:
        if revision:
            print("description = Build", code_db.repo_type[cig_code], "revision", revision, file=run_spec)
        else:
            print("description = Build", code_db.repo_type[cig_code], "latest revision", file=run_spec)
    else:
        print("description = Build", code_db.repo_type[cig_code], " release", file=run_spec)
    print("run_type = build", file=run_spec)
    print("platform_job_timeout = 30", file=run_spec)

    # Get the list of support libraries needed as input for this code
    input_support_files = BASE_DIR+"/support/lib_scripts.scp"
    for i, support_file in enumerate(code_db.batlab_support_libs[cig_code]):
        input_support_files += ", "+tmp_dir+"/"+support_file+".scp"

    print("inputs =", src_input_file_name, ",", build_input_file_name, ",", input_support_files, file=run_spec)
    print(file=run_spec)

    # Get the list of support library compilation scripts needed
    input_support_scripts = ""
    for i, support_script in enumerate(code_db.support_lib_scripts(cig_code)):
        input_support_scripts += support_script+" "

    print("remote_pre = build_support.sh", file=run_spec)
    print("remote_pre_args =", input_support_scripts, file=run_spec)
    print(file=run_spec)

    # To build the code, use the build.sh script
    print("remote_task = build.sh", file=run_spec)
    if use_repo:
        print("remote_task_args = repo", file=run_spec)
    else:
        print("remote_task_args = dist", file=run_spec)
    print(file=run_spec)

    platform_list = ""
    for i, platform in enumerate(code_db.batlab_platforms[cig_code]):
        if i is not 0: platform_list += ", "
        platform_list += platform

    print("platforms =", platform_list, file=run_spec)
    print("notify =", NOTIFY_EMAIL, file=run_spec)

    run_spec.close()

    # Submit the generated run specification
    subprocess.call(["nmi_submit", run_spec_file_name])

    # Once it's in the system, wipe everything we just created
    shutil.rmtree(tmp_dir)

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("syntax:", sys.argv[0], "<code_name> [revision]")
        exit(1)

    cig_code = sys.argv[1]
    if len(sys.argv) > 2: revision = sys.argv[2]
    else: revision = None

    if cig_code is "all": code_list = code_db.codes()
    else: code_list = [cig_code]

    for check_code in code_list:
        if check_code not in code_db.codes():
            print("unknown code:", check_code)
            exit(1)

        test_code(check_code, revision)

if __name__ == "__main__":
    main()

