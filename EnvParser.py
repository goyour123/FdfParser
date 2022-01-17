import sys, os
import re, json
import argparse
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

def parsePcdList():
  pass

if __name__ == '__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument("-e", "--EnvVarFile", type=lambda p: str(os.path.abspath(p)), help="Environment variable file")
  parser.add_argument("-p", "--PcdFile", type=lambda p: str(os.path.abspath(p)), help="PCD value file")

  args = parser.parse_args()

  if args.EnvVarFile:
    if os.path.isfile(args.EnvVarFile):
      envDict = parseEnv({'Env': args.EnvVarFile})
    else:
      warn('--EnvVarFile is not a file path')
      sys.exit()

  if args.PcdFile:
    if os.path.isfile(args.PcdFile):
      envDict = parsePcdList({'PcdList': args.PcdFile})
    else:
      warn('--PcdFile is not a file path')
      sys.exit()

  if envDict:
    dict2JsonFile('Env.json', envDict)