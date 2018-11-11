import sys, os
import re, json
from FdfParser import parse, get_cond, get_macro_value

def fileReplace(f, lines):
    f.seek(0)
    f.truncate()
    f.writelines(lines)

def hexFillZero(h, len):
    return h[0:2] + h[2:].zfill(len)

def restore(cfgDict, switchInUsed, target, newVal):
    cond = list()
    with open(cfgDict['Fdf'], 'r+') as f:
        fdf = f.readlines()
        for idx, line in enumerate(fdf):
            # Filter the comments
            validLine = line
            if line.split('#')[0] == '':
                continue
            else:
                validLine = line.split('#')[0]

            # Skip FDF section bacause there is no MACRO define in it usually
            sect = re.findall(r'\[(\S+)\.(\S+)\]', line)
            if sect:
                break

            # Find switch statement
            statement = re.findall(r'\s*!(\S+)\s+', validLine)
            if statement:
                if statement[0] == 'if':
                    if_stat = re.findall(r'\s*!if\s+\$\((\S+)\)\s*==\s*(\S+)\s*', line)
                    if if_stat:
                        oprdA, oprdB = if_stat[0]
                        cond.append(get_cond(get_macro_value(oprdA, switchInUsed), oprdB, '=='))
                elif statement[0] == 'else':
                    cond[-1] = not cond[-1]
                elif statement[0] == 'endif':
                    cond.pop(-1)

            if False in cond:
                continue

            # Find MACROs
            macro = re.findall(r'\s*DEFINE\s+([^\s=]+)', validLine)
            if len(macro) > 0:
                if macro[0] == target:
                    oprd = re.findall(r'\s*[\+\-\*/=]\s*([^\+\-\*\/\n\s#]+)', validLine)
                    fdf[idx] = line.replace(oprd[0], newVal)
        fileReplace(f, fdf)

if __name__ == '__main__':

    # Need to run FdfParser or FdVisualizer to generate the config.json whick contains FDF path
    if os.path.isfile('config.json'):
        with open('config.json', 'r') as config_f:
            config_dict = json.load(config_f)
            try:
                config_dict['Fdf']
            except KeyError:
                print('FDF file path doesn\'t exist in config.json!')
                sys.exit()
    else:
        print('config.json file not exist!')
        sys.exit()

    _ign, macroDict, config_dict, switchInused = parse(config_dict)
    
    if sys.argv[1] not in macroDict:
        print('Macro not found!')
        sys.exit()

    try:
        size = hexFillZero(hex(int(sys.argv[2], 16)), 8)
    except:
        print('Not valid size!')
        sys.exit()

    restore(config_dict, switchInused, sys.argv[1], size)
