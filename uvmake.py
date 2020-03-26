import os, sys
import re
import logging
import traceback
from os import path
from lxml import etree as et # so painful to type 'etree'
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter(fmt=r'[%(levelname)s][%(filename)s:%(lineno)d] %(message)s'))
logger.addHandler(_handler)
logger.setLevel(logging.INFO)

yaml = YAML(typ='rt')
yaml.default_flow_style = False
yaml.indent = 4

# config for generating uVision project files.
config = {}

args = None

version = '0.1' # my version

def shell_interface():
    import argparse
    parser = argparse.ArgumentParser(
        description='Configure tool for Keil uVsion C51 projects (for Keil C51 version 5)',
        usage='''
        %(prog)s  <path-to-config-file>       [options]
        '''
    )
    parser.add_argument(
        'config_file',
        help='path of config file, defaults to `uvmake.yaml` in current directory',
        #type=argparse.FileType(mode='r', encoding='UTF-8'),
        nargs='?',
        default='./uvmake.yaml',
        metavar='<path-to-config-file>'
        )
    parser.add_argument(
        '-t', '--config-template',
        help='generate config template file (file name is taken from option `<path-to-config-file>`). existing file will be overwritten.',
        action='store_true'
        )
    parser.add_argument(
        '-r', '--reverse-config',
        help='update the config file according to project files. if config file doesn\'t already exist, it is generated from template (see option `-t`) first',
        action='store_true'
        )
    parser.add_argument(
        '-u', '--update-config',
        help='same as option `-r`',
        action='store_true'
        )
    parser.add_argument(
        '-K', '--no-backup',
        help='do not backup project files before making changes.',
        action='store_true'
        )
    parser.add_argument(
        '-d', '--debug',
        help='run with debug output',
        action='store_true'
        )
    parser.add_argument(
        '-v', '--version',
        help='show version information',
        action='version',
        version='%(prog)s (version {}) by Cangyin 1522645226@qq.com'.format(version)
        )
    pro_group = parser.add_argument_group('project specific arguments')
    pro_group.add_argument(
        '-S', '--source',
        help='directories where your C51 source files are, in addition to the value from `uvmake.yaml`',
        nargs='+'
        )
    pro_group.add_argument(
        '-I', '--include',
        help='path for header files (.h files), in addition to the value from `uvmake.yaml`',
        nargs='+'
        )
    pro_group.add_argument(
        '-D', '--project-dir',
        help='directory for orginal and generated C51 project files. Overrides the value from `uvmake.yaml`',
        )
    pro_group.add_argument(
        '-P', '--project-name',
        help='name of the project files. Overrides the value from `uvmake.yaml`',
        )
    pro_group.add_argument(
        '-N', '--target-name',
        help='target name of the project',
        )
    pro_group.add_argument(
        '-O', '--output-dir',
        help='output directory for object files of the project. Overrides the value from `uvmake.yaml`',
        )
    pro_group.add_argument(
        '-o', '--output-name',
        help='output object file filename of the project. Overrides the value from `uvmake.yaml`',
        )
    pro_group.add_argument(
        '-F', '--clock-freq',
        help='clock frequency of MCU used in project',
        )
    return parser.parse_args()

def _unindent(s :str, n :int):
    #s = re.sub('^{' + int(n) = '}', '', s, flags=re.MULTILINE) # \s=[ \t\n\r\f\v], not suitable here.
    s = re.sub('^' + ' '*n, '', s, flags=re.MULTILINE)
    return s

def read_config(config_file :str):
    config = yaml.load(config_file, Loader=yaml.Loader)
    return config

