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
# prefix is used to ensure unique names
def parse_blocks(blocks, prefix):
    final_list    = []  # many possible
    initial_state = None # there can only be one.
    block_dict = {}
    for block in blocks:
        b_id   = block.attrib["id"]
        b_name = prefix+block.attrib["name"]+"-"+b_id
        b_tag  = block.find("tag").text
        block_dict[b_id] = {"name": b_name, "tag": b_tag}

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
        t["cur"] = blocks[tran.find("from").text]["name"]
        t["new"] = blocks[tran.find("to").text]["name"]

        def rw_val(val):
            if val == "_" or val == ",":
                print("Warning, there was a '_' or ',' in your JFlap, you will probably have errors.")
                print("'_' and ',' cannot be symbols when converting to online turing machine.")
                return "U"
            elif val == None:
                return "_"
            return val

        def move_val(val):
            if val and val.upper() == "R":
                return ">"
            elif val and val.upper() == "L":
                return "<"
            else:
                return "-"

        def op_tape(search, val_func, default):
            t[search] = {}
            results = tran.findall(search)
            for op in results:
                if op.attrib and op.attrib.get("tape"):
                    aid = op.attrib["tape"]
                    t[search][aid] = val_func(op.text)
                else:
                    t[search]["1"] = val_func(op.text)

            if len(results) == 0:
                t[search]["1"] = val_func(default)
                return default
            else:
                return tran.find(search).text

        read_val = op_tape("read", rw_val, None)
        op_tape("write", rw_val, read_val)
        op_tape("move", move_val, None)

        tran_list.append(t)
    return tran_list

def get_tape(root):
    elem = root.find("tapes")
    tape_text = "1"
    if elem != None:
        tape_text = elem.text

    tape = []
    for x in range(int(tape_text)):
        tape.append(str(x+1))
    return tape

def gen_file_contents(name, init, accept, trans, tapes):
    format_str = "{header}\nname: {name}\ninit: {init}\naccept: {accept}\n\n{data}"

    header = ("// Converted from JFlap to \"https://turingmachinesimulator.com/\".\n"
            "// Convert yours today at \"github.com/alanxoc3/jflap-to-turing\"!\n"
            "// And enjoy wasting your life, programming turing machines!\n")

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

    return format_str.format( header=header, name=name, init=str(init), accept=', '.join(map(str,accept)), data=data)

def automaton_to_bloc_tran(node, prefix):
    # Now get the automaton blocks.
    blocks, accept_list, init_state = parse_blocks(node.findall("block"), prefix)
    trans = parse_trans(node.findall("transition"), blocks)

    for k in blocks:
        node_tag = blocks[k]["tag"]
        node_name = blocks[k]["name"] # name is unique
        nal, nis, nt, nb = automaton_to_bloc_tran(node.find(node_tag), node_name+"-")
        if blocks[k]["name"] == init_state and nis != None:
            init_state = nis

        new_accept_list = []
        for accept in accept_list:
            if blocks[k]["name"] == accept and len(nal) > 0:
                new_accept_list = new_accept_list + nal
            else:
                new_accept_list.append(accept)

        accept_list = new_accept_list

        # any transitions with k now go to the starting transition.
        # replace the new on any that is k with the start name
        if len(nb) > 0:
            new_trans = []
            for x in trans:
                if x["new"] == blocks[k]["name"]:
                    x["new"] = nis

                if x["cur"] == blocks[k]["name"]:
                    # add transition for each final.
                    # remove original transition.
                    for accept in nal:
                        cpy = dict(x)
                        cpy["cur"] = accept
                        new_trans.append(cpy)
                else:
                    new_trans.append(x)
            trans = new_trans

            trans = trans + nt

    return accept_list, init_state, trans, blocks

def main(file_in, file_out, name):
    ## CODE ----------
    root = xml.etree.ElementTree.parse(file_in).getroot()

    automaton = root.find("automaton")
    tapes = get_tape(root)
    accept_list, init_state, trans, _ = automaton_to_bloc_tran(automaton, "")

    if name == None:
        name = "Jflap Converted Turing Machine"

    f_str = gen_file_contents(name, init_state, accept_list, trans, tapes)

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
    parser.add_argument("-n", "--name", help="The name to give your machine.")
     
    # parse it
    args = parser.parse_args()

    # run the code!
    main(args.input, args.o, args.name)
