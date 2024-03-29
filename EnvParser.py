import sys, os
import re, json
import argparse
import configparser
from warnings import warn

def dict2JsonFile(jsonFilePath, srcDict):
  with open(jsonFilePath, 'w') as j:
    j.write(json.dumps(srcDict, indent = 4))

def parseIni(config_dict):
  defidict = dict()
  config = configparser.ConfigParser(strict=False)
  config.optionxform = lambda option: option
  config.read(config_dict['Env'])
  for sect in config.sections():
    for key in config[sect]:
      defidict.update({key: config[sect][key]})
  return defidict

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

def parsePcdList(config_dict):
  defiDict = dict()
  with open(config_dict['PcdList'], 'r') as f:
    for line in f:
      defi = re.findall(r'(\S+\.\S+):\s(.+)', line)
      if defi:
        defiDict.update({defi[0][0]: defi[0][1]})
  return defiDict

if __name__ == '__main__':

  valDict = dict()

  parser = argparse.ArgumentParser()
  parser.add_argument("-e", "--EnvVarFile", type=lambda p: str(os.path.abspath(p)), help="Environment variable file")
  parser.add_argument("-p", "--PcdFile", type=lambda p: str(os.path.abspath(p)), help="PCD value file")
  parser.add_argument("-i", "--IniFile", type=lambda p: str(os.path.abspath(p)), help="Ini file")

  args = parser.parse_args()

  if args.EnvVarFile:
    if os.path.isfile(args.EnvVarFile):
      valDict.update({"Env": args.EnvVarFile})
      valDict.update(parseEnv(valDict))
    else:
      warn('--EnvVarFile is not a file path')
      sys.exit()

  if args.PcdFile:
    if os.path.isfile(args.PcdFile):
      valDict.update({"PcdList": args.PcdFile})
      valDict.update(parsePcdList(valDict))
    else:
      warn('--PcdFile is not a file path')
      sys.exit()

  if args.IniFile:
    if os.path.isfile(args.IniFile):
      valDict.update({"Ini": args.IniFile})
      valDict.update(parseIni(valDict))
    else:
      warn('--IniFile is not a file path')
      sys.exit()

  if valDict:
    dict2JsonFile('Val.json', valDict)