def get_config_template():
    _config_yaml = r'''
        #
        # Config file for Keil C51 projects.
        #
        # Now you can change some values here depending on
        # your need, and finally run `uvmake.py <THIS-FILE-NAME>`
        # in current directory to configure the project.
        # 

        ProjectDirectory: .\Keil51 Project Directory\
        ProjectName: project-name

        ## Directories to explore for source and header files
        SourceDirectories:
        - C:\source\dir\a
        - C:\source\dir\b\
        - C:\source\dir\b\c

        ## Individual source files
        SourceFiles:
        - C:\file1.h
        - C:\file2.c

        ProjectOptions:
            ## Options for Keil uVision C51 project.

            #  note: paths here are relative to `ProjectDirectory`
            TargetName: target-name
            OutputName: output-name
            OutputDirectory: .\Objects\
            
            # create .obj file or .lib file
            CreateExecutableOrLib: exe # 'exe' or 'lib'
            # create .hex file
            CreateHexFile: True

            # paths for header files found in `SourceDirectories`
            # will be automatically added.
            IncludePaths:
            - C:\include\path1
            - C:\include\path2

        UVisionOptions:
            ClockFrequency: 11059200
            remove_breakpoints: True  # 'True' or 'False'

        uvmake:
            ## Config for uvmake.py

            # grouping method for source files.
            # NONE:
            #   source files are grouped as header
            #   files(.h) or C files (.c).
            # C_BY_FOLDER:
            #   C files are grouped according to the
            #   folder they're in. header files are all
            #   in one group.
            # ALL_BY_FOLDER
            #   files are grouped according to the folder
            #   they're in, regardless of file type.
            file_grouping_method: NONE    # 'NONE', 'C_BY_FOLDER' or 'ALL_BY_FOLDER'
            header_group_name: Header Files   # for 'NONE' and 'C_BY_FOLDER'
            c_group_name: Source Files        # for 'NONE' only

            header_extensions:
            - .h
            - .hpp

            c_extensions:
            - .c
            - .cpp

            # exclude some files if its full path
            # contains any keyword specified here.
            exclude_keywords:
            - .vscode

            # maximum directory tree level to traverse for
            # source files, relative to starting paths.
            # 0 indicates that subdirectories are ignored. 
            max_dir_tree_level: 1
    '''
    _config_yaml = _unindent(_config_yaml, 8)
    return yaml.load(_config_yaml)

def _dump_config(_config, filepath):
    with open(filepath, 'w', encoding='UTF-8') as f:
        yaml.dump(_config, stream=f)

def make_config_template_file():
    _dump_config(get_config_template(), args.config_file)
    logger.info('Generated template config file: {}'.format(args.config_file))

def load_config():
    logger.debug('Loading config from file: {}'.format(args.config_file))
    global config
    try:
        config = yaml.load(open(args.config_file))
    except:
        logger.error('Error: cannot load the config file "{}"'.format(args.config_file))
        sys.exit(-1)
    logger.debug('Config loaded successfully')
    #yaml.dump(config, stream=sys.stdout)

    logger.debug('Checking for config keys...')

    def __check_key(d :dict, k):
        _errmsg = _unindent('''\
            Missing config item "{}", in file: "{}"

            Use command line option `-t` to get a template config file
            in case you don't know what the missing item is for.
            ''', 12)
        logger.debug('checking config key: {}'.format(k))
        if not k in d.keys():
            logger.error(_errmsg.format(k, args.config_file))
            sys.exit(-1)

    def __check_config(_config :dict, _template :dict):
        if isinstance(_template, dict):
            for key in _template:
                __check_key(_config, key)
                # uncomment this line for recursive and more conmprehensive check.
                # __check_config(_config[key], _template[key]) 
        else: # scalars. e.g. str, int, boolean 
            return

    __check_config(config, get_config_template())
    logger.debug('Check done.')

def merge_args(args):
    '''
        merge options in args into config
    '''
    if args.source:
        _source_dirs = [d for d in args.source if _verify_path(d)]
        config['SourceDirectories'].extend(_source_dirs)
    if args.include:
        _include_dirs = [d for d in args.include if _verify_path(d)]
        config['ProjectOptions']['IncludePath'] += ';'+';'.join(_include_dirs)
    if _verify_path(args.project_dir):
        config['ProjectDirectory'] = args.project_dir
    if _verify_path(args.output_dir):
        config['ProjectOptions']['OutputDirectory'] = args.output_dir

    def _simple_set(d, name, value):
        if value:
            d[name] = value

    _simple_set(config, 'ProjectName', args.project_name)
    _simple_set(config['ProjectOptions'], 'TargetName', args.target_name)
    _simple_set(config['ProjectOptions'], 'OutputName', args.output_name)
    _simple_set(config['UVisionOptions'], 'ClockFrequency', args.clock_freq)

