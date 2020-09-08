import sys
import ctypes

DEFAULT_SYSTEM = "c64"
DEFAULT_OUTPUT = "a.prg"

TOKEN_MAP = {
    "END" : 0x80,
    "FOR" : 0x81,
    "NEXT" : 0x82,
    "DATA" : 0x83,
    "INPUT#" : 0x84,
    "INPUT" : 0x85,
    "DIM" : 0x86,
    "READ" : 0x87,
    "LET" : 0x88,
    "GOTO" : 0x89,
    "RUN" : 0x8A,
    "IF" : 0x8B,
    "RESTORE" : 0x8C,
    "GOSUB" : 0x8D,
    "RETURN" : 0x8E,
    "REM" : 0x8F,
    "STOP" : 0x90,
    "ON" : 0x91,
    "WAIT" : 0x92,
    "LOAD" : 0x93,
    "SAVE" : 0x94,
    "VERIFY" : 0x95,
    "DEF" : 0x96,
    "POKE" : 0x97,
    "PRINT#" : 0x98,
    "PRINT" : 0x99,
    "CONT" : 0x9A,
    "LIST" : 0x9B,
    "CLR" : 0x9C,
    "CMD" : 0x9D,
    "SYS" : 0x9E,
    "OPEN" : 0x9F,
    "CLOSE" : 0xA0,
    "GET" : 0xA1,
    "NEW" : 0xA2,
    "TAB(" : 0xA3,
    "TO" : 0xA4,
    "FN" : 0xA5,
    "SPC(" : 0xA6,
    "THEN" : 0xA7,
    "NOT" : 0xA8,
    "STEP" : 0xA9,
    "+" : 0xAA,
    "-" : 0xAB,
    "*" : 0xAC,
    "/" : 0xAD,
    "^" : 0xAE,
    "AND" : 0xAF,
    "OR" : 0xB0,
    ">" : 0xB1,
    "=" : 0xB2,
    "<" : 0xB3,
    "SGN" : 0xB4,
    "INT" : 0xB5,
    "ABS" : 0xB6,
    "USR" : 0xB7,
    "FRE" : 0xB8,
    "POS" : 0xB9,
    "SQR" : 0xBA,
    "RND" : 0xBB,
    "LOG" : 0xBC,
    "EXP" : 0xBD,
    "COS" : 0xBE,
    "SIN" : 0xBF,
    "TAN" : 0xC0,
    "ATN" : 0xC1,
    "PEEK" : 0xC2,
    "LEN" : 0xC3,
    "STR$" : 0xC4,
    "VAL" : 0xC5,
    "ASC" : 0xC6,
    "CHR$" : 0xC7,
    "LEFT$" : 0xC8,
    "RIGHT$" : 0xC9,
    "MID$" : 0xCA,
    "GO" : 0xCB
}

START_POINTS = {
    "pet" : 0x0400,
    "vic20" : 0x1001,
    "c64" : 0x0800,
    "c16" : 0x1000,
    "c128" :0x4000,
}

class Options():
    def __init__(self, system, start, inname, outname):
        if system:
            self.sys = system
        else:
            self.sys = DEFAULT_SYSTEM
        if start:
            self.start = start
        else:
            self.start = START_POINTS[self.sys]
        if inname:
            self.input = open(inname)
        else:
            self.input = sys.stdin
        if outname:
            self.output = open(outname, mode='r')
        else:
            self.output = open(DEFAULT_OUTPUT, mode='wb')

    def __del__(self):
        self.input.close()
        self.output.close()

def usage(progname):
    print("Usage:")
    print("\tpython {} [options] [filename]".format(progname))
    print("Options:")
    print("\t--sys <system>     Set the system to tokenize for.")
    print("\t                   Options are:")
    print("\t                       pet")
    print("\t                       vic20")
    print("\t                       c64 (default)")
    print("\t                       c16")
    print("\t                       c128")
    print("\t--start <address>  Starting address of basic.")
    print("\t                   Defaults to the standard for the specified system.")
    print("\t-o <output file>   Name of the output prg file.")
    print("Filename:")
    print("\t                   The filename is the name of the input file, relative to the working directory.")
    print("\t                   It defaults to STDIN.")
    exit(0)

def parse_args(args):
    nextarg = None
    system = None
    start = None
    inname = None
    outname = None
    for arg in args[1:]:
        if not nextarg:
            if arg == "--sys":
                nextarg = "system"
            elif arg == "--start":
                nextarg = "start"
            elif arg == "-o":
                nextarg = "outname"
            else:
                inname = arg
        else:
            if nextarg == "system":
                if arg in START_POINTS:
                    system = arg
                else:
                    usage(args[0])
            elif nextarg == "start":
                start = int(arg)
            elif nextarg == "outname":
                outname = arg
            nextarg = None
    return Options(system, start, inname, outname)

def byte(n):
    if isinstance(n, str):
        if len(n) > 1:
            raise ValueError("Bytes must be a single char")
        return ctypes.c_char(n.encode("utf-8"))
    elif isinstance(n, int):
        if n > 255:
            raise ValueError("Bytes have a max value of 255")
        return ctypes.c_ubyte(n)
    else:
        raise ValueError("Invalid type for a byte")

def lowbyte(n):
    if not isinstance(n, int) or n > 65535:
        raise ValueError("Invalid 2-byte integer")
    return ctypes.c_ubyte(n % 256)

def highbyte(n):
    if not isinstance(n, int) or n > 65535:
        raise ValueError("Invalid 2-byte integer")
    return ctypes.c_ubyte(n // 256)

def tokenize_file(options):
    binary = b""
    current_address = options.start
    binary = binary + lowbyte(current_address) + highbyte(current_address)
    for line in options.input:
        in_quote = False
        binary_line = b""
        splitline = line.split()
        line_number = int(splitline[0])
        rest_line = " ".join(splitline[1:])
        binary_line = binary_line + lowbyte(line_number) + highbyte(line_number)
        while (len(rest_line) > 0):
            if not in_quote:
                for token in TOKEN_MAP:
                    if rest_line.upper().startswith(token):
                        binary_line = binary_line + byte(TOKEN_MAP[token])
                        rest_line = rest_line[len(token):]
                        break
                else:
                    c = rest_line[0]
                    if c == '"':
                        in_quote = not in_quote
                    binary_line = binary_line + byte(c)
                    rest_line = rest_line.replace(c, "", 1)
            else:
                c = rest_line[0]
                if c == '"':
                    in_quote = not in_quote
                binary_line = binary_line + byte(c)
                rest_line = rest_line.replace(c, "", 1)
        next_address = current_address + len(binary_line)
        binary = binary + lowbyte(next_address) + highbyte(next_address) + binary_line + byte(0)
        current_address = next_address
    binary = binary + byte(0) + byte(0)
    return binary

def write_tokenized_basic(options, binary):
    options.output.write(binary)

def main(args):
    options = parse_args(args)
    binary = tokenize_file(options)
    write_tokenized_basic(options, binary)


if __name__ == "__main__":
    main(sys.argv)