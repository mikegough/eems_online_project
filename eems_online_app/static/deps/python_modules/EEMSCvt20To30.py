#!/opt/local/bin/python
import MPilotProgram as mpprog
import MPilotFramework as mpf
import MPilotParse as mpp
from collections import OrderedDict
import sys
import os
import re
import copy as cp

class Converter(object):

    def __init__(
        self,
        inFNm,                 # input script filepath
        outFNm,                # output script filepath
        newInDataFNm=None,     # script's input file data path; None == no change
        newOutDataFNm=None,    # script's output file data path; None == no change
        writeDataOutput=True,   # suppresses script writing results to file
        deleteVars=['CSVID'],  # empty for no deletes
        ):

        if inFNm == outFNm:
          raise Exception('Input and output file names must be different')

        # Initialize variables
        self.inFNm = inFNm
        self.outFNm = outFNm
        self.newInDataFNm = newInDataFNm
        self.newOutDataFNm = newOutDataFNm
        self.writeDataOutput = writeDataOutput
        self.deleteVars = deleteVars

        self.outScript = None

        with open(inFNm,'r') as inF: self.inScript = inF.read()

        # Quick check to see if handling an EEMS 2 or an EEMS 3 script
        if self._Validate20Input():
            self.scriptType = 2
        else:
            self.scriptType = 3

        self.cmds20 = None

        self.mpFw = mpf.MPilotFramework([
                'MPilotEEMSBasicLib',
                'MPilotEEMSFuzzyLogicLib',
                'MPilotEEMSNC4IO',
                ])

        # Global lookup table for command substitution

        self.cmdLU = {
            'READ':{'newNm':'EEMSRead','warning':None},
            'READMULTI':{'newNm':'','warning':'Converting to Reads'},
            'CVTTOFUZZY':{'newNm':'CvtToFuzzy','warning':None},
            'CVTTOFUZZYCURVE':{'newNm':'CvtToFuzzyCurve','warning':None},
            'CVTTOFUZZYCAT':{'newNm':'CvtToFuzzyCat','warning':None},
            'MEANTOMID':{'newNm':'MeanToMid','warning':None},
            'COPYFIELD':{'newNm':'Copy','warning':None},
            'NOT':{'newNm':'FuzzyNot','warning':None},
            'OR':{'newNm':'FuzzyOr','warning':None},
            'AND':{'newNm':'FuzzyAnd','warning':None},
            'EMDSAND':{'newNm':None,'warning':'Not supported in EEMS 3.0'},
            'ORNEG':{'newNm':'FuzzyAnd','warning':None},
            'XOR':{'newNm':'FuzzyXOr','warning':None},
            'SUM':{'newNm':'Sum','warning':None},
            'MULT':{'newNm':'Multiply','warning':None},
            'DIVIDE':{'newNm':'ADividedByB','warning':None},
            'MIN':{'newNm':'Minimum','warning':None},
            'MAX':{'newNm':'Maximum','warning':None},
            'MEAN':{'newNm':'Mean','warning':None},
            'UNION':{'newNm':'FuzzyUnion','warning':None},
            'DIF':{'newNm':'AMinusB','warning':None},
            'SELECTEDUNION':{'newNm':'FuzzySelectedUnion','warning':None},
            'WTDUNION':{'newNm':'FuzzyWeightedUnion','warning':None},
            'WTDEMDSAND':{'newNm':'','warning':None},
            'WTDMEAN':{'newNm':'WeightedMean','warning':None},
            'WTDSUM':{'newNm':'WeightedSum','warning':None},
            # 'CALLEXTERN':{'newNm':'','warning':None},
            'SCORERANGEBENEFIT':{'newNm':'ScoreRangeBenefit','warning':None},
            'SCORERANGECOST':{'newNm':'ScoreRangeCost','warning':None},
            }

        # Used to determine of any directly read variable is fuzzy
        self.fuzzy30Ops = [
            'FuzzyNot',
            'FuzzyOr',
            'FuzzyAnd',
            'FuzzyXOr',
            'FuzzyUnion',
            'FuzzySelectedUnion',
            'FuzzyWeightedUnion',
            ]

    # def __init__(...)

    def _Validate20Input(self):

        # Only validates that the would-be 2.0 files has
        # either a valid READ or a READMULTI command

        is20 = False

        if re.search(r'^READ\(',self.inScript) or \
          re.search(r'^READMULTI\(',self.inScript) or \
          re.search(r'\nREAD\(',self.inScript) or \
          re.search(r'\nREADMULTI\(',self.inScript):

          return True

        else:

          return False

        # if re.search(r'^READ\(',script) or ... else

    # def _Validate20Input(self,inFNm):

    def _Parse20CmdToParams(self,mptCmdStruct):

        # mptCmdStruct is a dict:
        # 'lineNo': the command's line within the input file
        # 'rawCmdStr': the command string as it appeared in the input
        #    file, comments, line breaks, and all
        # 'cleanCmdStr': the command string stripped of all its
        #    comments, line breaks, and all

        # strip white space
        cmdStr = re.sub('\s+','',mptCmdStruct['cleanCmdStr'])

        # parse the command string into result, command name, and parameters
        exprParse = re.match(r'\s*([^\s]+.*=){0,1}\s*([^\s]+.*)\s*\(\s*(.*)\s*\)',cmdStr)

        if not exprParse or len(exprParse.groups()) != 3:
            raise Exception(
                '{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Invalid command format.\n',
                    'File: {}  Line number: {}\n'.format(mptCmdStruct['cmdFileNm'],mptCmdStruct['lineNo']),
                    'Full command:\n{}\n'.format(mptCmdStruct['rawCmdStr'])),
                    )

        parsedCmd = OrderedDict()

        # Every command must have a result
        if exprParse.groups()[0] is None:
            parsedCmd['rsltNm'] = 'NeedsName'
        else:
            parsedCmd['rsltNm'] = re.sub(r'\s*=\s*','',exprParse.groups()[0].strip())

        if (not re.match(r'^[a-zA-Z0-9\-\_]+$',parsedCmd['rsltNm']) and
            not re.match(r'^\[[a-zA-Z0-9\-\_,]+\]$',parsedCmd['rsltNm'])
            ):
            raise Exception(
                '{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Invalid result name in command.\n',
                    'File: {}  Line number: {}\n'.format(mptCmdStruct['cmdFileNm'],mptCmdStruct['lineNo']),
                    'Full command:\n{}\n'.format(mptCmdStruct['rawCmdStr'])),
                )

        parsedCmd['cmd'] = exprParse.groups()[1].strip()

        # Parse out the parameters
        paramStr = exprParse.groups()[2]
        paramPairs = []
        while paramStr != '':
            paramPairMatchObj = re.match(r'\s*([^=]*=\s*\[[^\[]*\])\s*,*\s*(.*)',paramStr)
            if paramPairMatchObj:
                paramPairs.append(paramPairMatchObj.groups()[0])
                paramStr = paramPairMatchObj.groups()[1]
            else:
                paramPairMatchObj = re.match(r'\s*([^=,]*=\s*[^,]*)\s*,*\s*(.*)',paramStr)
                if paramPairMatchObj:
                    paramPairs.append(paramPairMatchObj.groups()[0])
                    paramStr = paramPairMatchObj.groups()[1]
                else:
                    raise Exception(
                        '{}{}{}{}{}'.format(
                            '\n********************ERROR********************\n',
                            'Invalid parameter specification.\n',
                            'File: {}  Line number: {}\n'.format(mptCmdStruct['cmdFileNm'],mptCmdStruct['lineNo']),
                            'Section of command: {}\n'.format(paramStr),
                            'Full command:\n{}\n'.format(mptCmdStruct['rawCmdStr']),
                            )
                        )

            # if paramPair:...else:

        # while paramStr != '':

        parsedCmd['params'] = OrderedDict()
        for paramPair in paramPairs:

            paramTokens = re.split(r'\s*=\s*',paramPair)

            paramTokens[0] = paramTokens[0].strip()
            paramTokens[1] = paramTokens[1].strip()

            paramTokens[1] = re.sub(r'\s*\[\s*','[',paramTokens[1])
            paramTokens[1] = re.sub(r'\s*\]\s*',']',paramTokens[1])
            paramTokens[1] = re.sub(r'\s*,\s*',',',paramTokens[1])

            if (len(paramTokens) != 2
                or paramTokens[0] == ''
                or paramTokens[1] == ''
                or paramTokens[0] in parsedCmd
                ):

                raise Exception(
                    '{}{}{}{}'.format(
                        '\n********************ERROR********************\n',
                        'Invalid parameter specification. Line number {}\n'.format(mptCmdStruct['lineNo']),
                        'Parameter specification: {}\n'.format(paramPair),
                        'Full command:\n{}\n'.format(mptCmdStruct['rawCmdStr']),
                        )
                    )

            parsedCmd['params'][paramTokens[0]] = paramTokens[1]

        return parsedCmd

    # def _Parse20CmdToParams(self,mptCmdStruct):

    def _Parse20FileToCmds(self):

        cmds20 = []
        mptCmdStructstartLineNo = 0

        cmdLine = ''      # buffer to build command from lines of input file
        inParens = False  # whether or not parsing is within parentheses
        parenCnt = 0      # count of parenthesis levels
        inLineCnt = 0     # line number of input file for error messages.

        rawCmd = ''
        cleanCmd = ''

        # Parse the file into commands

        with open(self.inFNm,'rU') as inF:
            for inLine in inF:

                inLineCnt +=1

                cleanLine = re.sub('#.*$','',inLine)
                cleanLine = re.sub('\s+','',cleanLine)

                # Only start gathering a command where
                # a command starts
                if rawCmd == '':
                    if cleanLine == '':
                        continue
                    else:
                        mptCmdStructstartLineNum = inLineCnt

                rawCmd += inLine

                for charNdx in range(len(cleanLine)):
                    cleanCmd += cleanLine[charNdx]
                    if cleanLine[charNdx] == '(':
                        inParens = True
                        parenCnt += 1
                    elif cleanLine[charNdx] == ')':
                        parenCnt -= 1

                    if parenCnt < 0:
                        raise Exception(
                            '{}{}{}{}'.format(
                                '\n********************ERROR********************\n',
                                'Unmatched right paren *)*\n',
                                '  input: {}, line {}:\n'.format(self.inFNm,inLineCnt),
                                '  {}\n'.format(inLine),
                                )
                            )
                    if inParens and parenCnt == 0:
                        if charNdx < (len(cleanLine)-1):
                            raise Exception(
                                '{}{}{}{}'.format(
                                    '\n********************ERROR********************\n',
                                    'Extraneous characters beyond end of command\n',
                                    '  Input: {}, line {}:\n'.format(self.inFNm,inLineCnt),
                                    '  {}\n'.format(inLine),
                                    )
                                )

                        else:

                            mptCmdStructTmp = ({
                                'cmdFileNm':self.inFNm,
                                'lineNo':mptCmdStructstartLineNum,
                                'rawCmdStr':rawCmd,
                                'cleanCmdStr':cleanCmd,
                                })

                            # self._Parse20CmdToParams(mptCmdStructTmp)
                            cmds20.append(cp.deepcopy(self._Parse20CmdToParams(mptCmdStructTmp)))

                            rawCmd = ''
                            cleanCmd = ''
                            inParens = False
                            parenCnt = 0

                # for charNdx in range(len(cleanLine)):
            # for line in inF:
        # with open(self.inFNm,'rU') as inF:

        if cleanCmd != '':
            raise Exception(
                '{}{}{}{}'.format(
                    '\n********************ERROR********************\n',
                    'Incomplete command in file\n',
                    '  input: {}, line {}:\n'.format(self.inFNm,mptCmdStructstartLineNum),
                    '  {}\n'.format(rawCmd),
                    )
                )

        # Replace READMULTI first, adding to commands

        for cmd in cmds20:

            if cmd['cmd'] == 'READMULTI':

                inFldNms = cmd['params']['InFieldNames'].replace('[','').replace(']','').split(',')
                for inFldNm in cmd['params']['InFieldNames']:
                    newCmd = cp.deepcopy(cmd)
                    newCmd['cmd'] = 'READ'
                    del(newCmd['params']['InFieldNames'])
                    newCmd['params']['InFieldName'] = inFldNm
                    cmds20.append(newCmd)

            # if cmd['cmd'] == 'READMULTI':
        # for cmd in cmds20:

        # This gives us a list of valid 2.0 commands for conversion
        self.cmds20 = cmds20

    # def _Parse20FileToCmds(self):

    def _Turn20CmdsInto30(self):

        # This will make destructive changes to the 2.0 commands

        # Then fix the result name for read
        # Snag a filename and fieldname for the output

        if self.newInDataFNm is not None:
            DimensionFileName = self.newInDataFNm
        else:
            DimensionFileName = None

        DimensionFieldName = None

        for cmd in self.cmds20:

            if cmd['cmd'] == 'READ':
                if 'NewFieldName' in cmd['params']:
                    cmd['rsltNm'] =  cmd['params']['NewFieldName']
                    del(cmd['params']['NewFieldName'])
                else:
                    cmd['rsltNm'] =  cmd['params']['InFieldName']

                if DimensionFileName is None:
                    DimensionFileName = cmd['params']['InFileName']
                if DimensionFieldName is None:
                    DimensionFieldName = cmd['params']['InFieldName']

            # if cmd['cmd'] == 'READ':
        # for cmd in cmds20:

        # Convert to dictionary, easier to fix all that needs fixing
        self.cmds20 = OrderedDict(zip([cmd['rsltNm'] for cmd in self.cmds20],self.cmds20))

        # Delete unwanted commands
        for rsltNm in self.cmds20.keys():
            if rsltNm in self.deleteVars:
                del(self.cmds20[rsltNm])


        # If result is to be output, remove it from the 2.0 command and add it to outputs
        outputFNmsAndVars = {} # will have filename and list

        for cmdNdx,cmd in self.cmds20.items():

            if 'params' in cmd:
                if 'OutFileName' in cmd['params']:
                    if cmd['params']['OutFileName'] not in outputFNmsAndVars:
                        outputFNmsAndVars[cmd['params']['OutFileName']] = [cmd['rsltNm']]
                    else:
                        outputFNmsAndVars[cmd['params']['OutFileName']].append(cmd['rsltNm'])
                    del cmd['params']['OutFileName']

            if cmd['cmd'] in self.cmdLU:
                if self.cmdLU[cmd['cmd']] is None:
                    raise Exception(
                        '{}{}{}'.format(
                            '\n********************ERROR********************\n',
                            'EEMS 2.0 command: {}'.format(cmd['cmd']),
                            self.cmdLU['cmd']['warning']
                            )
                    )
                else:
                    cmd['cmd'] = self.cmdLU[cmd['cmd']]['newNm']

        # for cmdNdx,cmd in self.cmds20.items():

        # Now create the output commands


        if self.writeDataOutput:
            outCnt = 0

            if self.newOutDataFNm is None:

                for fNm,vNms in outputFNmsAndVars.items():
                    newCmd = OrderedDict()
                    newCmd['rsltNm'] = 'output{}'.format(outCnt)
                    outCnt = outCnt + 1
                    newCmd['cmd'] = 'EEMSWrite'
                    newCmd['params'] = OrderedDict()
                    newCmd['params']['DimensionFileName'] = DimensionFileName
                    newCmd['params']['DimensionFieldName'] = DimensionFieldName
                    newCmd['params']['OutFileName'] = self.outFNm
                    newCmd['params']['OutFieldNames'] = '[{}]'.format(','.join(outputFNmsAndVars[fNm]))
                    self.cmds20[(newCmd['rsltNm'])] = newCmd
                # for fNm,vNms in outputFNmsAndVars:

            else:

                allVNms = []
                for fNm,vNms in outputFNmsAndVars.items():
                    allVNms = allVNms + vNms

                newCmd = OrderedDict()
                newCmd['rsltNm'] = 'output{}'.format(outCnt)
                outCnt = outCnt + 1
                newCmd['cmd'] = 'EEMSWrite'
                newCmd['params'] = OrderedDict()
                newCmd['params']['DimensionFileName'] = DimensionFileName
                newCmd['params']['DimensionFieldName'] = DimensionFieldName
                newCmd['params']['OutFileName'] = self.newOutDataFNm
                newCmd['params']['OutFieldNames'] = '[{}]'.format(','.join(allVNms))
                self.cmds20[(newCmd['rsltNm'])] = newCmd

            # if self.newOutDataFNm is None:

        # This makes sure that fuzzy values read in directly are tagged as fuzzy
        for cmd,cmdData in self.cmds20.items():

            if cmdData['cmd'] in self.fuzzy30Ops:

                tmpInFieldNames = []

                if 'InFieldName' in cmdData['params']:
                    tmpInFieldNames.append(cmdData['params']['InFieldName'])
                if 'InFieldNames' in cmdData['params']:
                    tmpInFieldNames = tmpInFieldNames + \
                      re.sub(r"\]","",re.sub(r"\[","",cmdData['params']['InFieldNames'])).split(',')

                # We have the names, now if they were initialized with READ,
                # we need to tag them as fuzzy.
                for inFldNm in tmpInFieldNames:
                    if self.cmds20[inFldNm]['cmd'] == 'EEMSRead':
                        self.cmds20[inFldNm]['params']['DataType'] = 'Fuzzy'


    # def _Prep20CmdsFor30(self)

    def _Convert20To30(self):

        self._Parse20FileToCmds()
        self._Turn20CmdsInto30()

        # Turn commands in to string
        self.outScript = ''
        for ndx,cmd in self.cmds20.items():

            params = []
            for paramNm,paramVal in cmd['params'].items():
                if self.newInDataFNm is not None and paramNm == 'InFileName':
                    params.append('{} = {}'.format(paramNm, self.newInDataFNm))
                else:
                    params.append('{} = {}'.format(paramNm, paramVal))

            self.outScript = '{}{} = {}(\n  {}\n  )\n'.format(
                self.outScript,
                cmd['rsltNm'],
                cmd['cmd'],
                ',\n  '.join(params)
                )

    # def _Convert20To30(self):

    def _DoSubsFor30(self):

        # Get parsed program
        self.cmds30 = mpp.ParseStringToCommands(self.inScript)

        # Remove unwanted variables
        for rsltNm in self.cmds30.keys():
            if rsltNm in self.deleteVars:
                del(self.cmds30[rsltNm])

        # Suppress or subsitute output path
        if not self.writeDataOutput:
            for rsltNm,data in self.cmds30.items():
                if data['parsedCmd']['cmd'] == 'EEMSWrite':
                    del(self.cmds30['rsltNm'])
        elif self.newOutDataFNm is not None:
            for rsltNm,data in self.cmds30.items():
                if data['parsedCmd']['cmd'] == 'EEMSWrite':
                    data['parsedCmd']['params']['OutFileName'] = self.newInDataFNm

        # Substitute input path
        if self.newInDataFNm is not None:
            for rsltNm,data in self.cmds30.items():
                if data['parsedCmd']['cmd'] == 'EEMSRead':
                    data['parsedCmd']['params']['InFileName'] = self.newInDataFNm

        self.outScript = ''
        for rsltNm,data in self.cmds30.items():
            self.outScript = '{}{}\n'.format(
                self.outScript,
                self.mpFw.CreateFxnObject(data['parsedCmd']['cmd'],data).FormattedCmd()
                )

    # def _DoSubsFor30(self):

    def _VerifyAndWriteOutScript(self):

        with mpprog.MPilotProgram(
            mpf.MPilotFramework([
                'MPilotEEMSBasicLib',
                'MPilotEEMSFuzzyLogicLib',
                'MPilotEEMSNC4IO',
                ]),
            sourceProgStr = self.outScript
            ) as prog:

            pass

        with open(self.outFNm,'w') as outF:
            outF.write(self.outScript)

    # def _VerifyAndWriteOutScript(self):

    def ConvertScript(self):

        if self.scriptType == 2:
            self._Convert20To30()
        elif self.scriptType == 3:
            self._DoSubsFor30()
        else:
            raise Exception('Unknown script type: {}'.format(self.scriptType))

        self._VerifyAndWriteOutScript()

    # def ConvertFile(self):

# class Converter(object):

################################################################################