def _verify_path(p):
    if not p: return False
    if path.exists(p):
        return True
    else:
        logger.warning('Invalid path "{}", ignored!'.format(p))
        return False

def _write_file(xml_doc, filepath, backup=True):
    from shutil import copy
    if not path.exists(filepath):
        logger.error('File path invalid!')
        return
    if backup:
        backup_name = filepath + '.backup'
        if path.exists(backup_name):
            logger.error('Backup file already exists: "{}", Cancelling...'.format(backup_name))
            return
        logger.info('Creating backup file for: ' + filepath)
        copy(filepath, backup_name)
    logger.info('Updating file: {} ...'.format(filepath))
    with open(filepath, 'wb') as f:
        et.indent(xml_doc)
        docinfo = xml_doc.docinfo
        xml_doc.write(f, encoding=docinfo.encoding, method="xml", xml_declaration=True, standalone=docinfo.standalone)
    logger.info('  Update completed.')

def _parse_xml_doc(xml_file):
    def __patch_xml(doc):
        # prevent creation of self-closing tags
        for node in doc.xpath('//*[not(text())]'):
            node.text = ''
            
    logger.info('Parsing project XML file: ' + xml_file)
    try:
        doc = et.parse(xml_file)
        __patch_xml(doc)
    except Exception as e:
        logger.error('XML parsing failed!')
        raise
    logger.info('  Parsing completed.')
    return doc

def _resolve_project_related_options(root):
    _opts = dict()

    def __has_value(name):
        return _opts.get(name) is not None

    def __set_val(xp, value):
        root.xpath(xp)[0].text = str(value)

    try:
        _opts = config['ProjectOptions']
        _base = '/Project/Targets/Target/'

        if __has_value('TargetName'):
            __set_val(_base + 'TargetName', _opts['TargetName'])
        
        if __has_value('IncludePaths') :
            if not isinstance(_opts['IncludePaths'], list) :
                logger.warning('the type of `IncludePaths` should be a list, got {}'.format(type(_opts['IncludePaths'])))
            else:
                __set_val(_base + 'TargetOption/Target51/C51/VariousControls/IncludePath', ';'.join(_opts['IncludePaths']))

        if __has_value('OutputName'):
            __set_val(_base + 'TargetOption/TargetCommonOption/OutputName', _opts['OutputName'])
        
        if __has_value('OutputDirectory'):
            __set_val(_base + 'TargetOption/TargetCommonOption/OutputDirectory', path.join('.\\', path.normpath(_opts['OutputDirectory']) + '\\'))
        
        if __has_value('CreateExecutableOrLib'):
            if _opts['CreateExecutableOrLib'] == 'lib':
                __set_val(_base + 'TargetOption/TargetCommonOption/CreateExecutable', 0)
                __set_val(_base + 'TargetOption/TargetCommonOption/CreateLib', 1)
            elif _opts['CreateExecutableOrLib'] == 'exe':
                __set_val(_base + 'TargetOption/TargetCommonOption/CreateExecutable', 1)
                __set_val(_base + 'TargetOption/TargetCommonOption/CreateLib', 0)
            else:
                logger.warning('Invalid value for `CreateExecutableOrLib`: {}'.format(_opts['CreateExecutableOrLib']))

        if __has_value('CreateHexFile'):
            __set_val(_base + 'TargetOption/TargetCommonOption/CreateHexFile', '1' if _opts['CreateHexFile'] else '0')
    except:
        logger.error('Failed on resolving related options in project file!')
        raise

