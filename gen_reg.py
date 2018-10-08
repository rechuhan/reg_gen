# -*- coding:utf-8 -*-
from collections import namedtuple
from jinja2 import Environment
import xlrd
import sys
import os
import re

def escape_reserved_bit_name(in_str, offset):
    if in_str=='RESERVED' or in_str=='reserved':
        out_str = in_str+"%s"%offset
    else:
        out_str = in_str
    return out_str

def change_to_int(in_str):
    if isinstance(in_str,str):
        if in_str.startswith('0x'):
            out_int = int(in_str, 16)
        else:
            try:
                out_int = int(in_str)
            except:
                out_int = int(float(in_str))
    else:
        out_int = int(in_str)
    return out_int

def gen_blk(file_name, base_address, all_regbit):
    all_reg = []
    blk = namedtuple("Blk", ['name', 'base_address', 'reg'])
    reg = namedtuple("Reg", ['name', 'bitfield'])
    saved_name = ''
    tmp_lst = []
    for one_bitfield in all_regbit:
        if one_bitfield.REG_NAME!=saved_name:   # a new reg
            if tmp_lst:                         # not first
                tmp_reg = reg._make([one_bitfield.REG_NAME, tmp_lst])   #previous reg
                all_reg.append(tmp_reg)
                tmp_lst = []
            saved_name = one_bitfield.REG_NAME
        tmp_lst.append(one_bitfield)
    else:
        tmp_reg = reg._make([one_bitfield.REG_NAME, tmp_lst])   #previous reg
        all_reg.append(tmp_reg)

    #for one_reg in all_reg:
    #    print (one_reg)
    if file_name.endswith('_reg.xlsx'):
        blk_name = file_name[:-9]
    else:
        print("ERROR, file name should end with _reg.xlsx, but %s"%file_name)
        blk_name = file_name
    tmp_blk = blk._make([blk_name, base_address, all_reg])
    return tmp_blk
def gen(template_file_name, all_blk):
    env = Environment()
    t = env.from_string(open(template_file_name).read())
    txt = t.render(all_blk=all_blk)
    s = txt.encode('utf-8',"ignore")
    fp = open('kunpeng_reg.xml', 'w')
    fp.write(txt)
    fp.close()

def content_uniform(in_str):
    out_str = re.sub(r'\s*,\s*', ',', in_str.strip())
    #out_str = "%r"%in_str
    #out_str = in_str.replace(u"",r",")  #TODO FIXME
    return out_str

def deal_with_cell_type(sheet, row, col):
            #print("xlrd.XL_CELL_TEXT is %d"%xlrd.XL_CELL_TEXT)
            if sheet.cell_type(row,col)==xlrd.XL_CELL_TEXT:
                #print("got str on %r with cell_type %d"%(sheet.cell_value(row,col), sheet.cell_type(row,col)))
                return content_uniform(sheet.cell_value(row, col))
            elif sheet.cell_type(row,col)==xlrd.XL_CELL_NUMBER:
                return "%f"%sheet.cell_value(row,col)
            elif sheet.cell_type(row,col)==xlrd.XL_CELL_DATE:
                return "%r"%sheet.cell_value(row,col)
            else :
                #print("return empty on %r with cell_type %d"%(sheet.cell_value(row,col), sheet.cell_type(row,col)))
                return ""

def get_cell_content(all_crange, sheet, row, col):
    for one_crange in all_crange:
        rlo, rhi,   clo, chi = one_crange
        #print("one crange %d %d %d %d"%(rlo, rhi, clo, chi))
        if rlo <= row < rhi and clo <= col < chi:
            return deal_with_cell_type(sheet, rlo, clo)

    else:
        return deal_with_cell_type(sheet, row, col)

def have_next_line(all_crange, row):
    for one_crange in all_crange:
        rlo, rhi,   clo, chi = one_crange
        if row == rlo and clo==1 and chi==2:
            return True
    else:
        return False

def belong_to_previous_line(all_crange, row):
    for one_crange in all_crange:
        rlo, rhi,   clo, chi = one_crange
        if row == rhi-1 and clo==1 and chi==2:
            return True
    else:
        return False


