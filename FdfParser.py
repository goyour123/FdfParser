import sys
import re
import json

def get_region_value(val, macro_dict):
    try:
        int(val, base=16)
    except:
        macro = re.findall(r'\$\((\S*)\)', val)
        val = macro_dict[macro[0]]
    else:
        pass

    return hex(int(val, base=16))

def update_macro_dict(key, line, dict):
    oprd = re.findall(r'\s*[\+\-\*/=]\s*([^\+\-\*\/\n\s#]+)', line)
    operator = re.findall(r'([\+\-\*/])', line)

    result = int(get_region_value(oprd[0], dict), base=16)

    if len(operator) > 0:
        for idx, optr in enumerate(operator):
            val = int(get_region_value(oprd[idx + 1], dict), base=16)
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
            sect = re.findall(r'\[FD\.(.+)\]', line)
            macro = re.findall(r'DEFINE\s+([^\s=]+)', line)
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
                if int(get_region_value(region_size, macro_dict), base=16) == 0:
                    continue
                f.writelines(region_offect + '|' + region_size + ' ' + get_region_value(region_offect, macro_dict) + '|' + get_region_value(region_size, macro_dict) +'\n')
            f.writelines('\n')

if __name__ == '__main__':
    main()