def _resolve_uvopt_related_options(root):

    def __set_val(xp, value):
        root.xpath(xp)[0].text = value

    try:
        if config['ProjectOptions'].get('TargetName') is not None:
            __set_val('/ProjectOpt/Target/TargetName', config['ProjectOptions']['TargetName'])

        _opts =  config['UVisionOptions']
        if _opts.get('ClockFrequency') is not None:
            __set_val('/ProjectOpt/Target/TargetOption/CLK51', str(_opts['ClockFrequency']))
        if _opts.get('remove_breakpoints') == True:
            _node = root.xpath('/ProjectOpt/Target/TargetOption')[0]
            if _node.xpath('Breakpoint'):
                _node.remove(_node.xpath('Breakpoint')[0])
    except:
        logger.error('Failed on resolving related options in uVision option file!')
        raise

def _get_uvfile_type(file_name :str):
    uvfile_types = {
            '.c': 1,
            '.s*': 2, '.src': 2, '.a*': 2,
            '.obj': 3, '.o': 3,
            '.lib': 4,
            '.txt': 5, '.h': 5, '.inc': 5,
            '.plm': 6,
            '.cpp': 7,
            '.*': 8
    }
    for ext in uvfile_types:
        if('*' in ext): # use regular expression
            extpattern = ext.replace('*', '.*').replace('.', '\.') + '$'
            extpattern = re.compile(extpattern)
            if extpattern.search(file_name):
                return uvfile_types[ext]
        else:
            if file_name.endswith(ext):
                return uvfile_types[ext]

def _create_SubElement(parent, tag, attrib={}, text=None, nsmap=None, **_extra):
    result = et.SubElement(parent, tag, attrib, nsmap, **_extra)
    result.text = text
    return result
 
def make_project_xml_groups(file_groups :dict) -> et._Element:
    groups = et.Element('Groups')

    def _make_xml_group_node(group_name :str, filepaths :list):
        group = et.Element('Group')
        _create_SubElement(group, 'GroupName', text=group_name)
        files_node = _create_SubElement(group, 'Files')
        for f in filepaths:
            file_node = _create_SubElement(files_node, 'File')
            file_name = path.split(f)[1]
            _create_SubElement(file_node, 'FileName', text=file_name)
            _create_SubElement(file_node, 'FileType', text=str(_get_uvfile_type(file_name)))
            _create_SubElement(file_node, 'FilePath', text=f)
        return group

    for group_name in file_groups:
        group = _make_xml_group_node(group_name, file_groups[group_name])
        groups.append(group)

    return groups

def make_uvoption_xml_groups(file_groups :dict) -> list:
    groups = []

    def _make_xml_group_node(group_name :str, group_number :int, filepaths :list):
        group = et.Element('Group')
        _create_SubElement(group, 'GroupName', text='0')
        _create_SubElement(group, 'tvExp', text='0')
        _create_SubElement(group, 'tvExpOptDlg', text='0')
        _create_SubElement(group, 'cbSel', text='0')
        _create_SubElement(group, 'RteFlg', text='0')
        for i in range(len(filepaths)):
            f = filepaths[i]
            file_node = _create_SubElement(group, 'File')
            _create_SubElement(file_node, 'GroupNumber', text=str(group_number))
            _create_SubElement(file_node, 'FileNumber', text=str(i+1))
            file_name = path.split(f)[1]
            _create_SubElement(file_node, 'FileType', text=str(_get_uvfile_type(file_name)))
            _create_SubElement(file_node, 'tvExp', text='0')
            _create_SubElement(file_node, 'tvExpOptDlg', text='0')
            _create_SubElement(file_node, 'bDave2', text='0')
            _create_SubElement(file_node, 'PathWithFileName', text=f)
            _create_SubElement(file_node, 'FilenameWithoutPath', text=file_name)
            _create_SubElement(file_node, 'RteFlg', text='0')
            _create_SubElement(file_node, 'bShared', text='0')
        return group

    i = 1
    for group_name in file_groups:
        group = _make_xml_group_node(group_name, i, file_groups[group_name])
        groups.append(group)
        i += 1 

    return groups

