__author__ = 'desultory'

__version__ = '0.2.2'

from subprocess import run

MODULE_METADATA_FILES = ['modules.alias', 'modules.alias.bin', 'modules.builtin', 'modules.builtin.alias.bin', 'modules.builtin.bin', 'modules.builtin.modinfo',
                         'modules.dep', 'modules.dep.bin', 'modules.devname', 'modules.order', 'modules.softdep', 'modules.symbols', 'modules.symbols.bin']


def resolve_kmod(self, module_name):
    """
    Gets the file path of a kernel module
    """
    args = ['modinfo', '--field', 'filename', module_name]

    if self.config_dict.get('kernel_version'):
        args += ['--set-version', self.config_dict['kernel_version']]

    cmd = run(args, capture_output=True)
    if cmd.returncode != 0:
        self.logger.error(f'Kernel module {module_name} not found')
        self.logger.debug(f'Error: {cmd.stderr.decode("utf-8").strip()}')
        return

    module_path = cmd.stdout.decode('utf-8').strip()

    if module_path == '(builtin)':
        self.logger.info(f'Kernel module {module_name} is built-in')
        return

    self.logger.debug(f'Kernel module {module_name} is located at {module_path}')

    return module_path


def get_all_modules(self):
    """
    Gets the name of all currently installed kernel modules
    """
    cmd = run(['lsmod'], capture_output=True)
    if cmd.returncode != 0:
        self.logger.error('Failed to get list of kernel modules')
        self.logger.debug(f'Error: {cmd.stderr.decode("utf-8").strip()}')
        return

    modules = cmd.stdout.decode('utf-8').split('\n')[1:]
    modules = [module.split()[0] for module in modules if module and module.split()[0] != 'Module']

    self.logger.info(f'Found {len(modules)} active kernel modules')
    return modules


def get_module_metadata(self):
    """
    Gets all module metadata for the specified kernel version
    """
    from pathlib import Path

    if 'kernel_version' not in self.config_dict:
        self.logger.debug("Kernel version not specified, using current kernel")
        cmd = run(['uname', '-r'], capture_output=True)
        if cmd.returncode != 0:
            self.logger.error('Failed to get kernel version')
            self.logger.debug(f'Error: {cmd.stderr.decode("utf-8").strip()}')
            return

        kernel_version = cmd.stdout.decode('utf-8').strip()
        self.logger.info(f'Using detected kernel version: {kernel_version}')
    else:
        kernel_version = self.config_dict['kernel_version']

    module_path = Path('/lib/modules/') / kernel_version

    for meta_file in MODULE_METADATA_FILES:
        meta_file_path = module_path / meta_file

        self.logger.debug("Adding kernel module metadata files to dependencies: %s", meta_file_path)
        self.config_dict['dependencies'].append(meta_file_path)


def fetch_modules(self):
    """
    Fetches all kernel modules
    """
    modules = self.config_dict.get('kernel_modules', get_all_modules(self))

    for module in modules:
        if module_path := resolve_kmod(self, module):
            self.config_dict['dependencies'].append(module_path)
        else:
            self.logger.warning(f'Failed to add kernel module {module} to dependencies')

    get_module_metadata(self)
