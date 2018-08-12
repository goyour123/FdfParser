import sys, os
import re, json

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
        return None

def get_macro_value(macro, macro_dict):
    val = macro_dict[macro]
    try:
        int(val, base=16)
    except:
        pass
    else:
        val = hex(int(val, base=16))

    return val

def get_value(var, macro_dict):
    try:
        int(var, base=16)
    except ValueError:
        return int(get_macro_value(extract_var(var), macro_dict), base=16)
    else:
        return int(var, base=16)

def update_macro_dict(key, line, dict):
    oprd = re.findall(r'\s*[\+\-\*/=]\s*([^\+\-\*\/\n\s#]+)', line)
    operator = re.findall(r'([\+\-\*/])', line)

    # Set the first operand as the initial result value
    result = get_value(oprd[0], dict)

    if len(operator) > 0:
        for idx, optr in enumerate(operator):
            val = get_value(oprd[idx + 1], dict)
            if (optr == '+'):
                result += val
            elif (optr == '-'):
                result -= val
            elif (optr == '*'):
                result *= val
            elif (optr == '/'):
                result /= val

    dict[key] = hex(int(result))
    return dict

def parse(parsingFilePath=None):

    fd_info, fd_list, fd_count = {}, [], 0
    macro_dict = {}

    with open(parsingFilePath, 'r') as f:

        cond_nest = []
        fd_cond, fv_cond = False, False

        for line in f:
            
            # Filter the comments
            if line.split('#')[0] == '':
                continue
            else:
                line = line.split('#')[0]

            sect = re.findall(r'\[(\S+)\.(\S+)\]', line)
            macro = re.findall(r'\s*DEFINE\s+([^\s=]+)', line)
            statement = re.findall(r'\s*!(\S+)\s+', line)

            # Check what section is under parsing
            if len(sect) > 0:
                sect_type, name = sect[0]
                if (sect_type == 'FD'):
                    fd_cond, fv_cond= True, False
                    fd_list.append(name)
                    fd_count += 1
                    fd_info[fd_list[fd_count-1]] = []
                elif (sect_type == 'FV'):
                    fd_cond, fv_cond = False, True
                else:
                    fd_cond, fv_cond = False, False

            if fv_cond:
                continue

            if len(statement) > 0:
                if statement[0] == 'if':
                    if_stat = re.findall(r'\s*!if\s+\$\((\S+)\)\s*==\s*(\S+)\s*', line)

                    if len(if_stat) > 0:
                        oprda, oprdb = if_stat[0]

                        # Save switch conditions to config.json
                        try:
                            open('config.json', 'r+')
                        except FileNotFoundError:
                            # If config.json is not existed, create it and set the switch condition to NO
                            with open('config.json', 'w') as config_f:
                                config_dict = {'Switch': {oprda: 'NO'}}
                                config_f.write(json.dumps(config_dict, indent=4))
                        else:
                            with open('config.json', 'r+') as config_f:
                                config_dict = json.load(config_f)
                                try:
                                    config_dict['Switch'][oprda]
                                except KeyError:
                                    # If the switch condition is not existed in config.json, add it into config.json and set it to NO
                                    config_dict['Switch'][oprda] = 'NO'
                                    config_f.truncate(0)
                                    config_f.seek(0)
                                    config_f.write(json.dumps(config_dict, indent=4))

                    cond_nest.append(get_cond(get_macro_value(oprda, config_dict['Switch']), oprdb, '=='))
                elif statement[0] == 'else':
                    cond_nest[-1] = not cond_nest[-1]
                elif statement[0] == 'endif':
                    cond_nest.pop(-1)

            # Skip parsing if the condition is not match
            if False in cond_nest:
                continue

            if fd_cond > 0:
                region = re.findall(r'([\$0].+)\|([\$0].+)', line)
                if len(region) > 0:
                    fd_info[fd_list[fd_count-1]].append(region[0])

            if len(macro) > 0:
                # Collect MACROs into a dict
                macro_dict = update_macro_dict(macro[0], line, macro_dict)

    # Output the MACRO dict as a JSON file
    macro_json = json.dumps(macro_dict, indent=4)
    with open('macro.json', 'w') as f:
        f.write(macro_json)

    # Save parsingFilePath into config.json
    with open('config.json', 'r+') as f:
        config_dict = json.load(f)
        config_dict.update({'Fdf': parsingFilePath})
        f.truncate(0)
        f.seek(0)
        f.write(json.dumps(config_dict, indent=4))

    # Create Region file
    with open('region.txt', 'w') as f:
        f.writelines('----------------\nParsed File Path: ' + parsingFilePath + '\n----------------\n\n')
        for fd in fd_info:
            f.writelines(fd + ' Offset|Size\n')
            for region_offset, region_size in fd_info[fd]:
                offset_macro, size_macro = extract_var(region_offset), extract_var(region_size)
                if int(get_macro_value(size_macro, macro_dict), base=16) == 0:
                    continue
                f.writelines(region_offset + '|' + region_size + ' ' + get_macro_value(offset_macro, macro_dict) + '|' + get_macro_value(size_macro, macro_dict) +'\n')
            f.writelines('\n')

if __name__ == '__main__':

    try:
        sys.argv[1]
    except IndexError:
        if os.path.isfile('config.json'):
            with open('config.json', 'r') as config_f:
                config_dict = json.load(config_f)
                try:
                    config_dict['Fdf']
                except KeyError:
                    sys.exit()
                else:
                    fdfPath = config_dict['Fdf']
        else:
            sys.exit()
    else:
        fdfPath = sys.argv[1]

    parse(parsingFilePath=fdfPath)