def make_project_file(template_pro_file, file_groups :dict, backup=True):
    if not path.exists(template_pro_file):
        logger.error('Project file "{}" not found!'.format(template_pro_file))
        raise
    doc = _parse_xml_doc(template_pro_file)
    root = doc.getroot()

    new_groups = make_project_xml_groups(file_groups)
    _node = root.xpath('/Project/Targets/Target')[0]
    _node.replace(_node.xpath('Groups')[0], new_groups)

    _resolve_project_related_options(root)
    
    _write_file(doc, template_pro_file, backup=backup)

def make_uv_option_file(template_uvopt_file, file_groups :dict, backup=True):
    if not path.exists(template_uvopt_file):
        logger.error('Project file "{}" not found!'.format(template_uvopt_file))
        raise
    doc = _parse_xml_doc(template_uvopt_file)
    root = doc.getroot()

    for g in root.xpath('/ProjectOpt/Group'):
        root.remove(g)

    for g in make_uvoption_xml_groups(file_groups):
        root.xpath('/ProjectOpt')[0].append(g)
    
    _resolve_uvopt_related_options(root)

    _write_file(doc, template_uvopt_file, backup=backup)

def make_project(project_dir :str, project_name :str, file_groups :dict, backup=True):
    from copy import deepcopy
    _file_groups = deepcopy(file_groups)
    # make file path in `_file_groups` relative to `project_dir`
    for g in _file_groups:
        _file_groups[g] = \
            sorted( # sort by filename
                [path.relpath(f, start=project_dir) for f in _file_groups[g]],
                key=path.basename
                )
    
    logger.info('Entering project directory: ' + project_dir)
    old_dir = os.getcwd()
    os.chdir(project_dir)

    try:
        make_project_file(
            template_pro_file=project_name + '.uvproj',
            file_groups = _file_groups,
            backup=backup
            )
        make_uv_option_file(
            template_uvopt_file=project_name + '.uvopt',
            file_groups = _file_groups,
            backup=backup
            )
    except Exception as e:
        logger.error('Error occurred, cancelling...')
        logger.debug(traceback.format_exc())
        sys.exit(-1)
    
    logger.info('Leaving project directory:  ' + project_dir)
    os.chdir(old_dir)

def reverse_config():
    project_dir = config['ProjectDirectory']
    if not path.exists(project_dir):
        logger.error('Project directory not exist: "{}", please check your config file or command line option (option `-D`)'.format(project_dir))
        sys.exit(-1)

    old_dir = os.getcwd()
    os.chdir(project_dir)

    project_name = config['ProjectName']
    if (not project_name) or \
        (not path.exists(project_name + '.uvproj')) or \
        (not path.exists(project_name + '.uvopt')):

        logger.error('Project files: "{}.uvproj" or "{}.uvopt" not exist'.format(project_name, project_name))
        logger.info('Trying to find project files (*.uvproj and *.uvopt) in directory "{}"'.format(project_dir))
        
        uvproj = [f for f in os.listdir('./') if f.endswith('.uvproj')]
        uvopt = [f for f in os.listdir('./') if f.endswith('.uvopt')]

        if not (len(uvproj) == 1 and len(uvopt)==1):
            logger.error('Multiple project files found: ' + '\n  ' + '\n  '.join(uvproj + uvopt))
            logger.info('Exit.')
            sys.exit(-1)
            
        uvproj = uvproj[0].split('.', maxsplit=1)[0]
        uvopt  = uvopt[0].split('.', maxsplit=1)[0]
        if not uvproj == uvproj:
            logger.error('Multiple project files found: ' + '\n  ' + '\n  '.join(uvproj + uvopt))
            logger.info('Exit.')
            sys.exit(-1)

        logger.info('Found project files: "{}.uvproj" and "{}.uvopt"'.format(project_name, project_name))
        project_name = uvproj
        config['ProjectName'] = uvproj

    root = _parse_xml_doc(project_name + '.uvproj').getroot()

    def __get(xp):
        return root.xpath(xp)[0].text

    # 1
    config['SourceDirectories'] = []

    # gather files in project
    _files = [_node.text for _node in root.xpath('/Project/Targets/Target/Groups//File/FilePath')]
    # convert to absolute path
    _files = [path.abspath(f) for f in _files]
    logger.debug('Files in project:' + '\n  ' + '\n  '.join(_files))
    # 2
    config['SourceFiles'] = _files
    # 3
    config['ProjectOptions']['TargetName'] = __get('/Project/Targets/Target/TargetName')

    _base = '/Project/Targets/Target/TargetOption/TargetCommonOption/'
    config['ProjectOptions']['OutputName'] = __get(_base +'OutputName')
    config['ProjectOptions']['OutputDirectory'] = __get(_base +'OutputDirectory')
    config['ProjectOptions']['CreateHexFile'] = True if __get(_base +'CreateHexFile') else False

    if (__get(_base +'CreateExecutable') == '1' and \
        __get(_base +'CreateLib') == '0'):
        config['ProjectOptions']['CreateExecutableOrLib'] = 'exe'
    elif (__get(_base +'CreateExecutable') == '0' and \
        __get(_base +'CreateLib') == '1'):
        config['ProjectOptions']['CreateExecutableOrLib'] = 'lib'
    else:
        logger.warning('Wrong value combinition: CreateExecutable={} and CreateLib={}'.format(__get(_base +'CreateExecutable'), __get(_base +'CreateLib')))

    # 4
    _inc = __get('/Project/Targets/Target/TargetOption/Target51/C51/VariousControls/IncludePath')
    config['ProjectOptions']['IncludePaths'] = _inc.strip(';').split(';') if _inc else []

    # 5
    root = _parse_xml_doc(project_name + '.uvopt').getroot()
    config['UVisionOptions']['ClockFrequency'] = int(__get('/ProjectOpt/Target/TargetOption/CLK51'))

    os.chdir(old_dir)
    _dump_config(config, args.config_file)

    logger.info('Config file updated.')