def read_reg_xls(file_name):
    trans_access = {
        'RW':'read-write',
        'RO':'read-only',
        'WO':'write-only',
        'W1C':'oneToClear'

    }
    print("opening excel spreadsheet %s\n"%file_name)
    book = xlrd.open_workbook(file_name)
    for sheet_index in range(book.nsheets):
        one_sheet = book.sheet_by_index(sheet_index)
        all_crange = []
        for crange in one_sheet.merged_cells:
            #rlo, rhi, clo, chi = crange
            all_crange.append(crange)
    #print("got %s"%one_sheet.name)
    current_category = ''
    saved_lst = []
    for row_index in range(one_sheet.nrows):
        if row_index==0:
            tmp_content = get_cell_content(all_crange, one_sheet, 0, 0)
            if tmp_content!="base address":
                print("ERROR, first cell should be base address, but %s"% tmp_content)
                os._exit(4)
            base_addr = get_cell_content(all_crange, one_sheet, 0, 1)
            base_addr = change_to_int(base_addr)
        elif row_index==1:
            tmp_lst = []
            no_use_cols = []
            for col_index in range(one_sheet.ncols) :
                tmp_content = get_cell_content(all_crange, one_sheet, row_index, col_index)
                if tmp_content:
                    tmp_lst.append(tmp_content)
                else:
                    no_use_cols.append(col_index)
            regbit = namedtuple("Regbit", ['ADDRESS', 'REG_NAME',  'RESET_VALUE', 'BITS', 'SIG_NAME','ACCESS','DESCRIPTION','COMMENT', 'bitoffset', 'bitwidth'])
            all_regbit = []
        elif row_index>1:
            tmp_content = get_cell_content(all_crange, one_sheet, row_index, 3)
            if not tmp_content: #if bits column is empty, an empty row, go to next row
                continue
            tmp_content = get_cell_content(all_crange, one_sheet, row_index, 0)
            if not tmp_content:
                tmp_lst = saved_lst #if column 0 is empty, this is a bitfield belong to previous reg
            else:
                tmp_lst = ['','','','','','','','','','']        #if column 0 not empty, this is a new reg

            for col_index in range(one_sheet.ncols):
                #print("cell[%0d, %0d] is %s"%(row_index, col_index, get_cell_content(all_crange, one_sheet, row_index, col_index)))
                if col_index not in no_use_cols:
                    tmp_content = get_cell_content(all_crange, one_sheet, row_index, col_index)
                    if tmp_content:
                        tmp_lst[col_index]=tmp_content
                    #else :  #empty cell, use previous value
                    #    #print(tmp_lst)
            saved_lst = tmp_lst
            tmp_lst[5] = trans_access.get(tmp_lst[5], 'read-write')
            tmp_lst[0] = change_to_int(tmp_lst[0])
            if isinstance(tmp_lst[3],str):
                parts = tmp_lst[3].split(':')
                if len(parts)>1:
                    tmp_lst[8] = int(float(parts[1]))
                    tmp_lst[9] = int(float(parts[0]))-int(float(parts[1]))+1
                else:
                    tmp_lst[8] = int(float(parts[0]))
                    tmp_lst[9] = 1
            else:
                tmp_lst[8] = int(float(tmp_lst[3]))
                tmp_lst[9] = 1
            tmp_lst[4] = escape_reserved_bit_name(tmp_lst[4], tmp_lst[8])
            tmp_regbit = regbit._make(saved_lst)
            all_regbit.append(tmp_regbit)

    #for one_regbit in all_regbit:
    #    print (one_regbit)
    return base_addr, all_regbit

if __name__=="__main__":
    if len(sys.argv) <2:
        print("one excel file name is needed")
    else:
        all_blk = []
        for one_arg in sys.argv[1:]:
            if not os.path.isfile(one_arg):
                print("ERROR, %s is not a file"%one_arg)
                continue
            base_addr , all_regbit = read_reg_xls(one_arg)
            one_blk = gen_blk(one_arg, base_addr, all_regbit)
            all_blk.append(one_blk)
        gen("reg.template.xml", all_blk)
        #doit("t.v.template")

# vim: set fenc=utf-8
