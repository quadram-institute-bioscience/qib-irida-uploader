#!/usr/bin/env python3
import pathlib
import click
import re
import iridauploader.config as _config
import iridauploader.core as core
from iridauploader.model import project
from iridauploader.parsers import supported_parsers
from iridauploader.parsers import directory
from iridauploader.model import Project
from iridauploader.core import api_handler
import logging
import datetime
import os, sys


@click.command()
@click.option('--pid', default=None, help='Project ID')
@click.option('--name', default=None, help='Project Name')
@click.option('--pe/--se', default=True, help='Paired-End reads?')
@click.option('--sort/--no-sort', default=False, help='Sort samples [Experiment]')
@click.option('--pattern', default='*_R1_001.fastq.gz', help='Path to fastq files')
@click.option('--config', default='config.conf', help='Path to IRIDA config file')
@click.argument('path', default=os.getcwd())
def prepare(path, pattern, pid, name, pe, sort, config):
    """
    Prepare for uploading a folder of fastq files to IRIDA \n
    - Create project on IRIDA given the user credentials \n
    - Generate a sample list inside the folder  
    """
    # :param sort: Sorting sample in numeric order
    # :param path: path to the folder of fastq files
    # :param pattern: pattern to scan, by default: *_R1_001.fastq.gz
    # :param pid: IRIDA project ID, you need to manually create in IRIDA control management
    # :param pe: Are the reads paired-end?
    # :return: A csv file SampleList.csv

    p = pathlib.Path(path)
    
    if pid is None:
        if name is None:
            run_date = re.search('[0-9]{6}(?=\_NB)', path)
            if run_date is not None:
                run_date = run_date.group()
            else:
            #     sys.exit("I could not find an expected folder name for IRIDA. Please name it manually")
            # if len(run_date) == 0:
                run_date = datetime.date.today().strftime("%y%m%d")
            project_name = f'QIB-{p.parts[-1].replace("_","-")}-{run_date}'
#	    logging.info(f"Project name is: {project_name}")
        else:
            project_name = name
        
        pid = create_project(name = project_name, config_file = config)
    if pe:
        regex = re.compile('_S[0-9]{1,3}|_R[12].')
    else:
        regex = re.compile(".fastq|.fq.")
    
    fastqs = p.rglob(pattern)
    fastq_names = [fq.name for fq in fastqs]
    _sorted_fastq_names = fastq_names
    # Sort sample
    if sort:
        _sorted_fastq_names = sorted(fastq_names, key=lambda s: int(regex.split(s)[0].split("_")[-1]))
    
    sample_ids = [regex.split(sp)[0] for sp in _sorted_fastq_names]
    sample_file = p.joinpath('SampleList.csv')
    # print(sorted(fastq_names, key=lambda s: int(regex.split(s)[0].split("_")[-1])))
    with sample_file.open(mode='w') as fh:
        fh.write('[Data]\n')
        fh.write("Sample_Name,Project_ID,File_Forward,File_Reverse\n")
        reverse_reads = ""
        for i in range(0, len(_sorted_fastq_names)):
            if pe:
                reverse_reads = _sorted_fastq_names[i].replace("_R1", "_R2")
            fh.write(f"{sample_ids[i]}, {pid}, {_sorted_fastq_names[i]}, {reverse_reads}\n")
    print("Finish!")

# @click.command()
# @click.option('--project_description', help='Project description')
# @click.option('--config_file', default='config.conf', help='Config file')
# @click.argument('name')
# @click.argument('path', default=os.getcwd())
def create_project(name, config_file, project_description = None):
    """
    Create a project
    argument:\n
        name: project name\n
        project_description: project description\n
        config_file: IRIDA config file\n
    return project id
    """
    _config.set_config_file(config_file)
    _config.setup()
    if project_description is None:
        project_description = f"Created on {datetime.date.today()} by BOT"
    try:
        _api = api_handler.initialize_api_from_config()
        projects_list = _api.get_projects()
        existed_project = [prj.id for prj in projects_list if prj.name==name]
        if len(existed_project) == 0:
            new_project = Project(name, project_description)
            created_project = _api.send_project(new_project)
            logging.info(f"Created project {name} - {created_project['resource']['identifier']}")
            project_id = created_project['resource']['identifier']
            return(project_id)
        else:
            logging.warning(f"Project(s) {name} is existed")
            logging.info(existed_project)
            return(existed_project[0])
    except Exception as e:
        raise(e)


def _upload(run_directory, force_upload, upload_assemblies):
    """
    start upload on a single run directory
    :param run_directory:
    :param force_upload:
    :param upload_assemblies
    :return: exit code 0 or 1
    """
    return core.cli_entry.upload_run_single_entry(run_directory, force_upload, upload_assemblies).exit_code


def _upload_batch(batch_directory, force_upload, upload_assemblies):
    """
    Start uploading runs in the batch directory
    :param batch_directory:
    :param force_upload:
    :param upload_assemblies
    :return: exit code 0 or 1
    """
    return core.cli_entry.batch_upload_single_entry(batch_directory, force_upload, upload_assemblies).exit_code

@click.command()
@click.option('--force-upload', 'force_upload', is_flag=True, default=False, help="Force upload")
@click.option('--assemblies', 'upload_assemblies', is_flag=True, default=False, help="Upload assemblies")
@click.option('--config', default='config.conf', help='Path to IRIDA config file')
@click.argument('directory', default=os.getcwd())
def upload(directory, force_upload, upload_assemblies, config):
    """
    Upload a run folder to IRIDA
    """
    if not os.access(directory, os.W_OK):  # Cannot access upload directory
        print("ERROR! Specified directory is not writable: {}".format(directory))
        sys.exit(1)
    logging.info(f'Current directory: {directory}')
    _config.set_config_file(config)
    _config.setup()
    _upload(directory, force_upload,upload_assemblies)

@click.group()
def irida():
    pass

irida.add_command(prepare)
irida.add_command(upload)

if __name__ == '__main__':
    irida()
    # create_project()