# `file_grouping_method` implementation base.
class FileGrouping():
    def __init__(self):
        self._file_groups = dict()
        #self.__recent_group = dict()

    @classmethod
    def is_headerfile(cls, filepath :str):
        exts = config['uvmake']['header_extensions']
        return any([filepath.endswith(ext) for ext in exts])

    def has_gathered(self, filepath :str):
        for g in self._file_groups:
             if filepath in self._file_groups[g]:
                logger.info('Ignored duplicate file: "{}"'.format(filepath))
                return True
        return False

    def gather(self, filepaths :list):
        for filepath in filepaths:
            if self.has_gathered(filepath):
                continue
            self.gather_it(filepath)

    # method function that actually handles files,
    # implemented in subclasses.
    # grouping method differs in how `gather_it()`
    # handles the files passed in.
    def gather_it(self):
        logger.error('Calling un-implemented method!')
        pass

    def get(self):
        return self._file_groups

# implements file grouping method 'NONE'.
class FileGroupingNone(FileGrouping):
    def __init__(self):
        super().__init__()
        self.h_group_name = config['uvmake']['header_group_name']
        self.c_group_name = config['uvmake']['c_group_name']
        self._file_groups[self.h_group_name] = []
        self._file_groups[self.c_group_name] = []

    def gather_it(self, filepath :str):
        if self.is_headerfile(filepath):
            self._file_groups[self.h_group_name].append(filepath)
        else:
            self._file_groups[self.c_group_name].append(filepath)
    
# implements file grouping method 'C_BY_FOLDER'.
class FileGroupingCByFolder(FileGrouping):
    def __init__(self):
        super().__init__()
        self.h_group_name = config['uvmake']['header_group_name']
        self._file_groups[self.h_group_name] = []

    def gather_it(self, filepath :str):
        if self.is_headerfile(filepath):
            self._file_groups[self.h_group_name].append(filepath)
        else:
            folder_name = path.split(path.dirname(filepath))[1]
            if not self._file_groups.get(folder_name):
                self._file_groups[folder_name] = []
            self._file_groups[folder_name].append(filepath)

