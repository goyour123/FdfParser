import sys
import re
import json

def get_cond(oprda, oprdb, optr):
    if optr == '==':
        if oprda == oprdb:
            return True
        else:
            return False

def get_macro_value(macro, macro_dict):
    try:
        int(macro, base=16)
    except:
        var = re.findall(r'\$\((\S*)\)', macro)
        if len(var) > 0:
            val = macro_dict[var[0]]
        else:
            val = macro_dict[macro]
    else:
        val = macro

    try:
        int(val, base=16)
    except:
        pass
    else:
        val = hex(int(val, base=16))

    return val

def update_macro_dict(key, line, dict):
    oprd = re.findall(r'\s*[\+\-\*/=]\s*([^\+\-\*\/\n\s#]+)', line)
    operator = re.findall(r'([\+\-\*/])', line)

    result = int(get_macro_value(oprd[0], dict), base=16)

    if len(operator) > 0:
        for idx, optr in enumerate(operator):
            val = int(get_macro_value(oprd[idx + 1], dict), base=16)
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

def main():

    fd_info, fd_list, fd_count = {}, [], 0
    macro_dict = {}

    with open(sys.argv[1], 'r') as f:
        for line in f:
            
            # Filter the comments
            if line.split('#')[0] == '':
                continue
            else:
                line = line.split('#')[0]

            sect = re.findall(r'\[FD\.(.+)\]', line)
            macro = re.findall(r'\s*DEFINE\s+([^\s=]+)', line)
            statement = re.findall(r'\s*!(\S+)\s+', line)

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
                                config_f.write(json.JSONEncoder().encode({oprda: 'NO'}))
                        else:
                            with open('config.json', 'r+') as config_f:
                                config_dict = json.load(config_f)
                                try:
                                    config_dict[oprda]
                                except KeyError:
                                    # If the switch condition is not existed in config.json, add it into config.json and set it to NO
                                    config_dict[oprda] = 'NO'
                                    config_f.truncate(0)
                                    config_f.seek(0)
                                    config_f.write(json.JSONEncoder().encode(config_dict))

            if len(fd_list) > 0:
                region = re.findall(r'([\$0].+)\|([\$0].+)', line)
                if len(region) > 0:
                    fd_info[fd_list[fd_count-1]].append(region[0])

            if len(sect) > 0:
                fd_list.append(sect[0])
                fd_count += 1
                fd_info[fd_list[fd_count-1]] = []

            if len(macro) > 0:
                # Collect MACROs into a dict
                macro_dict = update_macro_dict(macro[0], line, macro_dict)

    # Output the MACRO dict as a JSON file
    macro_json = json.JSONEncoder().encode(macro_dict)
    with open('macro.json', 'w') as f:
        f.write(macro_json)

    # Create Region file
    with open('region.txt', 'w') as f:
        for fd in fd_info:
            f.writelines(fd + ' Offset|Size\n')
            for region_offect, region_size in fd_info[fd]:
                if int(get_macro_value(region_size, macro_dict), base=16) == 0:
                    continue
                f.writelines(region_offect + '|' + region_size + ' ' + get_macro_value(region_offect, macro_dict) + '|' + get_macro_value(region_size, macro_dict) +'\n')
            f.writelines('\n')

if __name__ == '__main__':
    main()
