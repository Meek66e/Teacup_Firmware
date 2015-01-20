#!/bin/env python
import re

VERSION = "0.1"


supportedCPUs = ['ATmega168', 'ATmega328P', 'ATmega644', 'ATmega644P', 'ATmega644PA',
				'ATmega1280', 'ATmega1284', 'ATmega1284P', 'ATmega2560', 'AT90USB1286']

pinNames = ["AIO%d" % x for x in range(16)] + ["DIO%d" % x for x in range(64)]
pinNamesWithBlank = ["-"] + pinNames

sensorTypes = { "MAX6675": 'TT_MAX6675', "Thermistor": 'TT_THERMISTOR',
			 "AD595": 'TT_AD595', "PT100": 'TT_PT100',  "Intercom": 'TT_INTERCOM'}

BSIZE = (90, 60)
BSIZESMALL = (90, 30)


TYPE_GENERAL = 0
TYPE_FLOAT = 1

reDefQSm = re.compile("\s*#define\s+(\S+)\s+(.*)")
reDefQSm2 = re.compile("\s*(\"[^\"]*\")")

reInclude = re.compile("^\s*#include\s+\"([^\"]*)")
reFloatAttr = re.compile("/\*\s*float\s*\*/")
reDefine = re.compile("\s*#define\s+(\w+)\s+(\S+)")
reDefineBL = re.compile("^\s*#define\s+(\w+)\s+(\S+)")
reCommDefBL = re.compile("^\s*//\s*#define\s+(\w+)\s+(\S+)")
reDefQS = re.compile("\s*#define\s+(\w+)\s+(\"[^\"]*\")")
reDefTS = re.compile("\s*(DEFINE_TEMP_SENSOR\\([^)]*\\))")
reDefHT = re.compile("\s*(DEFINE_HEATER\\([^)]*\\))")
reDefBool = re.compile("\s*#define\s+(\w+)\s+")
reDefBoolBL = re.compile("^\s*#define\s+(\w+)\s+")
reCommDefBoolBL = re.compile("^\s*//\s*#define\s+(\S+)\s+")
reStartSensors = re.compile("^\s*//\s*DEFINE_TEMP_SENSORS_START")
reEndSensors = re.compile("^\s*//\s*DEFINE_TEMP_SENSORS_END")
reStartHeaters = re.compile("^\s*//\s*DEFINE_HEATERS_START")
reEndHeaters = re.compile("^\s*//\s*DEFINE_HEATERS_END")
reCandHeatPins = re.compile("^\s*//\s*#define\s+HEATER_PIN\s+(\w+)")
reCandThermPins = re.compile("^\s*//\s*#define\s+THERMISTOR_PIN\s+(\w+)")
reCandProcessors = re.compile("^\s*//\s*#define\s+CPU_TYPE\s+(\w+)")
reCandCPUClocks = re.compile("^\s*//\s*#define\s+F_CPU_OPT\s+(\w+)")

reHelpTextStart = re.compile("^\s*/\*\*\s+\\\\def\s+(.*)")
reHelpTextEnd = re.compile("^\s*\*/")
		
reSensor3 = re.compile(".*\\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\\)")
reSensor4 = re.compile(".*\\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\\)")
reHeater = re.compile(".*\\(\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*\\)")

reInteger = re.compile("^\d+U?L?$")
reFloat = re.compile("^\d+(\.\d*)?$")

defineValueFormat =      "#define %-30.30s %s\n"
defineBoolFormat =       "#define %s\n"
defineHeaterFormat =     "#define HEATER_%s HEATER_%s\n"
defineDCExtruderFormat = "#define %-30.30s HEATER_%s\n"