# implements file grouping method 'ALL_BY_FOLDER'.
class FileGroupingAllByFolder(FileGrouping):
    def __init__(self):
        super().__init__()

    def gather_it(self, filepath :str):
        folder_name = path.split(path.dirname(filepath))[1]
        if not self._file_groups.get(folder_name):
            self._file_groups[folder_name] = []
        self._file_groups[folder_name].append(filepath)


def gather_source_files(dirs :list, more_files :list, grouping :FileGrouping) -> dict:
    header_exts = config['uvmake']['header_extensions']
    c_exts = config['uvmake']['c_extensions']
    exclude_keywords = config['uvmake']['exclude_keywords']
    max_dir_tree_level = config['uvmake']['max_dir_tree_level']

    def _dir_tree_level(path_str :str) -> int:
        return len(re.split(r'\\+|/+', path_str))

    def _filter_exts(file_list, exts) -> list:
        # filter files by file extension.
        return [f for ext in exts for f in file_list if f.endswith(ext)]

    def _filter_kws(file_list :list):
        # filter files by keywords.
        return [f for kw in exclude_keywords for f in file_list if not kw in f]

    # def _filter_files(file_list, exts, kws):
    #     if len(exts) > len(kws):
    #         return _filter_exts(_filter_kws(file_list, kws), exts)
    #     else:
    #         return _filter_kws(_filter_exts(file_list, exts), kws)

    for d in dirs:
        d = path.normpath(d)
        if not _verify_path(d):
            continue
        logger.info('Gathering source files in directory: ' + d)
        base_level = _dir_tree_level(d)
        for dirpath, dirnames, filenames in os.walk(d):
            if _dir_tree_level(dirpath) - base_level > max_dir_tree_level:
                break
            filenames = _filter_exts(filenames, header_exts + c_exts)
            filepaths = [path.join(dirpath, filename) for filename in filenames] # combine to full path
            filepaths = _filter_kws(filepaths)
            if not filenames:
                continue
            logger.debug('Source files found in "{}":'.format(dirpath) + '\n  ' + '\n  '.join(filepaths))
            logger.info('  Files gathered: {}'.format(len(filepaths)))
            grouping.gather(filepaths)
    if more_files:
        more_files = [path.normpath(f) for f in more_files if _verify_path(f)]
        grouping.gather(more_files)

    file_groups = grouping.get()

    # add the paths to header files into 'IncludePaths'
    _opts = config['ProjectOptions']
    if not _opts['IncludePaths']:
        _opts['IncludePaths'] = []
    for g in file_groups:
        for f in file_groups[g]:
            if grouping.is_headerfile(f):
                # make the path relative to project directory
                f = path.relpath(f, start=config['ProjectDirectory'])
                f = path.dirname(f)
                if not f in _opts['IncludePaths']:
                   _opts['IncludePaths'].append(f)

    return file_groups

if __name__ == '__main__':

    args = shell_interface()

    if args.config_template:
        make_config_template_file()
        exit()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    if not path.exists(args.config_file) and not args.reverse_config:
        logger.error(args.config_file + '  not exist. run with `-h` to get help information')
        exit()
    if not path.exists(args.config_file):
        make_config_template_file()
    
    load_config()
    merge_args(args)

    # now, config file exists and loaded.
    if args.reverse_config:
        reverse_config()
        sys.exit(0)

    backup = False if args.no_backup else True
    
    _gm = config['uvmake']['file_grouping_method']
    if   _gm == 'NONE':
        grouping = FileGroupingNone()
    elif _gm == 'C_BY_FOLDER':
        grouping = FileGroupingCByFolder()
    elif _gm == 'ALL_BY_FOLDER':
        grouping = FileGroupingAllByFolder()
    else:
        logger.error('Unknown grouping method: {}. Please check the config file.'.format(str(_gm)))
        sys.exit(-1)

    file_groups = gather_source_files( \
        config['SourceDirectories'],
        config['SourceFiles'],
        grouping
        )
    # yaml.dump(file_groups, stream=sys.stdout)

    make_project(
        config['ProjectDirectory'],
        config['ProjectName'],
        file_groups,
        backup=backup
        )

    logger.info('All done.')
