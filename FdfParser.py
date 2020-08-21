import sys, os
import re, json
from warnings import warn
from EnvParser import parseEnv

def get_cond(oprda, oprdb, optr):
    if optr == '==':
        if oprda == oprdb:
            return True
        else:
            return False

def extract_var(string):
    var = re.findall(r'\$\((\S*)\)', string)
    if len(var) > 0:
        return var[0]
    else:
        try:
            int(string, 16)
        except:
            return None
        else:
            return string

def get_macro_value(macro, macro_dict):
    try:
        int(macro_dict[macro], 16)
    except ValueError:
        val = macro_dict[macro]
    except KeyError:
        try:
            int(macro, 16)
        except:
            val = None
        else:
            val = macro
    else:
        val = hex(int(macro_dict[macro], 16))
    return val

def get_value(var, macro_dict):
    try:
        int(var, base=16)
    except ValueError:
        if get_macro_value(extract_var(var), macro_dict):
            return int(get_macro_value(extract_var(var), macro_dict), base=16)
        else:
            return None
    else:
        return int(var, base=16)

def update_macro_dict(key, line, macro_dict):
    oprd = re.findall(r'\s*[\+\-\*/=]\s*([^\+\-\*\/\n\s#]+)', line)
    operator = re.findall(r'([\+\-\*/])', line)

    # Set the first operand as the initial result value
    if type(get_value(oprd[0], macro_dict)) != type(None):
        result = get_value(oprd[0], macro_dict)
    else:
        return macro_dict, line

    if len(operator) > 0:
        for idx, optr in enumerate(operator):
            if type(get_value(oprd[idx + 1], macro_dict)) != type(None):
                val = get_value(oprd[idx + 1], macro_dict)
                if (optr == '+'):
                    result += val
                elif (optr == '-'):
                    result -= val
                elif (optr == '*'):
                    result *= val
                elif (optr == '/'):
                    result /= val
            else:
                return macro_dict, line

    macro_dict[key] = hex(int(result))
    return macro_dict, None

def dictUpdateJson(jsonFilePath, dictUpdate):
    if os.path.isfile(jsonFilePath):
        with open (jsonFilePath, 'r+') as j:
            jDict = json.load(j)
            jDict.update(dictUpdate)
            j.truncate(0)
            j.seek(0)
            j.write(json.dumps(jDict, indent = 4))
    else:
        with open (jsonFilePath, 'w') as j:
            j.write(json.dumps(dictUpdate, indent = 4))

def cnvRgnName(rgnDef):
    try:
        rgnName = re.search(r'[FLASH]+_REGION_(.+)_[A-Z]+', rgnDef).group(1)
    except AttributeError:
        return rgnDef
    else:
        return rgnName

def setOutputHex(h):
    return h[0:2] + (h[2:].zfill(8)).upper()

def charPrinter(char, text, length):
    frontDashNum = round(length/2) - round(len(text)/2)
    backDashNum = length - round(length/2) - (len(text) - round(len(text)/2))
    return char * frontDashNum + text + char * backDashNum

def export(export_file_path, fdf_file_path, fd_dict, macro_dict):
    width = 61
    with open(export_file_path, 'w') as f:
        f.writelines('----------------\nParsed File Path: ' + fdf_file_path + '\n----------------\n\n')
        for fd in fd_dict:
            pre_offset = None
            f.writelines('[FD.' + fd + ']\n')
            f.writelines('# |' + charPrinter('-', ' ' + fd + ' layuot ', width) + '|\n')
            for region_offset, region_size in reversed(fd_dict[fd]):
                offset_macro, size_macro = extract_var(region_offset), extract_var(region_size)
                if int(get_macro_value(size_macro, macro_dict), base=16) == 0:
                    continue
                offset = int(get_macro_value(offset_macro, macro_dict), 16) + int(get_macro_value(size_macro, macro_dict), 16)
                if pre_offset and pre_offset != offset:
                    f.writelines('# |' + charPrinter('-', '', width) + '| ' + setOutputHex(hex(pre_offset)) + '\n')
                    f.writelines('# |' + charPrinter(' ', '', width) + '| ' + '\n')
                pre_offset = int(get_macro_value(offset_macro, macro_dict), 16)

                f.writelines('# |' + charPrinter('-', '', width) + '| ' + setOutputHex(hex(offset)) + '\n')
                f.writelines('# |' + charPrinter(' ', cnvRgnName(region_offset), width) + '| ' + '\n')
                if (int(get_macro_value(offset_macro, macro_dict), 16) == 0):
                    f.writelines('# |' + charPrinter('-', '', width) + '| ' + setOutputHex(get_macro_value(offset_macro, macro_dict)) + '\n')
            f.writelines('\n')

