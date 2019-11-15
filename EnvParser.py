import sys, os
import re, json
from warnings import warn

def dict2JsonFile(jsonFilePath, srcDict):
  with open(jsonFilePath, 'w') as j:
    j.write(json.dumps(srcDict, indent = 4))

def parseEnv(config_dict):
  defiDict = dict()
  with open(config_dict['Env'], 'r') as f:
    for line in f:
      # Filter the comments
      if line.split('#')[0] == '' or line == '\n':
          continue
      else:
          line = line.split('#')[0]
      
      defi = re.findall(r'.*DEFINE\s+(\S+)\s+=\s+(\S+)\s*', line)
      if defi:
        defiDict.update({defi[0][0]: defi[0][1]})
      
      defi2 = re.findall(r'.*EDK_GLOBAL\s+(\S+)\s+=\s+(\S+)\s*', line)
      if defi2:
        defiDict.update({defi2[0][0]: defi2[0][1]})
  return defiDict

if __name__ == '__main__':

  arg_names = ['script', 'env_file']
  args = dict(zip(arg_names, sys.argv))

  if len(args) > 1:
    if os.path.isfile(args['env_file']):
      envDict = parseEnv({'Env': args['env_file']})
    else:
      warn('System argument 1 is not a file path')
  else:
    pass

  if envDict:
    dict2JsonFile('Env.json', envDict)