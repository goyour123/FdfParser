import sys
import re
import json

def get_region_value(val, macro_dict):
    try:
        int(val, base=16)
    except:
        macro = re.findall(r'\$\((.*)\)', val)
        val = macro_dict[macro[0]]
    else:
        pass

    return hex(int(val, base=16))

def update_macro_dict(key, val, dict):
    try:
        int(val, base=16)
    except:
        oprd = re.findall(r'\$\((.*?)\)', val)
        operator = re.findall(r'([\+\-\*/])', val)
        result = int(dict[oprd[0]], base=16)
        for idx, optr in enumerate(operator):
            if (optr == '+'):
                result += int(dict[oprd[idx + 1]], base=16)
            elif (optr == '-'):
                result -= int(dict[oprd[idx + 1]], base=16)
            elif (optr == '*'):
                result *= int(dict[oprd[idx + 1]], base=16)
            elif (optr == '/'):
                result /= int(dict[oprd[idx + 1]], base=16)
        val = hex(int(result))
    else:
        pass
    dict[key] = val
    return dict

def main():

    fd_info, fd_list, fd_count = {}, [], 0
    macro_dict = {}
        
    with open(sys.argv[1], 'r') as f:
        for line in f:
            sect = re.findall(r'\[FD\.(.+)\]', line)
            macro = re.findall(r'DEFINE\s+?(\S+)\s+=\s+?(\S+)\s*', line)
            if len(fd_list) > 0:
                region = re.findall(r'([$0].+)\|([$0].+)', line)
                if len(region) > 0:
                    fd_info[fd_list[fd_count-1]].append(region[0])
            if len(sect) > 0:
                fd_list.append(sect[0])
                fd_count += 1
                fd_info[fd_list[fd_count-1]] = []
            if len(macro) > 0:
                # Collect MACROs into a dict
                macro_dict = update_macro_dict(macro[0][0], macro[0][1], macro_dict)

    # Output the MACRO dict as a JSON file
    macro_json = json.JSONEncoder().encode(macro_dict)
    with open('macro.json', 'w') as f:
        f.write(macro_json)

    # Create Region file
    with open('region.txt', 'w') as f:
        for fd in fd_info:
            f.writelines(fd + ' Offset|Size\n')
            for region_offect, region_size in fd_info[fd]:
                get_region_value(region_offect, macro_dict)
                get_region_value(region_size, macro_dict)
                f.writelines(region_offect + '|' + region_size + ' ' + get_region_value(region_offect, macro_dict) + '|' + get_region_value(region_size, macro_dict) +'\n')
            f.writelines('\n')
if __name__ == '__main__':
    main()
