#!/usr/bin/env python

# Converts a .jff (Jflap) file to the rules on "https://turingmachinesimulator.com/".

# RULES for "turingmachinesimulator":
# name: [name_of_machine]
# init: [initial_state]
# accept: [accept_state_1],... ,[accept_state_n]
# 
# // this is repeated for each transition.
# [current_state],[read_symbol],read...
# [new_state],[write_symbol],sym...,[>|<|-],lr...

import xml.etree.ElementTree
import argparse
 
# parses the blocks for how many, initial, and accept states.
def parse_blocks(blocks):
    final_list    = []  # many possible
    initial_state = "" # there can only be one.
    block_dict = {}
    for block in blocks:
        b_id   = block.attrib["id"]
        b_name = block.attrib["name"]
        block_dict[b_id] = b_name

        if (block.find("final") != None):
            final_list.append(b_name)
        if (block.find("initial") != None):
            initial_state = b_name

    return block_dict, final_list, initial_state

# Parse the transitions
def parse_trans(trans, blocks):
    tran_list = []
    for tran in trans:
        t = {}
        t["cur"] = blocks[tran.find("from").text]
        t["new"] = blocks[tran.find("to").text]

        def rw_val(val):
            if val == "_":
                print("warning, there was a '_' in your jflap, converting to 'U'.")
                return "U"
            elif val == None:
                return "_"
            return val

        def move_val(val):
            if val.upper() == "R":
                return ">"
            elif val.upper() == "L":
                return "<"
            elif val.upper() == "S":
                return "-"
            else:
                return "_"

        def op_tape(search, val_func):
            t[search] = {}
            for op in tran.findall(search):
                aid = op.attrib["tape"]
                t[search][aid] = val_func(op.text)

        op_tape("read", rw_val)
        op_tape("write", rw_val)
        op_tape("move", move_val)

        tran_list.append(t)
    return tran_list

def get_tape(tape_text):
    tape = []
    for x in range(int(tape_text)):
        tape.append(str(x+1))
    return tape

def gen_file_contents(name, init, accept, trans, tapes, blocks):
    format_str = "{header}\nname: {name}\ninit: {init}\naccept: {accept}\n\n{data}"

    header = ("// jflap file converted to \"https://turingmachinesimulator.com/\".\n"
            "// Enjoy wasting your life, programming turing machines!\n")

    def tran_to_str(tran):
        top_arr = [tran["cur"]]

        for tape in tapes:
            top_arr.append(tran["read"][tape])
        bot_arr = [tran["new"]]
        for tape in tapes:
            bot_arr.append(tran["write"][tape])
        for tape in tapes:
            bot_arr.append(tran["move"][tape])

        top_str = ",".join(map(str,top_arr))
        bot_str = ",".join(map(str,bot_arr))
        return "\n".join([top_str, bot_str])

    data = "\n\n".join(map(tran_to_str, trans))

    return format_str.format(
            header=header,
            name=name,
            init=str(init),
            accept=', '.join(map(str,accept)),
            data=data
            )


def main(file_in, file_out):
    ## CODE ----------
    root = xml.etree.ElementTree.parse(file_in).getroot()

    automaton = root.find("automaton")
    tapes = get_tape(root.find("tapes").text)

    # Now get the automaton blocks.
    blocks, accept_list, init_state = parse_blocks(automaton.findall("block"))
    trans = parse_trans(automaton.findall("transition"), blocks)

    f_str = gen_file_contents("Jflap Converted Turing Machine", init_state, accept_list, trans, tapes, blocks)

    if file_out == None:
        print(f_str)
    else:
        f = open(file_out, "w")
        f.write(f_str)
        f.close()

if __name__ == "__main__":
    # create a parser object
    parser = argparse.ArgumentParser(prog="PROG",description = "A program that converts JFlap files to the format at \"https://turingmachinesimulator.com/\"")
     
    # arguments
    parser.add_argument("input", help="JFlap input file.")
    parser.add_argument("-o", help="Output file to write to instead of stdin.")
     
    # parse it
    args = parser.parse_args()

    # run the code!
    main(args.input, args.o)