def parse(config_dict):

    fd_info, fd_list, fd_count, sorted_fd_info = {}, [], 0, {}
    macro_dict, switch_inused, pcd_dict, pending_lines = {}, {}, {}, []

    # Init macro_dict from config_dict
    for cfg in config_dict['Switch']:
        print(config_dict['Switch'][cfg])
        try:
            int(config_dict['Switch'][cfg], base=16)
        except:
            pass
        else:
            macro_dict.update({cfg: config_dict['Switch'][cfg]})

    with open(config_dict['Fdf'], 'r') as f:

        cond_nest = []
        fd_cond, ign_cond = False, True

        for line in f:

            # Filter the comments
            if line.split('#')[0] == '' or line == '\n':
                continue
            else:
                line = line.split('#')[0]

            sect = re.findall(r'\[(\S+)\]', line)
            # Check what section is under parsing
            if len(sect) > 0:
                sect_type = sect[0].split('.')
                if (sect_type[0] == 'FD'):
                    fd_cond, ign_cond= True, False
                    fd_list.append(sect_type[1])
                    fd_count += 1
                    fd_info[fd_list[fd_count-1]] = []
                elif (sect_type[0] == 'Defines'):
                    fd_cond, ign_cond = False, False
                else:
                    ign_cond = True
                continue

            if ign_cond:
                continue

            statement = re.findall(r'\s*!(\S+)\s+', line)
            if len(statement) > 0:
                if statement[0] == 'if':
                    if_stat = re.findall(r'\s*!if\s+\$\((\S+)\)\s*==\s*(\S+)\s*', line)
                    if_stat_pcd = re.findall(r'\s*!if\s+([a-zA-Z0-9]+\.[a-zA-Z0-9]+)\s*', line)
                    if len(if_stat) > 0:
                        oprda, oprdb = if_stat[0]
                        try:
                            config_dict['Switch'][oprda]
                        except KeyError:
                            # If the switch condition is not existed in config_dict, add and set it to NO
                            if 'Switch' not in config_dict:
                                config_dict.update({'Switch': {oprda: 'NO'}})
                            else:
                                config_dict['Switch'][oprda] = 'NO'
                        cond_nest.append(get_cond(get_macro_value(oprda, config_dict['Switch']), oprdb, '=='))
                        switch_inused.update({oprda: config_dict['Switch'][oprda]})
                    elif len(if_stat_pcd) > 0:
                        # Collect PCDs
                        oprda = if_stat_pcd[0]
                        try:
                            pcd_dict[oprda]
                        except KeyError:
                            pcd_dict[oprda] = False
                        # No parsing for PCD switch
                        cond_nest.append(False)
                    else:
                        # No parsing for unknown case
                        cond_nest.append(False)

                elif statement[0] == 'else':
                    cond_nest[-1] = not cond_nest[-1]

                elif statement[0] == 'elseif':
                    elif_stat = re.findall(r'\s*!elseif\s+\$\((\S+)\)\s*==\s*(\S+)\s*', line)
                    elif_stat_pcd = re.findall(r'\s*!elseif\s+([a-zA-Z0-9]+\.[a-zA-Z0-9]+)\s*', line)
                    if len(elif_stat) > 0:
                        oprda, oprdb = elif_stat[0]
                        try:
                            config_dict['Switch'][oprda]
                        except KeyError:
                            # If the switch condition is not existed in config_dict, add and set it to NO
                            if 'Switch' not in config_dict:
                                config_dict.update({'Switch': {oprda: 'NO'}})
                            else:
                                config_dict['Switch'][oprda] = 'NO'
                        cond_nest[-1] = get_cond(get_macro_value(oprda, config_dict['Switch']), oprdb, '==')
                        switch_inused.update({oprda: config_dict['Switch'][oprda]})
                    elif len(elif_stat_pcd) > 0:
                        # Collect PCDs
                        oprda = elif_stat_pcd[0]
                        try:
                            pcd_dict[oprda]
                        except KeyError:
                            pcd_dict[oprda] = False
                        # No parsing for PCD switch
                        cond_nest[-1] = False
                    else:
                        # No parsing for unknown case
                        cond_nest[-1] = False

                elif statement[0] == 'endif':
                    cond_nest.pop(-1)
                continue

            # Skip parsing if the condition is not match
            if False in cond_nest:
                continue

            if fd_cond > 0:
                region = re.findall(r'([\$0].+)\|([\$0].+)', line)
                if len(region) > 0:
                    fd_info[fd_list[fd_count-1]].append(region[0])
                    continue

            macro = re.findall(r'\s*DEFINE\s+([^\s=]+)', line)
            if len(macro) > 0:
                # Collect MACROs into a dict
                macro_dict, pending = update_macro_dict(macro[0], line, macro_dict)
                if pending:
                    pending_lines.append(pending)
                elif pending_lines:
                    temp_pl_list = []
                    for pl in pending_lines:
                        pl_macro = re.findall(r'\s*DEFINE\s+([^\s=]+)', pl)
                        macro_dict, pending = update_macro_dict(pl_macro[0], pl, macro_dict)
                        if pending:
                            temp_pl_list.append(pl)
                    pending_lines = temp_pl_list

    # Sorting the region in fd_info
    if macro_dict:
        for fd in fd_info:
            sorted_fd_info.update({fd: sorted(fd_info[fd], key=lambda rgn: int(get_macro_value(extract_var(rgn[0]), macro_dict), 16))})
    else:
        warn('The macro_dict is empty.')
        warn('No MACRO define was found in this condition.')

    return sorted_fd_info, macro_dict, config_dict, switch_inused, fd_info

if __name__ == '__main__':
    arg_names = ['script', 'fdf_file', 'env_file']
    args = dict(zip(arg_names, sys.argv))

    if len(args) < 3:
        warn('Too few arguments')
        sys.exit()
    else:
        if os.path.isfile(args['fdf_file']) and os.path.isfile(args['env_file']):
            config_dict = {'Fdf': os.path.abspath(args['fdf_file']), \
                           'Env': os.path.abspath(args['env_file'])}
            config_dict.update({'Switch': parseEnv(config_dict)})
        else:
            warn('Invalid arguments')
            sys.exit()

    sorted_fd_dict, macro_dict, config_dict, switch_inused, fd_info = parse(config_dict)

    # Output the MACRO dict as a JSON file
    # dictUpdateJson('macro.json', macro_dict)

    # Output the FD dict as a JSON file
    # dictUpdateJson('fd.json', sorted_fd_dict)

    # Save config_dict into config.json
    dictUpdateJson('config.json', config_dict)

    # Export Region file
    export('region.txt', config_dict['Fdf'], sorted_fd_dict, macro_dict)
