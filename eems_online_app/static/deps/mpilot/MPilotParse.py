from collections import OrderedDict
import re
import copy as cp

# MPilot parser
#
# Functions to:
#
#  Parse a file into commands
#  Parse a string into commands
#  Parse a command into parameters
#
# tjs 2016.06.20
#    Started
# tjs 2016.11.04
#    Added parsing of a string

def ParseStringToCommands(
    inStr,
    objNm=None
    ):
    # Each command must start on a new line
    # a mptCmdStruct is a list of dicts for the command string

    mptCmdStructs = OrderedDict()
    mptCmdStructstartLineNo = 0
    if objNm is None: objNm = 'Input string'

    cmdLine = ''      # buffer to build command from lines of input file
    inParens = False  # whether or not parsing is within parentheses
    parenCnt = 0      # count of parenthesis levels
    inLineCnt = 0     # line number of input file for error messages.

    rawCmd = ''
    cleanCmd = ''

    # Basically a finite state machine to build individual commands
    
    for inLine in inStr.split('\n'):
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
                        '  input: {}, line {}:\n'.format(objNm,inLineCnt),
                        '  {}\n'.format(inLine),
                        )
                    )
            if inParens and parenCnt == 0:
                if charNdx < (len(cleanLine)-1):
                    raise Exception(
                        '{}{}{}{}'.format(
                            '\n********************ERROR********************\n',
                            'Extraneous characters beyond end of command\n',
                            '  Input: {}, line {}:\n'.format(objNm,inLineCnt),
                            '  {}\n'.format(inLine),
                            )
                        )

                else:

                    mptCmdStructTmp = ({
                        'cmdFileNm':objNm,
                        'lineNo':mptCmdStructstartLineNum,
                        'rawCmdStr':rawCmd,
                        'cleanCmdStr':cleanCmd,
                        })

                    mptCmdStructTmp['parsedCmd'] = ParseCommandToParams(mptCmdStructTmp)
                    rsltNm = mptCmdStructTmp['parsedCmd']['rsltNm']

                    if mptCmdStructTmp['parsedCmd']['rsltNm'] in mptCmdStructs:
                        raise Exception(
                            '{}{}{}{}{}{}'.format(
                                '\n********************ERROR********************\n',
                                'Result appears more than once in input: {}.\n'.format(objNm),
                                'First occurence: line {}:\n'.format(mptCmdStructs[rsltNm]['lineNo']),
                                '  Command:\n{}\n'.format(mptCmdStructs[rsltNm]['rawCmdStr']),
                                'Second occurence: line {}:\n'.format(mptCmdStructTmp['lineNo']),
                                '  Command:\n{}\n'.format(mptCmdStructTmp['rawCmdStr']),
                                )
                            )

                    mptCmdStructs[mptCmdStructTmp['parsedCmd']['rsltNm']] = cp.deepcopy(mptCmdStructTmp)

                    rawCmd = ''
                    cleanCmd = ''
                    inParens = False
                    parenCnt = 0

        # for charNdx in range(len(cleanLine)):
    # for inLine in inStr.split('\n'):

    if cleanCmd != '':
        raise Exception(
            '{}{}{}{}'.format(
                '\n********************ERROR********************\n',
                'Incomplete command in file\n',
                '  input: {}, line {}:\n'.format(objNm,mptCmdStructstartLineNum),
                '  {}\n'.format(rawCmd),
                )
            )

    return mptCmdStructs

# def ParseStringToCommands(inFDef):

def ParseFileToCommands(inFDef):
    
    if isinstance(inFDef, basestring):
        fObj = open(inFDef, 'rU')
    else:
        fObj = inFDef

    with fObj as inFile:
        rtrn = ParseStringToCommands(fObj.read(),fObj.name)

    return rtrn

# def ParseFileToCommands(inFDef):

def ParseCommandToParams(mptCmdStruct):
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
        raise Exception(
            '{}{}{}{}'.format(
                '\n********************ERROR********************\n',
                'Command is missing result name.\n',
                'File: {}  Line number: {}\n'.format(mptCmdStruct['cmdFileNm'],mptCmdStruct['lineNo']),
                'Full command:\n{}\n'.format(mptCmdStruct['rawCmdStr'])),
            )


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

# def ParseCommandToParams(inCmd):
    
